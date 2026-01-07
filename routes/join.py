from fastapi import APIRouter
from twilio.twiml.voice_response import VoiceResponse

from utils.digits import collect_digits_simple
from utils.helpers import TwilioFormDataDep, twiml_response

router = APIRouter()


def my_handler(account_id: int, resp: VoiceResponse):
    # account_id is already an integer!
    print(f"Got account ID: {account_id}")
    resp.say("Thank you!")


@router.post("/ivr/join/start")
async def join_game_start(form_data: TwilioFormDataDep):
    resp = VoiceResponse()
    resp.say("Awesome, let's get you ready to play!")
    resp.redirect("/ivr/join/collect-game-code")
    return twiml_response(resp)


@router.post("/ivr/join/collect-game-code")
async def collect_room_code(form_data: TwilioFormDataDep):
    return collect_digits_simple(
        form_data,
        num_digits=6,
        prompt="Please say or enter your 6-digit game code.",
        on_collected=my_handler,
        retry_message="Sorry, I didn't catch that.",
        redirect_to_on_fail="/ivr/join/collect-game-code",
    )
