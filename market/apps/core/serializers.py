from rest_framework import serializers


class ResponseErrorSerializer(serializers.Serializer):
    class ErrorComponentSerializer(serializers.Serializer):
        message = serializers.CharField()
        location = serializers.CharField(required=False)

    errors = serializers.ListField(
        allow_empty=False, child=serializers.DictField(allow_empty=False, child=ErrorComponentSerializer())
    )
