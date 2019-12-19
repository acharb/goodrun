from dirtyfields import DirtyFieldsMixin
from datetime import datetime

from django.contrib.postgres.fields import ArrayField
from django.db import models
from django.db.models.signals import pre_save, post_save
from django.dispatch import receiver

from base.send.tasks import send_copilot_sms
from base.success_handlers import SuccessHandler
from base.utils import get_expiration_date


class BaseModelMixin(DirtyFieldsMixin, models.Model):

    created_at = models.DateTimeField(null=True, auto_now_add=True)
    modified_at = models.DateTimeField(null=True, auto_now=True)

    class Meta:
        get_latest_by = 'created_at'
        abstract = True


class UserProfile(BaseModelMixin, models.Model):

    phone_number = models.CharField(max_length=25, unique=True)
    is_organizer = models.BooleanField(default=False)
    name = models.CharField(max_length=50, null=True, blank=True)
    creating_event = models.BooleanField(default=False)
    next_outbound_text = models.TextField(null=True, blank=True)
    opted_out = models.BooleanField(default=False)
    password = models.CharField(max_length=100, blank=True, null=True)

    def save(self, *args, **kwargs):
        is_new = not self.pk
        super().save(*args, **kwargs)
        first_node = QuestionFlowNode.objects.get(title=QuestionFlowNode.INTRO, order=1)
        if is_new:
            self._load_question_flow_list_into_queue(first_node)

    def __str__(self):
        if self.name:
            return self.name
        return self.phone_number

    def is_awaiting_invitation_response(self):
        if self.invitations.filter(state='SENT').exists():
            return True
        return False

    # Priority of Actions:
    # 1: Invitation response
    # 2: Pending question to be answered
        # Question Que: [ Q1, Q2, Q3, Q4 ]
    def get_next_unanswered_action(self):
        latest_unanswered_invitation = self.invitations.filter(state=Invitation.SENT).order_by('-created_at').first()
        if latest_unanswered_invitation:
            return latest_unanswered_invitation
        latest_unanswered_active_question = self.questions.filter(active=True).filter(response__text=None).order_by('created_at').first()
        return latest_unanswered_active_question if latest_unanswered_active_question else None

    def _load_question_flow_list_into_queue(self, first_node, event=None):
        node = first_node
        while node:

            question_prompt = QuestionPrompt.objects.create(
                sent_to=self,
                prompt=node.prompt,
                allowed_answers=node.allowed_answers,
                answer_options_display=node.answer_options_display,
                order_in_flow=node.order,
                flow_type=node.title,
                next_flow_options=node.next_flow_options,
                success_handlers=node.success_handlers,
                event=event
            )

            # HACKY - only way I can think of customizing allowed answers for beyond yes/no or None
            question_prompt._override_allowed_answers_if_needed()
            # TODO: make automatic?
            QuestionResponse.objects.create(
                responder=self,
                question_prompt=question_prompt
            )
            node = node.next

    def pop_next_outbound_text(self):
        if self.next_outbound_text:
            next_outbound_text = self.next_outbound_text
            self.next_outbound_text = None
            self.save()
            return next_outbound_text
        return None

    def get_active_event(self):
        now = datetime.now()
        organized_event = self.events_organized.filter(expiration_date__gte=now).first()
        if organized_event:
            return organized_event
        else:
            for active_event in Event.objects.filter(active=True):
                if self.id in active_event.invitations.values_list('sent_to__id', flat=True):
                    return active_event
        return None

    def expire_previous_questions(self):
        self.questions.update(active=False)

    def expire_active_events(self):
        now = datetime.now()
        self.events_organized.filter(expiration_date__gte=now).update(expiration_date=now)
        # TODO: Consolidate expiration and active into one
        self.events_organized.update(active=False)


