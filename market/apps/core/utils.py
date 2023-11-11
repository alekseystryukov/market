import datetime
import string
import secrets
import logging
from functools import wraps
from typing import Optional, Union, List, Dict

from django.contrib import messages
from django.http import JsonResponse
from django.urls import reverse
from drf_yasg.utils import swagger_auto_schema
from rest_framework import status
from rest_framework.response import Response
from market.awscli import send_event


logger = logging.getLogger(__name__)


def get_response_body_errors(
        errors: Optional[Union[str, List[str]]] = None,
        serializer_errors: Optional[Dict[str, List[str]]] = None
) -> Dict[str, List[Dict[str, str]]]:
    """
    :return: dict. For example,
        {
            "errors": [
                {"message": "Required thing", "location": "dishes[0].beetroot"},
                {"message": "Retry after 30 seconds"}
            ]
        }
    """
    if errors is None and serializer_errors is None:
        raise ValueError('Must be provided either "errors" or "serializer_errors"')

    result_errors = []

    if serializer_errors is not None:
        result_errors.extend([
            {'message': message, 'location': field_name}
            for field_name, list_of_errors in serializer_errors.items()
            for message in list_of_errors
        ])

    if errors is not None:
        if isinstance(errors, str):
            errors = [errors]

        result_errors.extend([{'message': message} for message in errors])

    return {'errors': result_errors}


def swagger_auto_schema_wrapper(
        doc: 'BaseSwaggerAPIViewDoc',  # noqa: F821
        request_serializer_cls: Optional['Serializer'] = None,  # noqa: F821
        **kwargs,
):
    def wrapper(func):
        return swagger_auto_schema(
            tags=doc.tags,
            operation_summary=doc.summary,
            operation_description=doc.description,
            request_body=request_serializer_cls,
            responses=doc.responses,
            **kwargs
        )(func)

    return wrapper


def validate_request_data(serializer_cls, method: str = 'POST'):
    def wrapper(func):
        def inner(self, request, *args, **kwargs):
            ser = serializer_cls(data=request.data if method == 'POST' else request.query_params)
            if not ser.is_valid():
                errors = get_response_body_errors(serializer_errors=ser.errors)
                return Response(data=errors, status=status.HTTP_400_BAD_REQUEST)

            return func(self, request, *args, serializer=ser, **kwargs)

        return inner

    return wrapper


def get_instance_or_ajax_redirect(error_message, redirect_url):
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(self, request, object_id, *args, **kwargs):
            try:
                instance = self.model.objects.get(id=object_id)
            except self.model.DoesNotExist:
                self.message_user(request, error_message, level=messages.ERROR)
                return JsonResponse(data={'redirectUrl': reverse(redirect_url)})

            return view_func(self, request, object_id, *args, instance=instance, **kwargs)

        return _wrapped_view

    return decorator


def to_percentage(value: float, decimal_digits=2) -> float:
    return round(value * 100, decimal_digits)


def mask_string(value: str, showed_number_of_digits: int = 4) -> str:
    return f'{value[:showed_number_of_digits]}****{value[-showed_number_of_digits:]}' if value else ''


def phone_mask(phone: str) -> str:
    return f'****{phone[-4:]}'


def email_mask(email: str) -> str:
    """
    :return: str. For example: examplemail@gmail.com would be transformed to e****l@gmail.com
    """
    name, domain = email.split('@')
    return f'{name[0]}****{name[-1]}@{domain}'


def get_parts_of_timedelta(delta: datetime.timedelta) -> Dict[str, int]:
    total_seconds = delta.total_seconds()

    days, rest = divmod(total_seconds, 86400)
    hours, rest = divmod(rest, 3600)
    minutes, seconds = divmod(rest, 60)

    return {
         'days': int(days),
         'hours': int(hours),
         'minutes': int(minutes),
         'seconds': int(seconds)
    }


def generate_id_for_session() -> str:
    alphabet = string.ascii_letters + string.digits
    # from official documentation https://docs.python.org/3/library/secrets.html#recipes-and-best-practices
    return ''.join(secrets.choice(alphabet) for _ in range(32))
