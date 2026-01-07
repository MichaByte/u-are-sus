import os
from typing import Annotated

from fastapi import Depends, Form, Header, HTTPException, Request, Response
from twilio.request_validator import RequestValidator
from twilio.twiml.voice_response import VoiceResponse

from utils.types.forms import TwilioFormData
from utils.types.headers import TwilioHeaders

TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
validator = RequestValidator(TOKEN)

async def get_twilio_form(request: Request, form_data: Annotated[TwilioFormData, Form()], twilio_headers: Annotated[TwilioHeaders, Header()]):
    """Validates Twilio signature and returns form data"""
    is_valid = validator.validate(
        str(request.url).replace("http", "https"),
        dict(await request.form()),
        twilio_headers.x_twilio_signature
    )
    if not is_valid:
        raise HTTPException(status_code=400, detail="Error in Twilio Signature")
    return form_data


def twiml_response(voice_response: VoiceResponse) -> Response:
    """Converts VoiceResponse to FastAPI Response"""
    return Response(content=str(voice_response), media_type="application/xml")

TwilioFormDataDep = Annotated[TwilioFormData, Depends(get_twilio_form)]
