from base.send.send_sms import send_participant_invitations_for_event
from base.utils import format_date_time


# Can assume response saved to QuestionResponse successfuly before these are called
# NEEDS TO RETURN A BOOLEAN
class SuccessHandler(object):

    def handle_create_event_for_question_prompt(self, question_prompt):
        # to avoid circular imports
        from base.models import Event

        question_response = question_prompt.response
        sent_to = question_prompt.sent_to

        if question_response.text == 'yes':
            sent_to.expire_active_events()
            if not question_prompt.event:
                event = Event.objects.create(organizer=sent_to, confirm_create_event=True)
                for qp in sent_to.questions.filter(active=True).filter(flow_type=question_prompt.flow_type):
                    event.questions.add(qp)
                event.save()
            return True
        else:
            return True

    def handle_save_structure_type_to_event(self, question_prompt):
        question_response = question_prompt.response
        event = question_prompt.event
        inbound_sms_text = question_response.text

        if not event:
            return False

        if inbound_sms_text == 'yes':
            event.event_structure_type = event.STRUCTURED
        elif inbound_sms_text == 'no':
            event.event_structure_type = event.ASAP
        event.save()
        return True

    def handle_save_forward_text_to_event(self, question_prompt):
        question_response = question_prompt.response
        event = question_prompt.event
        inbound_sms_text = question_response.text

        event.text_to_forward = inbound_sms_text
        event.save()
        return True

    def handle_attach_confirmation_text_to_next_question(self, question_prompt):
        userprofile = question_prompt.sent_to
        event = question_prompt.event
        try:
            next_question = userprofile.questions.filter(active=True).filter(order_in_flow=question_prompt.order_in_flow + 1) \
                .filter(flow_type=question_prompt.flow_type).first()
            next_question.confirmation_text = event.get_pretty_event_details()
            next_question.save()
            return True
        except Exception:
            return False

    def handle_confirm_text(self, question_prompt):
        question_response = question_prompt.response
        event = question_prompt.event
        inbound_sms_text = question_response.text

        if inbound_sms_text == 'yes':
            event.active = True
            event.save()
            send_participant_invitations_for_event(event)
        elif inbound_sms_text == 'no':
            question_prompt.reset_answers_for_current_flow()
        return True

    def handle_confirm_structured_text(self, question_prompt):
        event = question_prompt.event
        question_response = question_prompt.response
        inbound_sms_text = question_response.text

        if inbound_sms_text == 'yes':
            event.active = True
            event.save()
            send_participant_invitations_for_event(event)
        elif inbound_sms_text == 'no':
            question_prompt.reset_answers_for_current_flow()
        return True

    # TODO: pretty coupled with handle_confirm_structured_text right now
    def append_outbound_sms_text_for_userprofile(self, question_prompt):
        question_response = question_prompt.response
        inbound_sms_text = question_response.text

        if inbound_sms_text == 'yes':
            userprofile = question_prompt.sent_to
            text = 'We\'ve sent out your invitations. Happy runs! \n\n'
            text += 'Here are some helpful commands for you: \n\n'
            text += '1. /accepted - Get a list of accepted players \n'
            text += '2. /remind - Send a reminder text to accepted players \n'
            text += '3. /maybe - Re-Ask players who responded with \'maybe\' \n'
            text += '4. /expire - Expire any active events you\'ve scheduled \n'
            userprofile.next_outbound_text = text
            userprofile.save()
        elif inbound_sms_text == 'no':
            text = 'Ok'
        return True

    def handle_save_userprofile_name(self, question_prompt):
        question_response = question_prompt.response
        inbound_sms_text = question_response.text

        userprofile = question_prompt.sent_to
        userprofile.name = inbound_sms_text
        userprofile.save()
        return True

    def handle_save_number_of_players_to_event(self, question_prompt):
        question_response = question_prompt.response
        event = question_prompt.event
        inbound_sms_text = question_response.text

        number_of_players = int(inbound_sms_text)
        event.number_of_players = number_of_players
        event.save()
        return True

    def handle_save_location_to_event(self, question_prompt):
        question_response = question_prompt.response
        event = question_prompt.event
        inbound_sms_text = question_response.text

        event.location = inbound_sms_text
        event.save()
        return True

    # TODO: Move formatting to validation in models
    def handle_save_time_to_event(self, question_prompt):
        question_response = question_prompt.response
        event = question_prompt.event
        inbound_sms_text = question_response.text

        event.date_time = format_date_time(inbound_sms_text)
        event.save()
        return True

    def handle_save_duration_to_event(self, question_prompt):
        question_response = question_prompt.response
        event = question_prompt.event
        inbound_sms_text = question_response.text

        event.duration = inbound_sms_text
        event.save()
        return True

    def handle_save_full_court_to_event(self, question_prompt):
        question_response = question_prompt.response
        event = question_prompt.event
        inbound_sms_text = question_response.text

        if inbound_sms_text == 'yes':
            event.full_court = True
        else:
            event.full_court = False
        event.save()
        return True

    def handle_save_additional_notes_to_event(self, question_prompt):
        question_response = question_prompt.response
        event = question_prompt.event
        inbound_sms_text = question_response.text
        cleaned_text = inbound_sms_text.lower().strip()

        if cleaned_text == 'no':
            inbound_sms_text = 'N/A'
        event.additional_notes = inbound_sms_text
        event.save()
        return True

    def handle_save_crew_to_event(self, question_prompt):
        question_response = question_prompt.response
        event = question_prompt.event
        inbound_sms_text = question_response.text
        cleaned_text = inbound_sms_text.lower().strip()

        # Wants to restart
        if cleaned_text == 'no':
            userprofile = event.organizer
            userprofile.expire_active_events()
            userprofile.expire_previous_questions()
            return True

        try:
            from base.models import Crew
            # TODO HACKYYYYYYY - FIX
            answer_display = question_prompt.answer_options_display[question_prompt.allowed_answers.index(cleaned_text)]
            # eg '1 - Cornell Club Bball'
            crew = Crew.objects.get(name=answer_display[4:])
            event.crew_sent_to = crew
            event.save()
        except Exception:
            return False

        return True