class Event(BaseModelMixin, models.Model):

    NUM_OF_PLAYERS_OPTIONS = [(i, i) for i in range(1, 16)]

    ASAP = 'ASAP'
    STRUCTURED = 'STRUCTURED'

    EVENT_STRUCTURE_TYPES = [
        (STRUCTURED, STRUCTURED),
        (ASAP, ASAP)
    ]

    # Detail Fields:
    confirm_create_event = models.BooleanField(null=True)
    event_structure_type = models.CharField(max_length=25, null=True, choices=EVENT_STRUCTURE_TYPES)
    asap_event_message = models.TextField(null=True, blank=True)
    number_of_players = models.IntegerField(null=True, choices=NUM_OF_PLAYERS_OPTIONS)
    location = models.TextField(null=True, blank=True)
    date_time = models.DateTimeField(null=True)
    # change to duration field later?
    duration = models.CharField(max_length=25, null=True)
    full_court = models.BooleanField(null=True)
    cost = models.DecimalField(null=True, max_digits=8, decimal_places=2)
    additional_notes = models.TextField(null=True, blank=True)
    text_to_forward = models.TextField(null=True, blank=True)
    crew_sent_to = models.ForeignKey('Crew', related_name='events', null=True, on_delete=models.CASCADE)

    @property
    def organizer_name(self):
        if self.organizer.name:
            return self.organizer.name
        return None

    @organizer_name.setter
    def organizer_name(self, name):
        self.organizer.name = name
        self.organizer.save()

    organizer = models.ForeignKey(UserProfile, related_name='events_organized', on_delete=models.CASCADE)
    participants = models.ManyToManyField(UserProfile, related_name='events_participated')
    tipoff_eta = models.DurationField(null=True, editable=False)
    expiration_date = models.DateTimeField(default=get_expiration_date)
    invitations_have_sent = models.BooleanField(default=False)
    active = models.BooleanField(default=False)

    def is_in_progress(self):
        if self.get_next_unanswered_prompt_and_answers() or (self.date_time and (self.date_time < datetime.now())):
            return True
        return False

    def details_complete(self):
        if self.get_next_unanswered_prompt_and_answers():
            return False
        return True

    def get_pretty_event_details(self):
        if self.event_structure_type == self.ASAP:
            text = self.text_to_forward
        elif self.event_structure_type == self.STRUCTURED:
            text = ''
            text += 'Number of Players: ' + str(self.number_of_players) + '\n'
            text += 'Location: ' + str(self.location) + '\n'
            text += 'Date and Time: ' + str(self.date_time.strftime("%Y-%m-%d %H:%M")) + '\n'
            # add PM or AM
            text += 'Time: '
            text += 'Duration: ' + str(self.duration) + '\n'
            text += 'Full Court? ' + ('Yes' if self.full_court else 'No') + '\n'
            # text += 'Cost: $' + str(self.cost) + '\n'
            text += 'Addtl Notes: ' + str(self.additional_notes) + '\n'
        return text

    def get_accepted_invitations(self):
        accepted_invitations = self.invitations.filter(state='ACCEPTED')
        return accepted_invitations

    def get_accepted_invitations_text(self, show_numbers=True):
        text = 'ACCEPTED:\n\n'
        if not self.invitations.filter(state='ACCEPTED'):
            text += 'None'
        else:
            for accepted_invitation in self.invitations.filter(state='ACCEPTED'):
                sent_to = accepted_invitation.sent_to
                if show_numbers:
                    text += sent_to.phone_number
                    text += (' - ' + sent_to.name + '\n') if sent_to.name else '\n'
                else:
                    text += (sent_to.name + '\n') if sent_to.name else 'Anonymous\n'
        return text

    def get_declined_invitations_text(self, show_numbers=True):
        text = 'DECLINED:\n\n'
        if not self.invitations.filter(state='DENIED'):
            text += 'None'
        else:
            for denied_invitations in self.invitations.filter(state='DENIED'):
                sent_to = denied_invitations.sent_to
                if show_numbers:
                    text += sent_to.phone_number
                    text += (' - ' + sent_to.name + '\n') if sent_to.name else '\n'
                else:
                    text += (sent_to.name + '\n') if sent_to.name else 'Anonymous\n'
        return text

    def resend_maybe_invitations(self):
        for inv in self.invitations.filter(state='MAYBE'):
            # TODO: Figure out rabbitmq
            send_copilot_sms.apply_async((inv.text, inv.sent_to.phone_number))
            # copilot_send_sms(inv.text, inv.sent_to.phone_number)
            # send_sms(text, inv.sent_to.phone_number)
            inv.sent_count += 1
            inv.save()

    def remind_accepted_invitations(self):
        text = 'This is a reminder for your upcoming GoodRun event. Details are below: \n\n'
        text += self.get_pretty_event_details()
        for inv in self.invitations.filter(state='ACCEPTED'):
            # TODO: Figure out rabbitmq
            send_copilot_sms.apply_async((text, inv.sent_to.phone_number))
            # copilot_send_sms(text, inv.sent_to.phone_number)
            # send_sms(text, inv.sent_to.phone_number)

    def resend_to_non_responses(self):
        for inv in self.invitations.filter(state='SENT'):
            send_copilot_sms.apply_async((inv.text, inv.sent_to.phone_number))
            inv.sent_count += 1
            inv.save()

    def is_expired(self):
        return self.expiration_date >= datetime.now()

    def expire_questions(self):
        self.questions.update(active=False)


