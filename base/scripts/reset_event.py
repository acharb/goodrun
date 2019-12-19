
userprofile = UserProfile.objects.get(phone_number='')
# event = userprofile.events_organized.filter(active=True)[0]

question_prompt = userprofile.questions.filter(flow_type='ASAP').filter(active=True).order_by('created_at').last()    
response = question_prompt.response
response.text = None
response.save()
