from pydantic import BaseModel


class TwilioHeaders(BaseModel):
    x_twilio_signature: str