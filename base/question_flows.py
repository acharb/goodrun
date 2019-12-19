from base.models import QuestionFlowNode


# Format: (
#     <Prompt>,
#     <Answer Options>,
#     <Answer Options Display>,
#     <next flow options by title corresponding to question answer>,
#     [<success handlers>]
# )


intro_question_flow = (
    QuestionFlowNode.INTRO,
    [
        (
            'You have no active events. Would you like to organize a run? (They expire within 72 hours)',
            ['yes', 'no'],
            ['\'yes\'', '\'no\''],
            [],
            ['handle_create_event_for_question_prompt']
        ),
        (
            'Would you like us to create a regular event for you? Or forward a text to partipants ASAP?',
            ['yes', 'no'],
            ['\'yes\' (for us to do the work)', '\'no\' (to forward text)'],
            [QuestionFlowNode.STRUCTURED, QuestionFlowNode.ASAP],
            ['handle_save_structure_type_to_event']
        )
    ]
)

asap_structure_flow_list = (
    QuestionFlowNode.ASAP,
    [   # Very coupled to saving text, for this question only inbound sms is not cleaned
        (
            'What message would you like us to forward to the partipants?',
            [],
            [],
            [],
            ['handle_save_forward_text_to_event']
        ),

        (
            'Do you want to send to a specific crew?',
            ['yes', 'no'],
            ['\'yes\'', '\'no\''],
            [QuestionFlowNode.CREW_SEND, QuestionFlowNode.NON_CREW_SEND],
            []
        )
    ]
)


crew_send_flow_list = (
    QuestionFlowNode.CREW_SEND,
    [
        # Very Coupled - this question needs to be first in list in order to load available crew for UserProfile
        (
            'Which Crew do you want to send to? Below are your available crews. (respond with digit)',
            # allowed_answers get added when QPrompt created
            ['no'],
            ['Looks like you have no crews. You can add one at: \n<crews url>. \n\nReply \'no\' to start again.'],
            [],
            ['handle_attach_confirmation_text_to_next_question', 'handle_save_crew_to_event']
        ),
        # Super coupled with QuestionPrompt.get_prompt_text, need to change there if changes here
        (
            'Great, please confirm the below text is right and we\'ll forward it.',
            ['yes', 'no'],
            ['\'yes\'', '\'no\''],
            [],
            ['handle_confirm_text', 'append_outbound_sms_text_for_userprofile']
        )
    ]
)


non_crew_send_flow_list = (
    QuestionFlowNode.NON_CREW_SEND,
    [
        (
            'How many people do you want us to forward to?',
            [str(i) for i in range(1, 16)],
            ['A digit between 1-15 (e.g. 12)'],
            [],
            ['handle_save_number_of_players_to_event', 'handle_attach_confirmation_text_to_next_question']
        ),
        # Super coupled with QuestionPrompt.get_prompt_text, need to change there if changes here
        (
            'Great, please confirm the below text is right and we\'ll forward it.',
            ['yes', 'no'],
            ['\'yes\'', '\'no\''],
            [],
            ['handle_confirm_text', 'append_outbound_sms_text_for_userprofile']
        )
    ]
)


regular_structure_flow_map = (
    QuestionFlowNode.STRUCTURED,
    [
        (
            'How many number of players do you want for this run?',
            [str(i) for i in range(1, 16)],
            ['A digit between 1-15 (e.g. 12)'],
            [],
            ['handle_save_number_of_players_to_event']
        ),

        # What is the address and name of the park or school?
        (
            'What is the exact location of the run?',
            [],
            [],
            [],
            ['handle_save_location_to_event']
        ),

        # look into time parsers 
        # day at time
        # (eg. tomorrow at 7:00PM)
        # eg. Monday at 8:00PM

        # eg. Tomorrow at 7PM
        (
            'What day and time do you want the run to be (EST)?',
            [],
            ['Date and time using format: \'MM/DD/YYYY HH:MM TT\' \n eg. 01/01/2019 03:30 PM'],
            [],
            ['handle_save_time_to_event']
        ),

        (
            'How long is the run?',
            [],
            ['eg. \'2 hours\''],
            [],
            ['handle_save_duration_to_event']
        ),
        (
            'Is the run full-court? If no, a half-court game is assumed.',
            ['yes', 'no'],
            ['\'yes\'', '\'no\''],
            [],
            ['handle_save_full_court_to_event']
        ),

        # LATER: 'INDOOR' vs Outdoor - if Indoor ask cost question
        # (
        #     'How expensive in total is the run? We\'ll divide the total by the number of committed players.',
        #     [],
        #     ['US Dollar amount \n eg. \'100\''],
        #     [],
        #     ['handle_save_cost_to_event']
        # ),
        (
            'Any additional notes you want us to relay to the participants?',
            [],
            ['Reply with \'no\' if none'],
            [],
            ['handle_save_additional_notes_to_event']
        ),
        (
            'You\'re done! Last question, what is your name (so we can let the invitees know who\'s making this run happen)?',
            [],
            [],
            [],
            ['handle_save_userprofile_name', 'handle_attach_confirmation_text_to_next_question']
        ),
        (
            'Great, please confirm and we\'ll send!',
            ['yes', 'no'],
            ['\'yes\'', '\'no\''],
            [],
            ['handle_confirm_text', 'append_outbound_sms_text_for_userprofile']
        )
    ]
)


def create_question_flow(flow_list_tup):
    title = flow_list_tup[0]
    flow_list = flow_list_tup[1]
    order_of_node = 1
    last_node = None
    for (prompt, answer_options, answer_options_display, next_flow_options, success_handlers) in flow_list:
            current_node = QuestionFlowNode.objects.create(
                title=title,
                prompt=prompt,
                allowed_answers=answer_options,
                answer_options_display=answer_options_display,
                order=order_of_node,
                next_flow_options=next_flow_options,
                success_handlers=success_handlers
            )
            if last_node:
                last_node.next = current_node
                last_node.save()
            last_node = current_node
            order_of_node += 1


def create_flows():
    create_question_flow(intro_question_flow)
    create_question_flow(asap_structure_flow_list)
    create_question_flow(regular_structure_flow_map)
    create_question_flow(crew_send_flow_list)
    create_question_flow(non_crew_send_flow_list)
