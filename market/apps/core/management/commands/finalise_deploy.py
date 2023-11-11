from django.core.management import call_command
from django.core.management import BaseCommand
from django.conf import settings
from packaging import version
from io import StringIO, BytesIO
from .helpers.migrations import get_migrations_info, get_latest_applied
from .helpers.slack import send_slack_notification
import subprocess
import traceback
import logging
import boto3
import json
import os

logger = logging.getLogger(__name__)
releases_file = "market/releases.txt"
bucket_name = os.environ["S3_STATIC_BUCKET"]
bucket_prefix = os.environ.get("S3_STATIC_BUCKET_PREFIX", "")


class Command(BaseCommand):
    """
    This command works only on AWS Lambda, not on ECS
    since awscli ver1 doesn't support AWS_CONTAINER_CREDENTIALS_RELATIVE_URI
    """

    def add_arguments(self, parser):
        parser.add_argument('--hook_uri', type=str, required=True)
        parser.add_argument('--stack_name', type=str, required=True)

    def handle(self, *args, **options):
        rollback = False
        image = None
        changes = None
        errors = []
        stack_name = options["stack_name"]
        try:
            # static files
            call_command("collectstatic", interactive=False)
            subprocess.run(
                [
                    'aws', 's3', 'sync',
                    settings.STATIC_ROOT,
                    f's3://{bucket_name}{bucket_prefix}/static',
                    '--acl', 'public-read',
                ],
                check=True,
                capture_output=True
            )
            # migrate and save migrations state
            call_command("migrate", interactive=False)
            upload_migrations_state()
        except subprocess.CalledProcessError as e:
            errors.append(e.stderr.decode())
            errors.append(traceback.format_exc())
            raise
        except Exception:
            errors.append(traceback.format_exc())
            raise
        else:
            last_images = get_last_images(stack_name, limit=2)
            if last_images:
                image = last_images[0]
                if len(last_images) > 1:
                    previous_img = last_images[1]
                    previous_tag = previous_img.split(":")[-1]  # For ex:  1.2.0
                    most_recent_tag = image.split(":")[-1]  # For ex:  1.2.3
                    previous_version = version.parse(previous_tag)
                    most_recent_version = version.parse(most_recent_tag)
                    if previous_version > most_recent_version:
                        rollback = previous_tag
                    if not rollback:
                        changes = get_release_changes(previous_version, most_recent_version)
        finally:
            send_slack_notification(
                hook_uri=options["hook_uri"],
                new_version=image.split("/")[-1] if image else stack_name,
                account_id=settings.AWS_ACCOUNT,
                region=settings.AWS_REGION,
                env_name=settings.ENV_NAME,
                errors=errors,
                changes=changes,
                rollback=rollback,
            )


def get_release_changes(prev_version, next_version):
    """
    Accept previous and current version.
    Parses txt file with tag+description contents. Format is:
    "version1==>description1===version2==>description===2"
    See `make write-versions-file`

    Returns a list of (version, changes text) pairs. For ex.:
    [("1.2.1", "Fixed a bug in the awesome feature"),
     ("1.2.0", "The awesome feature")]
    """
    try:
        with open(releases_file) as f:
            releases_text = f.read()

        changes = []
        for tag_info in releases_text.split("==="):
            parts = tag_info.split("==>")
            if len(parts) == 2:
                tag = parts[0].strip()
                try:
                    parsed_tag = version.parse(tag)
                except version.InvalidVersion:
                    continue
                if prev_version < parsed_tag <= next_version:
                    changes.append(
                        (tag, parts[1].strip())
                    )
        return changes
    except Exception as e:
        logger.exception(e)


def get_last_images(stack_name, limit=2):
    """
    Search stack event history for successful create/update lambda function
    to get image url from the properties
    """
    results = []
    try:
        response = subprocess.check_output([
            "aws", "cloudformation", "describe-stack-events",
            "--stack-name", stack_name,
            "--max-items", "400",
            "--query",
            "StackEvents[?ResourceType=='AWS::ECS::TaskDefinition' && "
            "(ResourceStatus=='CREATE_COMPLETE' || ResourceStatus=='UPDATE_COMPLETE')].[ResourceProperties]"
        ])
        result = json.loads(response)  # result will be ["{k: v, ...}", "{k: v, ...}"]
        for prop_json in result:
            properties = json.loads(prop_json[0])
            image_uri = properties["ContainerDefinitions"][0]["Image"]
            if not results or image_uri != results[-1]:
                results.append(image_uri)
                if len(results) >= limit:
                    break
    except Exception as e:
        logger.exception(e)
    return results


def upload_migrations_state():
    ver = settings.PROJECT_VERSION
    all_migrations = get_migrations_info()
    latest = get_latest_applied(all_migrations)

    file_obj = StringIO()
    json.dump({"latest": latest, "version": ver}, file_obj, indent=4)
    data = bytes(file_obj.getvalue(), encoding='utf-8')

    s3 = boto3.client('s3')
    s3.upload_fileobj(BytesIO(data), bucket_name, f"{bucket_prefix.strip('/')}/migrations/{ver}.json")
