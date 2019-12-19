from django.conf import settings
from twilio.rest import Client
from base.send.tasks import send_copilot_sms
from datetime import datetime, timedelta
from base.celery import app

account_sid = settings.TWILIO_ACCOUNT_SID
auth_token = settings.TWILIO_AUTH_TOKEN

def send_sms(outbound_text, to_phone_number):

    try:
        client = Client(account_sid, auth_token)
        client.messages.create(
            to=to_phone_number,
            from_=settings.TWILIO_PHONE_NUMBER,
            body=outbound_text
        )
        return True
    # TODO: handle error here, text one of us the error?
    except Exception:
        return False


def copilot_send_sms(outbound_text, to_phone_number):
    m_id = ''

    try:
        client = Client(account_sid, auth_token)
        message = client.messages.create(
            to=to_phone_number,
            from_=m_id,
            body=outbound_text
        )
        return message
    except Exception:
        return False


outbound_text = 'copilot test'
to_phone_number = ''
# can't send to google # ?
copilot_send_sms(outbound_text, to_phone_number)



send_sms(outbound_text, to_phone_number)


print('start')
result = send_copilot_sms.apply_async((outbound_text, to_phone_number), eta=datetime.now() + timedelta(seconds=5))
print('end')