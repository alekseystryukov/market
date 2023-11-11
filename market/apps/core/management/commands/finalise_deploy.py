from django.core.management import call_command
from django.core.management import BaseCommand
from django.conf import settings
from io import StringIO, BytesIO
from .helpers.migrations import get_migrations_info, get_latest_applied
import subprocess
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

    def handle(self, *args, **options):
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


def upload_migrations_state():
    ver = settings.PROJECT_VERSION
    all_migrations = get_migrations_info()
    latest = get_latest_applied(all_migrations)

    file_obj = StringIO()
    json.dump({"latest": latest, "version": ver}, file_obj, indent=4)
    data = bytes(file_obj.getvalue(), encoding='utf-8')

    s3 = boto3.client('s3')
    s3.upload_fileobj(BytesIO(data), bucket_name, f"{bucket_prefix.strip('/')}/migrations/{ver}.json")
