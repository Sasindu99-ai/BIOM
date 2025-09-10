import urllib
from os import environ

import requests
from dotenv import load_dotenv
from rest_framework.exceptions import ValidationError

__all__ = ['SMSService']

load_dotenv()


class SMSService:
    @classmethod
    async def sendOTP(cls, mobileNumber: str, otp: str):
        url = environ.get('SMS_API_URL', '')
        data = {
            'apikey': environ.get('SMS_API_KEY', ''),
            'apitoken': environ.get('SMS_API_TOKEN', ''),
            'type': 'sms',
            'from': 'VIP Travels',
            'to': mobileNumber,
            'text': f"""Your OTP code is: {otp}
Do not share this code with anyone.""",
        }
        try:
            req = url + '&' + urllib.parse.urlencode(data)
            result = requests.get(req, verify=False, timeout=10)  # noqa: S501, ASYNC210
            return result.json()
        except Exception as e:
            raise ValidationError({'sms': 'Failed to send SMS'}) from e
