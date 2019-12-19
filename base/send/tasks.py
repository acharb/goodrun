from base.celery import app
from django.conf import settings
from twilio.rest import Client
import os

account_sid = settings.TWILIO_ACCOUNT_SID
auth_token = settings.TWILIO_AUTH_TOKEN

# locally, need to change if running on heroku
# app = Celery('tasks', broker=os.environ.get('BROKER_URL'))


def copilot_send_sms(outbound_text, to_phone_number):
    m_id = ''

    try:
        client = Client(account_sid, auth_token)
        return client.messages.create(
            to=to_phone_number,
            from_=m_id,
            body=outbound_text,
            status_callback='',
        )
    except Exception:
        return None


@app.task
def send_copilot_sms(outbound_text, to):
    print('sent to %s' % to)
    return copilot_send_sms(outbound_text, to)
