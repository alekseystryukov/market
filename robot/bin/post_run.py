#!/usr/bin/env python3
import xml.etree.ElementTree as ET
import logging
from uuid import uuid4
import requests
import boto3
import mimetypes
import os.path
import os


logger = logging.getLogger(__name__)
account_id = os.environ["AWS_ACCOUNT_ID"]
env_name = os.environ["ENV_NAME"]
bucket_name = os.environ["S3_BUCKET"]
bucket_url = os.environ["S3_URL"]
reports_dir = os.environ["ROBOT_REPORTS_DIR"]
webhook_uri = os.environ["SLACK_WEBHOOK_URI"]
bucket_prefix = os.environ.get("S3_PREFIX", "").strip('/')
s3 = boto3.client('s3')
mimetypes_obj = mimetypes.MimeTypes()


def total_stats():
    try:
        root = ET.parse(os.path.join(reports_dir, "output.xml")).getroot()
        stats = root.find("statistics").find("total").find("stat").attrib
        return {k: int(v) for k, v in stats.items()}
    except Exception:
        return {'pass': 0, 'fail': 0, 'skip': 0}


def upload_directory(directory_path, report_uid):
    directory_path_len = len(directory_path)
    for root, dirs, files in os.walk(directory_path):
        # upload all files
        for file_name in files:
            full_file_name = os.path.join(root, file_name)
            extra_args = {"ACL": "public-read"}
            mime_type = mimetypes_obj.guess_type(full_file_name)[0]
            if mime_type:
                extra_args["ContentType"] = mime_type
            with open(full_file_name, "rb") as f:
                relative_path = full_file_name[directory_path_len + 1:]
                s3.upload_fileobj(f, bucket_name, f"{bucket_prefix}/{report_uid}/{relative_path}",
                                  ExtraArgs=extra_args)


def send_slack_notification(report_uid):
    base_url = os.path.join(bucket_url, report_uid)
    stats = total_stats()
    is_success = ":triumph:" if stats["fail"] == 0 and stats["pass"] > 0 else ":face_with_spiral_eyes:"
    message = f"RobotTest report is ready\n" \
              f"Stats {is_success}: {stats}\n" \
              f"<{base_url}/report.html|Report>\n<{base_url}/log.html|Log>"
    hook_request = {
        "blocks": [
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": message
                }
            },
            {
                "type": "context",
                "elements": [
                    {
                        "type": "image",
                        "image_url": "https://cdn-icons-png.flaticon.com/512/1246/1246314.png",
                        "alt_text": "images"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"Account: *{account_id}*"
                    }
                ]
            },
            {
                "type": "context",
                "elements": [
                    {
                        "type": "image",
                        "image_url": "https://img.freepik.com/free-icon/gift_318-900115.jpg",
                        "alt_text": "images"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"Envoronment: *{env_name}*"
                    }
                ]
            }
        ]
    }
    response = requests.post(webhook_uri, json=hook_request)
    if response.status_code != 200:
        logger.error(f"Error from the slack hook call: {response.status_code} {response.text}",
                     extra=hook_request)


def main():
    report_uid = uuid4().hex
    print("Sending files to bucket")
    upload_directory(reports_dir, report_uid=report_uid)
    print("Sending a slack notification")
    send_slack_notification(report_uid)


if __name__ == "__main__":
    main()
