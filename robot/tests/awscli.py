#!/usr/bin/env python3
import mimetypes
from datetime import datetime
import logging
import boto3
import os


logger = logging.getLogger(__name__)

mimetypes_obj = mimetypes.MimeTypes()
bucket_name = os.environ["S3_STATIC_BUCKET"]
bucket_prefix = os.environ.get("S3_STATIC_BUCKET_PREFIX", "")
s3_client = None


def get_s3_client():
    global s3_client
    if s3_client is None:
        s3_client = boto3.client('s3')
    return s3_client

#
# def sync_directory_to_s3_bucket(source: str, destination: str):
#     subprocess.run(
#         [
#             'aws', 's3', 'sync',
#             source,
#             f's3://{bucket_name}{bucket_prefix}/{destination}',
#             '--acl', 'public-read',
#         ],
#         check=True,
#         capture_output=True
#     )


def upload_directory(source, destination):
    directory_path_len = len(source)
    for root, dirs, files in os.walk(source):
        # upload all files
        for file_name in files:
            full_file_name = os.path.join(root, file_name)
            extra_args = {"ACL": "public-read"}
            mime_type = mimetypes_obj.guess_type(full_file_name)[0]
            if mime_type:
                extra_args["ContentType"] = mime_type
            with open(full_file_name, "rb") as f:
                relative_path = full_file_name[directory_path_len + 1:]
                get_s3_client().upload_fileobj(
                    f,
                    bucket_name,
                    f"{bucket_prefix}/{destination}/{relative_path}",
                    ExtraArgs=extra_args
                )


def upload_file(file_name, destination):
    with open(file_name, "rb") as f:
        short_file_name = file_name.split("/")[-1]
        get_s3_client().upload_fileobj(
            f,
            bucket_name,
            f"{bucket_prefix}/{destination}/{short_file_name}",
        )


def sync_media_files_to_s3(dir_name: str, store_id: str):
    date = datetime.utcnow().isoformat().split("T")[0]
    destination = f"media/{store_id}/{date}"
    upload_directory(source=dir_name, destination=destination)


def sync_data_files_to_s3(data_file: str, store_id: str):
    date = datetime.utcnow().isoformat().split("T")[0]
    destination = f"media/{store_id}/{date}"
    upload_file(file_name=data_file, destination=destination)


if __name__ == "__main__":
    print("hello")
    sync_data_files_to_s3("/opt/robotframework/reports/data/data.json", "test")
