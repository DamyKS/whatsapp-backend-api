#from django.shortcuts import render

# Create your views here.
#from django.http import HttpResponse
#from django.utils.decorators import method_decorator
#from django.views import View
#from django.views.decorators.csrf import csrf_exempt
from twilio.twiml.voice_response import VoiceResponse, Dial
from django.conf import settings
#from django.http import HttpResponse, JsonResponse
from twilio.jwt.access_token import AccessToken, grants
from twilio.rest import Client

client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)

def get_access_token(username):
    voice_grant = grants.VoiceGrant(
        outgoing_application_sid=settings.TWIML_APPLICATION_SID,
        incoming_allow=True,
    )
    access_token = AccessToken(
        settings.TWILIO_ACCOUNT_SID,
        settings.TWILIO_API_KEY, 
        settings.TWILIO_API_SECRET,
        identity=username
    )
    access_token.add_grant(voice_grant)
    jwt_token = access_token.to_jwt()
    # Remove the decode() call since jwt_token is already a string
    return {"token": jwt_token}


def get_call_twiml(username, call_session_name):
    room_name = call_session_name
    participant_label = username
    response = VoiceResponse()
    dial = Dial()
    dial.conference(
        name=room_name,
        participant_label=participant_label,
        start_conference_on_enter=True,
    )
    response.append(dial)
    return response.to_xml()      