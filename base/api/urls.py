from django.urls import path
from base.api import views


urlpatterns = [
    path('crews/<userprofile_id>', views.list_crews_for_user),
    path('crews/<userprofile_id>/', views.list_crews_for_user),
    path('crews/<userprofile_id>/create', views.create_crew_for_user),
    path('userprofile/<userprofile_id>', views.get_userprofile),
    path('signin', views.signin),
    path('register', views.register)
]
