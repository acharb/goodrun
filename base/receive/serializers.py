from rest_framework import serializers


class InboundSmsSerializer(serializers.Serializer):
    phone_number = serializers.CharField(required=True)
    body = serializers.CharField(required=True, allow_blank=True)
