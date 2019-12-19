from base.commands import handle_command_for

userprofile = UserProfile.objects.get(phone_number='') 
inbound_sms = '/optin'


    REMIND = '/remind'
    ACCEPT = '/accepted'
    MAYBE = '/maybe'
    EXPIRE = '/expire'
    OPTOUT = '/optout'
    OPTIN = '/optin'
    RESET = '/reset'

test_cases= ['/optin', '/optout', '/remind', '/accepted', '/expire', '/maybe', '/reset', \
    '/no command', 'non command', '', ' ']

results = {}

handle_command_for(userprofile, inbound_sms)

def test_optin():
    userprofile = UserProfile.objects.get(phone_number='')
    cornell_crew = Crew.objects.get(name='Cornell Club Bball')
    userprofile.opted_out = True
    handle_command_for(userprofile, '/optin')
    if not cornell_crew.userprofiles.filter(id=userprofile.id):
        return False
    if userprofile.opted_out != False:
        return False
    return True

