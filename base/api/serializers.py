from rest_framework import serializers
from base.models import Crew


class CreateCrewSerializer(serializers.Serializer):
    crew_name = serializers.CharField()
    phone_numbers = serializers.JSONField()


class UserProfileSerializer(serializers.Serializer):

    id = serializers.IntegerField(allow_null=False)
    name = serializers.CharField(read_only=True)
    phone_number = serializers.CharField(read_only=True)


class CrewSerializer(serializers.ModelSerializer):

    userprofiles = UserProfileSerializer(many=True)

    class Meta:
        model = Crew
        fields = '__all__'
