



new_question = Question.objects.create(
    sent_to = userprofile
)

new_inv = Invitation.objects.create(
    sent_to = userprofile,
    event = new_event
)
