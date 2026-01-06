from fastapi import FastAPI, Response, Request, HTTPException
from twilio.twiml.voice_response import VoiceResponse, Gather
from utils import validate_request


app = FastAPI()

@app.post("/ivr/start")
async def chat(request: Request):
    if not await validate_request(request):
        raise HTTPException(status_code=400, detail="Error in Twilio Signature")    
    req_form = await request.form()
    city = req_form.get("FromCity")

    # Start our TwiML response
    resp = VoiceResponse()

    if "Digits" in req_form:
        # Get which digit the caller chose
        choice = req_form.get("Digits")
        # <Say> a different message depending on the caller's choice
        if choice == "1":
            resp.say("The extraterrestrial is on their way home, thank you!")
            return Response(content=str(resp), media_type="application/xml")
        elif choice == "2":
            resp.say("You called a little alien stinky. How could you?")
            resp.play("https://demo.twilio.com/docs/classic.mp3")
            return Response(content=str(resp), media_type="application/xml")
        else:
            # If the caller didn't choose 1 or 2, apologize and ask them again
            resp.say("Sorry, I don't understand that choice.")

    # Read a message aloud to the caller
    resp.say(
        f"Hello! Micah's records indicate that an extraterrestrail is in your home city of {city}!"
    )
    gather = Gather(num_digits=1)
    gather.say("Press 1 to help them get home, or press 2 to call them stinky.")
    # Play an audio file for the caller
    resp.append(gather)
    resp.redirect("/ivr/start")

    return Response(content=str(resp), media_type="application/xml")
