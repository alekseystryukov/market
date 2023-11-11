from django.conf import settings
from django.core.serializers.json import DjangoJSONEncoder
from datetime import datetime, timezone
from uuid import uuid4
from typing import Literal, Optional
import logging
import boto3
import json
import os


logger = logging.getLogger(__name__)
events_client = None
scheduler_client = None


def get_events_client():
    global events_client
    if events_client is None:
        events_client = boto3.client('events')
    return events_client


def get_scheduler_client():
    global scheduler_client
    if scheduler_client is None:
        scheduler_client = boto3.client('scheduler')
    return scheduler_client


EVENT_TYPE_TRANS_STATUS_UPDATE = "/transaction/update-transaction-status/"
EVENT_TYPE_SYNCHRONIZE_TRANSACTIONS_CURRENT_STATUSES = "/synchronize-transactions-current-statuses/"


def schedule_command(
    start_time: datetime,
    command: str,
    args: list = None,
    kwargs: dict = None,
):
    """
    Example call: schedule_command(start_time=datetime.utcnow()+timedelta(seconds=30), command="migrate")
    """
    # start_time to UTC
    if start_time.tzinfo is None:
        start_time = start_time.replace(tzinfo=timezone.utc)
    elif start_time.tzinfo != timezone.utc:
        start_time = start_time.astimezone(timezone.utc)

    queue_arn = os.environ.get("SQS_QUEUE_ARN")
    if not queue_arn:
        return logger.warning("SQS_QUEUE_ARN is not configured. Scheduling task has been skipped.")

    role_arn = os.environ.get("SCHEDULER_RUN_TASK_ROLE_ARN")
    if not role_arn:
        return logger.warning("SCHEDULER_RUN_TASK_ROLE_ARN is not configured. Scheduling task has been skipped.")

    command_input = {
        "command": command,
        "args": [],
        "kwargs": {},
    }
    if args:
        command_input["args"] = args
    if kwargs:
        command_input["kwargs"] = kwargs

    response = get_scheduler_client().create_schedule(
        ActionAfterCompletion="DELETE",
        Description="",
        FlexibleTimeWindow={'Mode': 'OFF'},
        # GroupName=os.environ.get("SCHEDULER_TASK_GROUP_NAME", ""),
        Name=f"ScheduledTask-{uuid4().hex}",
        ScheduleExpression=f"at({start_time.strftime('%Y-%m-%dT%H:%M:%S')})",
        ScheduleExpressionTimezone='UTC',
        Target={
            'Arn': queue_arn,
            'Input': DjangoJSONEncoder().encode(command_input),
            'RoleArn': role_arn,
        },
        #  ClientToken='string',
        #  Unique, case-sensitive identifier you provide to ensure the idempotency of the request.
        #  This field is autopopulated if not provided.
    )
    logger.debug(f"Schedule result {response}")


def send_event(
    event_type: Literal[EVENT_TYPE_TRANS_STATUS_UPDATE, EVENT_TYPE_SYNCHRONIZE_TRANSACTIONS_CURRENT_STATUSES],
    method: Literal["POST"] = "POST",
    body: Optional[dict] = None,
    headers: Optional[dict] = None,
    query: Optional[dict] = None,
):
    if not settings.AWS_EVENT_BUS_NAME:
        return logger.warning("AWS_EVENT_BUS_NAME is not configured. Event send is skipped")

    details = {
        "envName": settings.ENV_NAME,
        "httpMethod": method,
        "body": body,
        "headers": headers,
        "queryStringParameters": query,
    }
    event = {
        "Source": settings.AWS_EVENT_SOURCE,
        "DetailType": event_type,
        "Detail": json.dumps(details),
        "EventBusName": settings.AWS_EVENT_BUS_NAME,
    }
    result = get_events_client().put_events(Entries=[event])
    # at the moment any problems with sending events,
    # should make operation "unsuccessful" if it's possible
    # the problem should be fixed and operations retried.
    return result
