from time import sleep
from .wsgi import application
from urllib.parse import urlencode
from wsgiref.headers import Headers
from django.core.management import call_command
import json
import boto3
import logging
import sys
import os
import io


logger = logging.getLogger(__name__)


def process_message(msg):
    """
     'Body': '{"command": "migrate", "args": ["test_arg"], "kwargs": {"test_kwarg_key": "test_kwarg_value"}}'}
     OR
     'Body': '{\"version\":\"0\",\"id\":\"89dd703d-ee5d-451c-0ef0-63ac3c461f14\",
         \"detail-type\":\"/transaction/submit/\",\"source\":\"com.viamericas.rc\",\"account\":\"367570673549\",
         \"time\":\"2023-10-11T12:05:33Z\",\"region\":\"us-east-1\",\"resources\":[],
         \"detail\":{\"envName\":\"DEV\",\"httpMethod\":\"POST\",
            \"body\":{\"chain_id\":\"USA000002\",\"name\":\"What\",\"short_name\":\"wht\",\"prefix\":\"111\",
                \"branch_id\":\"A00002\"},\"headers\":null,\"queryStringParameters\":null}}'
    """
    msg_body = json.loads(msg['Body'])
    if "command" in msg_body:
        args = msg_body.get("args") or tuple()
        kwargs = msg_body.get("kwargs") or {}
        return call_command(msg_body["command"], *args, **kwargs)
    else:
        return process_request(msg_body)


def setup_environ_items(environ, headers):
    for key, value in environ.items():
        if isinstance(value, str):
            environ[key] = value.encode("utf-8").decode("latin1", "replace")

    for key, value in headers.items():
        key = "HTTP_" + key.upper().replace("-", "_")
        if key not in ("HTTP_CONTENT_TYPE", "HTTP_CONTENT_LENGTH"):
            environ[key] = value
    return environ


def process_request(message):
    details = message["detail"]

    headers = details.get("headers") or {}
    headers["content-type"] = headers.get("content-type", "application/json")
    allowed_hosts = os.getenv("ALLOWED_HOSTS", "*").split(",")
    if allowed_hosts and "*" not in allowed_hosts:
        headers["Host"] = allowed_hosts[0]
    headers = Headers(list(headers.items()))

    body = details.get("body", "")
    if isinstance(body, dict):
        body = json.dumps(body)
    body = body.encode()

    environ = {
        "CONTENT_LENGTH": str(len(body)),
        "CONTENT_TYPE": headers.get("Content-Type", ""),
        "PATH_INFO": message["detail-type"],
        "QUERY_STRING": urlencode(details.get("queryStringParameters") or {}),
        "REMOTE_ADDR": "",
        "REMOTE_USER": "",
        "REQUEST_METHOD": details.get("httpMethod", "POST"),
        "SCRIPT_NAME": "",
        "SERVER_NAME": headers.get("Host", "127.0.0.1"),
        "SERVER_PORT": headers.get("X-Forwarded-Port", "443"),
        "SERVER_PROTOCOL": "HTTP/1.1",
        "wsgi.errors": sys.stderr,
        "wsgi.input": io.BytesIO(body),
        "wsgi.multiprocess": False,
        "wsgi.multithread": False,
        "wsgi.run_once": False,
        "wsgi.url_scheme": headers.get("X-Forwarded-Proto", "https"),
        "wsgi.version": (1, 0),
    }
    environ = setup_environ_items(environ, headers)
    result = application(environ, lambda *_: _)
    return result


def main():
    # Create SQS client
    sqs = boto3.client('sqs')
    queue_url = os.environ.get("SQS_QUEUE_URL")

    empty_tries = 0
    # https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/sqs/client/receive_message.html#
    while True:
        response = sqs.receive_message(
            QueueUrl=queue_url,
            MessageAttributeNames=['All'],
            MaxNumberOfMessages=10,
            VisibilityTimeout=10,
            WaitTimeSeconds=20
        )
        messages = response.get("Messages")
        if messages:
            empty_tries = 0
            for message in messages:
                receipt_handle = message['ReceiptHandle']
                try:
                    result = process_message(message)
                except Exception as e:
                    logger.exception(e)
                    logger.error(
                        f"Unexpected error while processing msg from EventBus: {message}"
                    )
                else:
                    if result and result.status_code > 201:
                        logger.error(
                            f"Unexpected status '{result.status_code}': {result.content}\n"
                            f"while processing msg from EventBus: {message}"
                        )

                # Delete received message from queue
                sqs.delete_message(
                    QueueUrl=queue_url,
                    ReceiptHandle=receipt_handle
                )
                logger.info(f'Received and deleted message: {message}')
        else:
            empty_tries += 1
            sleep(min(empty_tries, 10))


if __name__ == "__main__":
    main()
