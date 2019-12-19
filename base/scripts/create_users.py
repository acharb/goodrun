from datetime import datetime, timedelta
import phonenumbers

def get_formatted_number(number):
    try:
        parsed = phonenumbers.parse(number)
    except phonenumbers.NumberParseException as npe:
        parsed = phonenumbers.parse('+1{}'.format(number))
    formatted_number = phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.INTERNATIONAL)
    return formatted_number

# alec_user = UserProfile.objects.create(phone_number=get_formatted_number(alec_number))


cornell_crew = Crew.objects.get(name='Cornell Club Bball')
bryson = UserProfile.objects.create(phone_number=get_formatted_number(''))
bryson.crews.add(cornell_crew)
bryson.save()
# google_user = UserProfile.objects.create(phone_number=get_formatted_number('3478813810‬'))
# google_user.crews.add(cornell_crew)
# google_user.save()

# new_event = Event.objects.create(
#     confirm_create_event = True,
#     organizer = alec_user,
#     number_of_players = 12,
#     location = 'Williamsburg open park',
#     date_time = datetime.now() + timedelta(days=2),
#     duration = timedelta(days=0, hours=2),
#     full_court = True,
#     cost = 150.00,
#     additional_notes = 'First Event created',
# )
