from fastapi import FastAPI
from twilio.twiml.voice_response import VoiceResponse
from utils.menus import MenuActionType, Menu, MenuOption, handle_menu
from utils.helpers import TwilioFormDataDep, twiml_response

from routes import include_routers

app = FastAPI()

include_routers(app)

def play_hours(resp: VoiceResponse, location: str = "main") -> None:
    """Example custom function - play business hours"""
    resp.say(f"Our {location} office hours are Monday through Friday, 9 AM to 5 PM.")


def create_main_menu() -> Menu:
    """Factory function for main menu"""
    return Menu(
        intro_message="How can we help you?",
        options=[
            MenuOption(
                digit=1,
                prompt="To join a game, press 1.",
                action_type=MenuActionType.REDIRECT,
                action_value="/ivr/join/start",
            ),
            MenuOption(
                digit=2,
                prompt="To host a game, press 2.",
                action_type=MenuActionType.FUNCTION,
                action_value=play_hours,
                action_args={"location": "main"},
            ),
            MenuOption(
                digit=3,
                prompt="To learn more about us, press 3.",
                action_type=MenuActionType.SAY_AND_RETURN,
                action_value=None,
                message="We are located at 123 Main Street, San Francisco, CA.",
            ),
        ],
        invalid_choice_message="Uh oh, that's not a valid option.",
        timeout_message="Whoops, I missed that!",
    )


@app.post("/ivr/start")
async def start():
    """Main IVR menu - initial presentation"""
    resp = VoiceResponse()
    resp.say(
        "Hi there! Thank you for calling our non-infringing murder mystery game. We are so excited to have you!"
    )
    resp.redirect("/ivr/start/menu")
    return twiml_response(resp)


@app.post("/ivr/start/menu")
async def start_menu(form_data: TwilioFormDataDep):
    return handle_menu(create_main_menu(), form_data.digits if form_data.digits else None)
