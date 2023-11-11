import codecs
from decimal import Decimal

from django.conf import settings
from rest_framework import renderers
from rest_framework.exceptions import ParseError
from rest_framework.parsers import BaseParser
from rest_framework.settings import api_settings
from rest_framework.utils import json


class JSONParser(BaseParser):
    """
    Parses JSON-serialized data.

    This class is a replacement for the 'rest_framework.parsers.JSONParser'
    Custom (overridden) feature is parsing floating point numbers as objects of type 'decimal.Decimal'
    """
    media_type = 'application/json'
    renderer_class = renderers.JSONRenderer
    strict = api_settings.STRICT_JSON

    def parse(self, stream, media_type=None, parser_context=None):
        """
        Parses the incoming bytestream as JSON and returns the resulting data.
        """
        parser_context = parser_context or {}
        encoding = parser_context.get('encoding', settings.DEFAULT_CHARSET)
        request = parser_context.get('request')  # it should be an instance of Request class from Django REST Framework
        try:
            decoded_stream = codecs.getreader(encoding)(stream)
            parse_constant = json.strict_constant if self.strict else None

            # The difference from original JSONParser class is 'parse_float=Decimal'
            json_body = json.load(decoded_stream, parse_constant=parse_constant, parse_float=Decimal)
        except ValueError as exc:
            raise ParseError('JSON parse error - %s' % str(exc))

        if request:  # I'm not sure if there is a case when the request is None
            request._request.json_body = json_body

        return json_body
