from django.core.management import call_command
from django.core.management import BaseCommand
from .helpers.migrations import get_migrations_info
from io import BytesIO
import logging
import boto3
import json
import os

logger = logging.getLogger(__name__)
bucket_name = os.environ["S3_STATIC_BUCKET"]
bucket_prefix = os.environ.get("S3_STATIC_BUCKET_PREFIX", "")


class Command(BaseCommand):

    def add_arguments(self, parser):
        parser.add_argument('--target', type=str, required=True)

    def handle(self, *args, **options):
        ver = options["target"]

        file_obj = BytesIO()
        s3 = boto3.client('s3')
        s3.download_fileobj(bucket_name,  f"{bucket_prefix.strip('/')}/migrations/{ver}.json", file_obj)
        data = json.loads(file_obj.getvalue())
        latest_versions = data["latest"]

        all_migrations = get_migrations_info()
        for app in all_migrations.keys():
            latest = latest_versions.get(app, "zero")
            try:
                call_command("migrate", app, latest, interactive=False)
            except Exception as e:
                logger.exception(e)
