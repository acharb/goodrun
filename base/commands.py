from enum import Enum
from base.models import Crew, UserProfile
from base.utils import format_phone_number

from twilio.twiml.messaging_response import MessagingResponse


class Command(Enum):

    REMIND = '/remind'
    RESEND = '/resend'
    ACCEPT = '/accepted'
    DECLINED = '/declined'
    MAYBE = '/maybe'
    EXPIRE = '/expire'
    OPTOUT = '/optout'
    OPTIN = '/optin'
    RESET = '/reset'
    DETAILS = '/details'


def is_a_command(inbound_sms):
    if get_command(inbound_sms):
        return True
    return False


def get_command(inbound_sms):
    cleaned_text = inbound_sms.lower().strip()
    command_arr = [e.value for e in Command]
    if cleaned_text in command_arr:
        command = command_arr[command_arr.index(cleaned_text)]
        return command
    else:
        arr = cleaned_text.split(' ')
        arr = [s for s in arr if s.strip()]
        if arr[0] == '/optin':
            return arr
    return None


def opt_in_userprofile(userprofile):
    cornell_crew = Crew.objects.get(name='Cornell Club Bball')
    userprofile.crews.add(cornell_crew)
    userprofile.opted_out = False
    userprofile.save()


def try_opt_in_phone_number(phone_number, name):
    resp = MessagingResponse()
    phone_number = format_phone_number(phone_number)
    userprofile = None
    try:
        userprofile = UserProfile.objects.get(phone_number=phone_number)
    except UserProfile.DoesNotExist:
        userprofile = UserProfile.objects.create(phone_number=phone_number, name=name)
    try:
        opt_in_userprofile(userprofile)
    except Exception:
        resp.message('Something went wrong. Please reach out to get this finished.')
        return resp
    resp.message('Opted in' + str(phone_number))
    return resp


def try_opt_in_self(userprofile):
    resp = MessagingResponse()
    try:
        opt_in_userprofile(userprofile)
    except Exception:
        resp.message('Something went wrong. Please reach out to get this finished.')
        return resp
    resp.message('Opted in')
    return resp


def handle_command_for(userprofile, inbound_sms):
    resp = MessagingResponse()

    command = get_command(inbound_sms)
    if type(command) == list and command[0] == Command.OPTIN.value:
        if command[1].index(':'):
            name = command[1][0:command[1].index(':')]
            name = name.lower().capitalize()
            phone_number = command[1][command[1].index(':') + 1:]
        else:
            phone_number = command[1]
            name = None
        return try_opt_in_phone_number(phone_number, name)

    if command == Command.OPTIN.value:
        return try_opt_in_self(userprofile)
    elif command == Command.RESET.value:
        userprofile.delete()
        resp.message('Account reset')
        return resp
    elif command == Command.OPTOUT.value:
        userprofile.opted_out = True
        userprofile.save()
        for crew in userprofile.crews.all():
            crew.userprofiles.remove(userprofile)
        resp.message('Opted out')
        return resp

    # For some reason questions may not expire when event does, so putting these here for now
    if command == Command.EXPIRE.value:
        userprofile.expire_active_events()
        userprofile.expire_previous_questions()
        resp.message('Expired your organized events.')
        return resp

    # prioritizes an event you organized over one your participating in
    active_event = userprofile.get_active_event()
    if not active_event:
        resp.message('You don\'t have an active event right now.')
        return resp

    # Organizer commands
    if active_event.organizer == userprofile:
        if command == Command.RESEND.value:
            active_event.resend_to_non_responses()
            resp.message('Resent invitations to non responders.')
            return resp
        elif command == Command.REMIND.value:
            active_event.remind_accepted_invitations()
            resp.message('Reminders sent for accepted invitations.')
            return resp
        elif command == Command.MAYBE.value:
            active_event.resend_maybe_invitations()
            resp.message('Invitations responded with \'maybe\' resent.')
            return resp

    # Partipants and Organizer Commands
    is_organizer = active_event.organizer == userprofile
    if command == Command.ACCEPT.value:
        text = active_event.get_accepted_invitations_text(show_numbers=is_organizer)
        resp.message(text)
        return resp
    # TODO: don't give partipants this access?
    elif command == Command.DECLINED.value:
        text = active_event.get_declined_invitations_text(show_numbers=is_organizer)
        resp.message(text)
        return resp
    elif command == Command.DETAILS.value:
        text = active_event.get_pretty_event_details()
        resp.message(text)
        return resp
    resp.message('Sorry, you can\'t make that command.')
    return resp
