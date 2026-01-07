from dataclasses import dataclass
from typing import Callable, Optional
from twilio.twiml.voice_response import VoiceResponse, Gather
from fastapi import Response

from utils.helpers import twiml_response as _twiml_response
from utils.types.forms import TwilioFormData


@dataclass
class DigitCollector:
    """
    Utility for collecting a specific number of digits from caller.
    Wraps the Gather verb, along with some nice-to-haves.

    Args:
        num_digits: Number of digits to collect
        prompt: Message to say before collecting
        success_message: Optional message after successful collection
        retry_message: Message when invalid input received
        max_retries: Maximum retry attempts (None for unlimited)
        on_success: Callback function(digits: str, resp: VoiceResponse) when digits collected
        on_failure: Optional callback function(resp: VoiceResponse) when max retries exceeded
        timeout: Timeout in seconds for digit input
    """

    num_digits: int
    prompt: str
    success_message: Optional[str] = None
    retry_message: str = "Invalid input. Please try again."
    max_retries: Optional[int] = 3
    on_success: Optional[Callable[[str, VoiceResponse], None]] = None
    on_failure: Optional[Callable[[VoiceResponse], None]] = None
    timeout: int = 10

    def render_initial(self) -> VoiceResponse:
        resp = VoiceResponse()
        gather = Gather(num_digits=self.num_digits, timeout=self.timeout)
        gather.say(self.prompt)
        resp.append(gather)

        # fallback if timeout
        resp.say(self.retry_message)
        resp.redirect("")

        return resp

    def handle_input(
        self, digits: Optional[str], retry_count: int = 0
    ) -> VoiceResponse:
        """
        Process collected digits

        Args:
            digits: The digits entered by user (None if timeout)
            retry_count: Current retry attempt number

        Returns:
            VoiceResponse with appropriate action
        """
        resp = VoiceResponse()

        # check if we have valid input
        if digits and len(digits) == self.num_digits and digits.isdigit():
            if self.success_message:
                resp.say(self.success_message)

            if self.on_success:
                self.on_success(digits, resp)

            return resp
        else:
            # invalid input or timeout
            retry_count += 1

            if self.max_retries is not None and retry_count >= self.max_retries:
                if self.on_failure:
                    self.on_failure(resp)
                else:
                    resp.say("Maximum attempts exceeded. Goodbye.")
                    resp.hangup()
                return resp

            # retry
            resp.say(self.retry_message)
            gather = Gather(num_digits=self.num_digits, timeout=self.timeout)
            gather.say(self.prompt)
            resp.append(gather)

            # fallback for timeout on retry
            resp.say(self.retry_message)
            resp.redirect("")

            return resp


def collect_digits(
    num_digits: int,
    prompt: str,
    digits: Optional[str] = None,
    retry_count: int = 0,
    **kwargs,
) -> Response:
    """
    Convenience function for callback based digit collection

    Args:
        num_digits: Number of digits to collect
        prompt: Message to say before collecting
        digits: Current digit input from user
        retry_count: Current retry count
        **kwargs: Additional DigitCollector parameters

    Returns:
        FastAPI Response with TwiML
    """
    collector = DigitCollector(num_digits=num_digits, prompt=prompt, **kwargs)

    if digits is None and retry_count == 0:
        resp = collector.render_initial()
    else:
        resp = collector.handle_input(digits, retry_count)

    return _twiml_response(resp)


def collect_digits_simple(
    form_data: TwilioFormData,
    num_digits: int,
    prompt: str,
    on_collected: Callable[[int, VoiceResponse], None],
    retry_message: str = "Invalid input. Please try again.",
    max_retries: Optional[int] = 3,
    on_max_retries: Optional[Callable[[VoiceResponse], None]] = None,
    redirect_to_on_fail: str | None = None,
    timeout: int = 10,
) -> Response:
    """
    Simplified digit collection that calls your callback with the integer value

    Args:
        form_data: Twilio form data from request
        num_digits: Number of digits to collect
        prompt: Message to say before collecting
        on_collected: Callback function(digits_as_int: int, resp: VoiceResponse)
        retry_message: Message when invalid input received
        max_retries: Maximum retry attempts (None for unlimited)
        on_max_retries: Optional callback when max retries exceeded
        redirect_to_on_fail: Optionally specify where to redirect if input can't be collected
        timeout: Timeout in seconds

    Returns:
        FastAPI Response with TwiML

    Example:
        def handle_account_id(account_id: int, resp: VoiceResponse):
            resp.say(f"Looking up account {account_id}")
            # do database lookup, redirect, etc.

        return collect_digits_simple(
            form_data,
            num_digits=8,
            prompt="Enter your 8-digit account ID.",
            on_collected=handle_account_id
        )
    """
    digits = form_data.digits if form_data.digits else None
    retry_count = int(form_data.retry_count if form_data.retry_count else "0")

    resp = VoiceResponse()

    # check if we have valid input
    if digits and len(digits) == num_digits and digits.isdigit():
        # success!
        digits_int = int(digits)
        on_collected(digits_int, resp)
        return _twiml_response(resp)

    # Invalid input or first time
    if digits is not None:  # was an attempt (not first time)
        retry_count += 1

    if max_retries is not None and retry_count >= max_retries:
        if on_max_retries:
            on_max_retries(resp)
        else:
            resp.say("Maximum attempts exceeded. Goodbye.")
            resp.hangup()
        return _twiml_response(resp)

    if digits is not None:
        resp.say(retry_message)

    gather = Gather(num_digits=num_digits, timeout=timeout)
    gather.say(prompt)
    resp.append(gather)

    # fallback for timeout
    resp.say(retry_message)
    resp.redirect(
        f"{redirect_to_on_fail}?RetryCount={retry_count}"
        if redirect_to_on_fail
        else f"?RetryCount={retry_count}"
    )

    return _twiml_response(resp)
