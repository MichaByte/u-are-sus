from dataclasses import dataclass
from enum import Enum
from typing import Callable, Optional, Union
from twilio.twiml.voice_response import VoiceResponse, Gather
from fastapi import Response

from utils.helpers import twiml_response as _twiml_response


class MenuActionType(Enum):
    REDIRECT = "redirect"
    FUNCTION = "function"
    SAY_AND_HANGUP = "say_and_hangup"
    SAY_AND_RETURN = "say_and_return"


@dataclass
class MenuOption:
    """
    Represents a single menu option

    Args:
        digit: The digit to press
        prompt: The text spoken for this option
        action_type: Type of action to perform
        action_value: URL string for redirect, or callable for function
        message: Optional message to say before performing action
        action_args: Optional dict of arguments to pass to function
    """

    digit: int
    prompt: str
    action_type: MenuActionType
    action_value: Union[str, Callable[[VoiceResponse], None]] | None
    message: Optional[str] = None
    action_args: Optional[dict] = None

    def execute(self, resp: VoiceResponse) -> VoiceResponse:
        # say message if provided
        if self.message:
            resp.say(self.message)

        # perform action based on type
        if self.action_type == MenuActionType.REDIRECT:
            resp.redirect(self.action_value)
        elif self.action_type == MenuActionType.FUNCTION and isinstance(
            self.action_value, Callable
        ):
            if self.action_args:
                self.action_value(resp, **self.action_args)
            else:
                self.action_value(resp)
        elif self.action_type == MenuActionType.SAY_AND_HANGUP:
            resp.hangup()
        elif self.action_type == MenuActionType.SAY_AND_RETURN:
            resp.redirect("")

        return resp


@dataclass
class Menu:
    """
    Basic IVR menu implementation

    Args:
        options: List of MenuOption objects
        intro_message: Optional greeting before menu options
        invalid_choice_message: Optional message for invalid input
        timeout_message: Message when user doesn't press anything (defaults to invalid_choice_message)
        num_digits: Number of digits to gather (default: 1)
        timeout: Timeout in seconds for digit input
    """

    options: list[MenuOption]
    intro_message: Optional[str] = None
    invalid_choice_message: str = "Sorry, I don't understand that choice."
    timeout_message: Optional[str] = None
    num_digits: int = 1
    timeout: int = 5

    def __post_init__(self):
        """Set default timeout_message if not provided"""
        if self.timeout_message is None:
            self.timeout_message = self.invalid_choice_message

    def get_full_prompt(self) -> str:
        """Return all option prompts as a single string"""
        prompts = []
        if self.intro_message:
            prompts.append(self.intro_message)
        prompts.extend(opt.prompt for opt in self.options)
        return " ".join(prompts)

    def handle_choice(self, choice: Optional[str]) -> VoiceResponse:
        resp = VoiceResponse()

        # Find matching option
        option = next(
            (opt for opt in self.options if opt.digit == int(choice or -1)), None
        )

        if option:
            return option.execute(resp)
        else:
            # invalid choice or timeout, prompt caller with menu again
            resp.say(self.invalid_choice_message)
            return self._render_gather(resp)

    def render_initial(self) -> VoiceResponse:
        resp = VoiceResponse()
        return self._render_gather(resp)

    def _render_gather(self, resp: VoiceResponse) -> VoiceResponse:
        gather = Gather(num_digits=self.num_digits, timeout=self.timeout)
        gather.say(self.get_full_prompt())
        resp.append(gather)

        # fallback if gather times out
        resp.say(self.timeout_message)
        resp.redirect("")  # empty means redirect to self. this restarts the menu

        return resp


def handle_menu(
    menu: Menu, choice: Optional[str], resp: Optional[VoiceResponse] = None
) -> Response:
    """
    Generic handler for menus

    Args:
        menu: The Menu object to handle
        choice: The digit choice from user (None for initial render)
        resp: Optional VoiceResponse to use (creates new one if not provided)

    Returns:
        FastAPI Response with TwiML
    """
    if resp is None:
        if choice:
            resp = menu.handle_choice(choice)
        else:
            resp = menu.render_initial()
    else:
        # use existing response object
        if choice:
            menu_resp = menu.handle_choice(choice)
        else:
            menu_resp = menu.render_initial()

        # append all verbs from menu_resp to the provided resp
        for verb in menu_resp.verbs:
            resp.append(verb)

    return _twiml_response(resp)
