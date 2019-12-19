from rest_framework.response import Response
from rest_framework.decorators import api_view
from rest_framework import status

from django.http import Http404
from django.db.utils import IntegrityError

from base.models import UserProfile, Crew
from base.api.serializers import UserProfileSerializer, CrewSerializer, CreateCrewSerializer

from base.utils import format_phone_number

import bcrypt


def _get_userprofile_or_404(userprofile_id):
    serializer = UserProfileSerializer(data={'id': userprofile_id})
    serializer.is_valid(raise_exception=True)
    userprofile_id = serializer.validated_data.get('id')
    userprofile = None
    try:
        userprofile = UserProfile.objects.get(id=userprofile_id)
    except UserProfile.DoesNotExist:
        raise Http404
    return userprofile


@api_view(('GET',))
def list_crews_for_user(request, userprofile_id):
    userprofile = _get_userprofile_or_404(userprofile_id)
    crews = userprofile.crews.all()
    crew_serializer = CrewSerializer(crews, many=True)
    return Response(crew_serializer.data)


# TODO Add serializer
@api_view(('POST',))
def create_crew_for_user(request, userprofile_id):
    userprofile = _get_userprofile_or_404(userprofile_id)

    crew_name = request.query_params.get('crew_name')
    try:
        new_crew = Crew.objects.create(name=crew_name)
        new_crew.userprofiles.add(userprofile)
        new_crew.save()
    except IntegrityError:
        return Response({'error': 'Crew with that name already exists'}, status=status.HTTP_400_BAD_REQUEST)

    numbers_list = request.query_params.getlist('numbers[]')
    names_list = request.query_params.getlist('names[]')

    index = 0
    for number in numbers_list:
        formatted_number = format_phone_number(number)
        name = names_list[index]
        try:
            new_user = UserProfile.objects.create(phone_number=formatted_number, name=name)
            new_crew.userprofiles.add(new_user)
        except IntegrityError:
            new_user = UserProfile.objects.get(phone_number=formatted_number)
            new_crew.userprofiles.add(new_user)

    crew_serializer = CrewSerializer(new_crew)
    return Response(crew_serializer.data)


@api_view(('GET',))
def get_userprofile(request, userprofile_id):
    userprofile = _get_userprofile_or_404(userprofile_id)
    user_serializer = UserProfileSerializer(userprofile)
    return Response(user_serializer.data)


@api_view(('GET',))
def signin(request):
    phone_number = request.query_params.get('phone_number')
    formatted_number = format_phone_number(phone_number)
    try:
        userprofile = UserProfile.objects.get(phone_number=formatted_number)
    except UserProfile.DoesNotExist:
        return Response({'error': 'Account Does Not Exist'}, status=status.HTTP_404_NOT_FOUND)

    if not userprofile.password:
        return Response({'error': 'No Password for Account Created'}, status=status.HTTP_400_BAD_REQUEST)

    db_password = str.encode(userprofile.password)
    password = str.encode(request.query_params.get('password'))
    if bcrypt.checkpw(password, db_password):
        user_serializer = UserProfileSerializer(userprofile)
        return Response(user_serializer.data)
    return Response({'error': 'Incorrect Password'}, status=status.HTTP_400_BAD_REQUEST)


@api_view(('POST',))
def register(request):
    phone_number = request.query_params.get('phone_number')
    formatted_number = format_phone_number(phone_number)
    try:
        userprofile = UserProfile.objects.get(phone_number=formatted_number)
    except UserProfile.DoesNotExist:
        return Response({'error': 'Account Does Not Exist. Text GoodRuns first to create account.'}, status=status.HTTP_404_NOT_FOUND)

    if userprofile.password:
        return Response({'error': 'Account already has password. Reach out to admins to change password.'}, status=status.HTTP_400_BAD_REQUEST)

    password = str.encode(request.query_params.get('password'))
    hashed_pw = bcrypt.hashpw(password, bcrypt.gensalt())

    userprofile.password = hashed_pw.decode()
    userprofile.save()
    user_serializer = UserProfileSerializer(userprofile)
    return Response(user_serializer.data)
