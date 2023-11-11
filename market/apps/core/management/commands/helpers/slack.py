import requests
import logging

logger = logging.getLogger(__name__)


def send_slack_notification(*_, hook_uri, new_version, account_id, region, env_name, errors, changes, rollback):
    if errors:
        errors = "\n".join(errors)
        errors = errors.replace('"', "'")
        if len(errors) > 2000:
            errors = f"{errors[:1000]}\n...\n{errors[-1000:]}"
        message = f"Release *{new_version}* failed the last stage\n```{errors}```"
    else:
        message = f"Release *{new_version}* has been deployed\n"
        if rollback:
            message += f":warning: It looks like a rollback from {rollback}\n" \
                        ":pray: Any migrations reverts should have been done before this rollback\n"
        elif changes:
            changes_text = "\n".join(f"{v}\n{info}\n" for v, info in changes)
            message += f"```{changes_text}```"
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
                        "image_url": "https://cdn-icons-png.flaticon.com/128/10096/10096797.png",
                        "alt_text": "images"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"Region: *{region}*"
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
    response = requests.post(hook_uri, json=hook_request)
    if response.status_code != 200:
        logger.error(f"Error from the slack hook call: {response.status_code} {response.text}",
                     extra=hook_request)
