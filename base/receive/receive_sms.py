from twilio.twiml.messaging_response import MessagingResponse

from django.http import Http404

from base.receive.serializers import InboundSmsSerializer
from base.utils import format_phone_number, format_date_time
from base.models import UserProfile, Event, Invitation, QuestionPrompt, QuestionFlowNode
from base.commands import is_a_command, handle_command_for


def _get_error_response_with_optional_action(action=None):
    text = "Oops, something went wrong. Please reply again.\n\n"
    if not action:
        return text
    if type(action) == QuestionPrompt:
        question = action
        text += question.get_prompt_text() + '\n'
    elif type(action) == Invitation:
        text += 'Allowed answers: \n\n'
        text += '\'yes\', \'no\', \'maybe\''
    return text


# TODO: figure out better way than grabbing all previous events. Task?
def handle_returning_user(userprofile):
    first_node = QuestionFlowNode.objects.get(title=QuestionFlowNode.INTRO, order=1)
    userprofile.expire_previous_questions()
    userprofile._load_question_flow_list_into_queue(first_node)


def pop_next_outbound_text_for(userprofile):
    popped_next_outbound_text = userprofile.pop_next_outbound_text()
    if popped_next_outbound_text:
        return popped_next_outbound_text

    next_action = userprofile.get_next_unanswered_action()
    if next_action:
        return next_action.get_prompt_text()

    active_events = userprofile.get_active_event()
    if active_events:
        return 'You have an active event. We\'re working on it!'
    else:
        handle_returning_user(userprofile)
        return pop_next_outbound_text_for(userprofile)

    return _get_error_response_with_optional_action()


def handle_sms_receive(request):
    resp = MessagingResponse()
    data = {
        'body': request.POST.get('Body'),
        'phone_number': request.POST.get('From')
    }
    serializer = InboundSmsSerializer(data=data)
    serializer.is_valid(raise_exception=True)

    # TODO add loggers (1 way for now? Too hard to add conversational?)
    inbound_sms_body = serializer.validated_data.get('body', None)
    phone_number = serializer.validated_data.get('phone_number', None)
    formatted_phone_number = format_phone_number(phone_number)

    # TODO LATER: possibly if new user in our system ask for contact info (name)
    userprofile = None
    try:
        userprofile = UserProfile.objects.get(phone_number=formatted_phone_number)
    except UserProfile.DoesNotExist:
        pass

    if userprofile:
        print('RECEIVED: %s\nFROM: %s' % (inbound_sms_body, userprofile.phone_number))

        if is_a_command(inbound_sms_body):
            return handle_command_for(userprofile, inbound_sms_body)
        elif inbound_sms_body.lower().strip()[0] == '/':
            resp.message('Unrecognized command.')
            return resp

        action = userprofile.get_next_unanswered_action()
        try:
            _save_question_or_invitation_response_or_404(action=action, inbound_sms_body=inbound_sms_body)
        except Exception:
            resp.message(_get_error_response_with_optional_action(action))
            return resp

        outbound_text = pop_next_outbound_text_for(userprofile)
        resp.message(outbound_text)
        return resp
    else:
        userprofile = UserProfile.objects.create(phone_number=formatted_phone_number)
        question = userprofile.get_next_unanswered_action()
        text = "\'What it do Babeeeee\' (Kawhi voice). \nWelcome to GoodRun, where we 'assist' in organizing your best run. \n\n" + question.get_prompt_text() + '\n'
        text += 'for help text -'
        resp.message(text)
        return resp

    # shouldn't get here
    resp.message(_get_error_response_with_optional_action())
    return resp


def _save_question_or_invitation_response_or_404(action, inbound_sms_body):
    if type(action) == QuestionPrompt:
        question_prompt = action
        if not question_prompt.is_save_text_successful(inbound_sms_body):
            raise Http404("Save Response Failed")
    elif type(action) == Invitation:
        invitation = action
        if not invitation.is_save_response_successful(inbound_sms_body):
            raise Http404
    return


def save_response_to_event_return_success(event, inbound_sms):
    prompt_answer_obj = event.get_next_unanswered_prompt_and_answers()
    try:
        field = prompt_answer_obj['field']
        # obviously better fix later
        if field == 'date_time':
            inbound_sms = format_date_time(inbound_sms)
        # if text is not 'yes', then delete event? Do something
        elif field == 'confirm_create_event':
            inbound_sms = True if inbound_sms.lower().strip() == 'yes' else False
        elif field == 'full_court':
            inbound_sms = True if inbound_sms.lower().strip() == 'yes' else False
        elif field == 'additional_notes':
            if inbound_sms.strip().lower() == 'no':
                inbound_sms = 'None'
        elif field == 'structure_of_event':
            if inbound_sms.strip().lower() == 'yes':
                inbound_sms = Event.STRUCTURED
                event.asap_event_message = 'NONE'
            elif inbound_sms.strip().lower() == 'no':
                inbound_sms = Event.ASAP

        setattr(event, field, inbound_sms)
        event.save()
        return True
    except Exception:
        return False
