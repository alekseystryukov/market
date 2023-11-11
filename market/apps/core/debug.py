import json
import logging
from functools import wraps

from django.conf import settings
from django.views.debug import ExceptionReporter, SafeExceptionReporterFilter
from rest_framework.request import Request

logger = logging.getLogger(__name__)


def sensitive_drf_post_parameters(*parameters):
    """
    The method is the same as 'sensitive_post_parameters', but with supporting APIView from Django REST Framework
    Look at 'django.views.decorators.debug.sensitive_post_parameters' to get more information
    """

    def decorator(view):
        @wraps(view)
        def sensitive_drf_post_parameters_wrapper(request, *args, **kwargs):
            if isinstance(request, Request):  # The Request class from Django REST Framework
                request._request.sensitive_post_parameters = parameters or '__ALL__'
            else:  # just simple Django Request
                request.sensitive_post_parameters = parameters or '__ALL__'

            return view(request, *args, **kwargs)

        return sensitive_drf_post_parameters_wrapper

    return decorator


class JSONSafeExceptionReporterFilter(SafeExceptionReporterFilter):
    def get_json_data_parameters(self, request):
        """
        This method prepares 'request.body' similarly to the way as 'get_post_parameters' prepares 'request.POST'.
        It needs only in case when content_type is 'application/json',
        because 'request.POST' is always empty in this case
        (https://docs.djangoproject.com/en/4.2/ref/request-response/#django.http.HttpRequest.POST)
        """
        if request is None or request.content_type != 'application/json':
            return {}

        try:
            # You should remember that DRF runs 'parse' method of a parser when you access 'request.data' at first time
            # and 'request' in APIView is a wrapper on the original Django request.
            # You work with the original Django request here.
            # Since this method is only for 'application/json', 'apps.core.parsers.JSONParser' will process the request.
            # This custom parser sets a new attribute 'json_body' to Django Request (not DRF Request), because you
            # won't be able to get input data from the request after view processing (read about RawPostDataException).
            # but if you don't call 'request.data', then no parsers will be triggered. It means that the request
            # won't have 'json_body' attribute and actually no data was read from the original request.
            # In this case we try to read data from 'request.body' directly here.
            if hasattr(request, 'json_body'):
                data = request.json_body.copy()
            else:
                data = json.loads(request.body) if request.body else {}
        except Exception as e:
            # I'm not sure that the code above works always correctly. This requires a more thorough review.
            # This exception block was added for safety and debugging.
            # You can remove it if you are sure that it works correctly (but I'm not sure 😁).
            logger.error('Unexpected error occurs in "get_json_data_parameters" of the exception reporter.',
                         extra={'message_id': 'get_json_data_parameters_unexpected_error',
                                'error_type': str(type(e)),
                                'error': str(e)})
            return {}

        sensitive_post_parameters = getattr(request, "sensitive_post_parameters", [])

        if self.is_active(request):
            if sensitive_post_parameters == "__ALL__":
                # Cleanse all parameters.
                for k in data:
                    data[k] = self.cleansed_substitute
            else:
                # Cleanse only the specified parameters.
                for param in sensitive_post_parameters:
                    if param in data:
                        data[param] = self.cleansed_substitute

        return data


class JSONExceptionReporter(ExceptionReporter):
    @property
    def html_template_path(self):
        return settings.BASE_DIR / 'templates' / 'technical_500.html'

    @property
    def text_template_path(self):
        return settings.BASE_DIR / 'templates' / 'technical_500.txt'

    def get_traceback_data(self):
        assert isinstance(self.filter, JSONSafeExceptionReporterFilter)

        context = super().get_traceback_data()
        context['filtered_json_data_items'] = self.filter.get_json_data_parameters(self.request).items()
        return context
