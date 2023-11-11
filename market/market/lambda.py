import json

from .wsgi import application
from django.core.management import call_command
import serverless_wsgi
import logging

logger = logging.getLogger(__name__)


def http_call_from_eventbus_event(event):
    details = event["detail"]
    headers = details.get("headers") or {}
    headers["content-type"] = headers.get("content-type", "application/json")
    result = {
        "httpMethod": details.get("httpMethod", "POST"),
        "path": event["detail-type"],
        "headers": headers,
        "queryStringParameters": details.get("queryStringParameters") or {},
    }
    body = details.get("body")
    if isinstance(body, dict):
        result["body"] = json.dumps(body)  # wsgi wants to parse this itself
    return result


def handler(event, context):
    if "httpMethod" in event:  # event from elb
        return serverless_wsgi.handle_request(application, event, context)
    elif "command" in event:  # command call
        args = event.get("args") or tuple()
        kwargs = event.get("kwargs") or {}
        return call_command(event["command"], *args, **kwargs)
    else:  # event from amazon EventBridge
        try:
            http_like_event = http_call_from_eventbus_event(event)
            result = serverless_wsgi.handle_request(application, http_like_event, context)
        except Exception as e:
            logger.error(f"Failed to process event {event}")
            raise e
        else:
            status = result["statusCode"]
            if status > 201:
                logger.error(
                    f"Unexpected status '{status}': {result['body']}\n"
                    f"while processing an event from EventBus: {event}"
                )
            return result