class QuestionFlowNode(BaseModelMixin, models.Model):

    INTRO = 'INTRO'
    ASAP = 'ASAP'
    STRUCTURED = 'STRUCTURED'
    CREW_SEND = 'CREW_SEND'
    NON_CREW_SEND = 'NON_CREW_SEND'

    TITLE_OPTIONS = [
        (INTRO, INTRO),
        (ASAP, ASAP),
        (STRUCTURED, STRUCTURED)
    ]

    title = models.CharField(max_length=25, choices=TITLE_OPTIONS, null=False, blank=False)
    prompt = models.CharField(max_length=250, null=False, blank=False)
    allowed_answers = ArrayField(models.CharField(max_length=250), null=True)
    order = models.IntegerField(null=False)
    answer_options_display = ArrayField(models.CharField(max_length=250), null=True)
    success_handlers = ArrayField(models.CharField(max_length=50, null=True, blank=True), null=True)

    next = models.OneToOneField('self', null=True, related_name='previous', on_delete=models.CASCADE)
    next_flow_options = ArrayField(models.CharField(max_length=25, choices=TITLE_OPTIONS, null=True, blank=True), null=True)

    class Meta:
        unique_together = ('title', 'order',)


class QuestionPrompt(BaseModelMixin, models.Model):

    sent_to = models.ForeignKey(UserProfile, related_name='questions', on_delete=models.CASCADE)
    active = models.BooleanField(default=True)
    order_in_flow = models.IntegerField(null=False)
    flow_type = models.CharField(max_length=15, choices=QuestionFlowNode.TITLE_OPTIONS, null=False, blank=False)
    prompt = models.CharField(max_length=250, null=False, blank=False)
    answer_options_display = ArrayField(models.CharField(max_length=250), null=True)
    confirmation_text = models.TextField(null=True, blank=True)

    event = models.ForeignKey(Event, related_name='questions', null=True, on_delete=models.CASCADE)
    event_field = models.CharField(max_length=50, null=True, blank=True)
    # allowed_answers and next_flow_options match orders
    allowed_answers = ArrayField(models.CharField(max_length=250), null=True)
    next_flow_options = ArrayField(models.CharField(max_length=25, choices=QuestionFlowNode.TITLE_OPTIONS, null=False, blank=False), null=True)
    success_handlers = ArrayField(models.CharField(max_length=50, null=True, blank=True), null=True)

    def get_prompt_text(self):
        text = ''
        text += self.prompt + '\n\n'

        # TODO: super hardcode, figure out a better way of doing this
        if self.confirmation_text:
            text += self.confirmation_text + '\n\n'

        if self.answer_options_display:
            text += 'Options: \n'
            for answer in self.answer_options_display:
                text += answer + '\n'
        return text

    def is_save_text_successful(self, inbound_sms_text):
        if self._is_save_text_to_response_successful(inbound_sms_text):
            return self._is_success_handler_successful()
        return False

    def _is_save_text_to_response_successful(self, inbound_sms_text):
        cleaned_text = inbound_sms_text.lower().strip()
        if not self._is_response_allowed(cleaned_text):
            return False

        # TODO fix this one off case
        if self.flow_type == QuestionFlowNode.ASAP and self.order_in_flow == 1:
            cleaned_text = inbound_sms_text.strip()

        response = self.response
        if not response:
            response = QuestionResponse.objects.create(
                question_prompt=self,
                responder=self.sent_to
            )
        response.text = cleaned_text
        response.save()
        return True

    def _is_response_allowed(self, inbound_sms_text):
        cleaned_text = inbound_sms_text.lower().strip()
        if self.allowed_answers:
            if not (cleaned_text in self.allowed_answers):
                return False
        return True

    def _is_success_handler_successful(self):
        success_handler = SuccessHandler()
        for function in self.success_handlers:
            is_handler_successful = getattr(success_handler, function)
            if not is_handler_successful(self):
                return False
        return True

    def reset_answers_for_current_flow(self):
        userprofile = self.sent_to
        flow_type = self.flow_type
        for question_prompt in userprofile.questions.filter(active=True).filter(flow_type=flow_type):
            response = question_prompt.response
            response.text = None
            response.save()

    def _override_allowed_answers_if_needed(self):
        # Load Crew Names
        if self.flow_type == QuestionFlowNode.CREW_SEND and self.order_in_flow == 1:
            allowed_answers = []
            answer_options_display = []
            userprofile = self.sent_to
            count = 1
            for crew in userprofile.crews.all():
                display = str(count) + ' - ' + crew.name
                answer_options_display.append(display)
                allowed_answers.append(str(count))
                count += 1
            if allowed_answers:
                self.allowed_answers = allowed_answers
                self.answer_options_display = answer_options_display
                self.save()


