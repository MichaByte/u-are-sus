from twilio.request_validator import RequestValidator
from fastapi import Request
import os

TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
validator = RequestValidator(TOKEN)


async def validate_request(request: Request):
    req_form = await request.form()
    return validator.validate(
        str(request.url).replace("http", "https"), dict(req_form), request.headers.get("X-Twilio-Signature")
    )