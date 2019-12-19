from django.urls import path
from django.conf.urls import include
from base import views

urlpatterns = [
    path('hello', views.hello),
    path('sms', views.sms),
    path('callback', views.print_callback),
    path('api/v1/', include('base.api.urls'))
]