class QuestionResponse(BaseModelMixin, models.Model):

    text = models.TextField(null=True, blank=True)
    responder = models.ForeignKey(UserProfile, related_name='responses', on_delete=models.CASCADE)
    question_prompt = models.OneToOneField(QuestionPrompt, related_name='response', on_delete=models.CASCADE)

    @property
    def answer_given(self):
        return self.text is not None

    @property
    def acceptable_answer_given_for_prompt(self):
        return self.text in self.question_prompt.allowed_answers


@receiver(post_save, sender=QuestionResponse)
def trigger_next_flow_load(sender, instance, *args, **kwargs):
    question_prompt = instance.question_prompt
    if not question_prompt.next_flow_options:
        return
    if not instance.acceptable_answer_given_for_prompt:
        return

    next_flow_title = question_prompt.next_flow_options[question_prompt.allowed_answers.index(instance.text)]
    first_node = QuestionFlowNode.objects.get(title=next_flow_title, order=1)
    userprofile = question_prompt.sent_to
    event = question_prompt.event
    # TODO: Need to do ASYNC?
    # load_next_questions_for.apply_async((userprofile, first_node))
    userprofile._load_question_flow_list_into_queue(first_node, event)


class Crew(BaseModelMixin, models.Model):

    name = models.CharField(max_length=40, unique=True)
    userprofiles = models.ManyToManyField(UserProfile, related_name='crews')

    def __str__(self):
        return self.name


class Invitation(BaseModelMixin, models.Model):

    SENT = 'SENT'
    ACCEPTED = 'ACCEPTED'
    MAYBE = 'MAYBE'
    DENIED = 'DENIED'
    ERROR = 'ERROR'

    INVITATION_STATES = [
        (SENT, SENT),
        (ACCEPTED, ACCEPTED),
        (MAYBE, MAYBE),
        (DENIED, DENIED),
        (ERROR, ERROR)
    ]

    event = models.ForeignKey(Event, related_name='invitations', on_delete=models.CASCADE)
    sent_to = models.ForeignKey(UserProfile, related_name='invitations', on_delete=models.CASCADE)
    state = models.CharField(max_length=8, choices=INVITATION_STATES, default='SENT')
    text = models.TextField(null=False, blank=False)
    sent_count = models.IntegerField(default=1)

    def __str__(self):
        return 'Sent To: ' + self.sent_to.phone_number

    def is_save_response_successful(self, inbound_sms_body):
        cleaned_text = inbound_sms_body.lower().strip()
        if cleaned_text == 'yes':
            self.state = self.ACCEPTED
            self._append_text_to_next_userprofile_prompt_stack('Invitation accepted. Keep an eye out for a text from the organizer!')
        elif cleaned_text == 'maybe':
            self.state = self.MAYBE
            self._append_text_to_next_userprofile_prompt_stack('Thanks! If the run is short of people close to its start time we may reach out to you again.')
        elif cleaned_text == 'no':
            self.state = self.DENIED
            self._append_text_to_next_userprofile_prompt_stack('Response saved.')
        else:
            self.state = self.ERROR
            self.save()
            return False
        self.save()
        return True

    def _append_text_to_next_userprofile_prompt_stack(self, text):
        userprofile = self.sent_to
        userprofile.next_outbound_text = text
        userprofile.save()


# For now can only have one invitation pending at a time
@receiver(pre_save, sender=Invitation)
def update_all_other_invitations(sender, instance, *args, **kwargs):
    instance.sent_to.invitations.filter(state='SENT').update(state='DENIED')
