from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt

from base.receive.receive_sms import handle_sms_receive


def hello(request):
    return HttpResponse('Why, hello')


@csrf_exempt
def sms(request):
    resp = handle_sms_receive(request)
    print('RESPONSE: \n%s' % resp.to_xml())
    return HttpResponse(str(resp))


@csrf_exempt
def print_callback(request):
    # import ipdb; ipdb.set_trace()
    print(request.POST)
    return HttpResponse(request)
