from market.logging import request_id_context
from django.http import HttpResponse
from uuid import uuid4


def request_id_middleware(get_response):
    def middleware(request):
        request_id = request.headers.get("X-Request-ID") or uuid4().hex
        with request_id_context(request_id):
            response = get_response(request)
        response.headers['X-Request-ID'] = request_id
        return response
    return middleware


def ping_middleware(get_response):
    def middleware(request):
        if request.META["PATH_INFO"] == "/ping/":
            return HttpResponse("pong")
        else:
            return get_response(request)
    return middleware
