from datetime import datetime, timedelta
import phonenumbers
from django.http import Http404


# TODO: adding 0 in hour is unintuitive
def format_date_time(date_time):
    try:
        date_time = date_time.replace(' ', '')
        month = int(date_time[0:2])
        day = int(date_time[3:5])
        year = int(date_time[6:10])
        hour = int(date_time[10:12])
        minute = int(date_time[13:15])
    except Exception:
        raise Http404('Invalid Date Time format')
    return datetime(year, month, day, hour, minute, 0)


def format_phone_number(number):
    try:
        parsed = phonenumbers.parse(number)
    except phonenumbers.NumberParseException:
        try:
            parsed = phonenumbers.parse('+1{}'.format(number))
        except phonenumbers.NumberParseException:
            return None
    formatted_number = phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.INTERNATIONAL)
    return formatted_number


def clean_inbound_sms(inbound_sms):
    return inbound_sms.lower().strip()


def get_expiration_date():
    # dont expire for now
    return datetime.now() + timedelta(days=365)
