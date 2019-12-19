from django.conf import settings
from twilio.rest import Client
from base.send.tasks import send_copilot_sms


account_sid = settings.TWILIO_ACCOUNT_SID
auth_token = settings.TWILIO_AUTH_TOKEN


def send_sms(outbound_text, to_phone_number):
    try:
        client = Client(account_sid, auth_token)
        return client.messages.create(
            to=to_phone_number,
            from_=settings.TWILIO_PHONE_NUMBER,
            body=outbound_text
        )
    # TODO: handle error here, text one of us the error?
    except Exception:
        return None


def send_participant_invitations_for_event(event):
    # to avoid circular imports
    from base.models import Invitation, Crew, UserProfile

    crew = None
    try:
        crew = event.crew_sent_to
    except Exception:
        pass

    # hardcode for now
    # for testing
    if not crew:
        alec = UserProfile.objects.get(phone_number='')
        if event.organizer == alec:
            crew = Crew.objects.get(name='Alec Test Crew')
        else:
            crew = Crew.objects.get(name='Cornell Club Bball')

    send_to_qs = crew.userprofiles.filter(opted_out=False).exclude(id=event.organizer.id)

    number_of_players_to_send_to = event.number_of_players if event.number_of_players else -1
    for up in send_to_qs:
        text = 'Hi' + ((' ' + str(up.name)) if up.name else '') + '! You\'ve been invited to join a GoodRun event' + \
            ((' by ' + str(event.organizer.name)) if event.organizer.name else '.') + '\n\n'
        text += 'The event details:\n\n'
        text += event.get_pretty_event_details() + '\n\n'
        text += 'Please respond if you will be attending the run.\n'
        text += 'Options: \'yes\', \'no\', or \'maybe\' (maybe means we\'ll text you before the event if it\'s not full). \n\n'
        text += '(to opt out reply /optout)'
        if abs(number_of_players_to_send_to) < 1:
            break
        # handle call back somehow, set invitation to error if failed
        Invitation.objects.create(event=event, sent_to=up, text=text)
        # TODO: Figure out RabbitMQ in production
        send_copilot_sms.apply_async((text, up.phone_number))
        # copilot_send_sms(text, up.phone_number)
        # send_sms(text, up.phone_number)
        number_of_players_to_send_to -= 1
    event.invitations_have_sent = True
    event.save()
