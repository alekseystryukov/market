import logging
import boto3
import json
import os

secrets_client = None


def get_secrets_client():
    global secrets_client
    if secrets_client is None:
        secrets_client = boto3.client('secretsmanager')
    return secrets_client


def unwrap_secret_to_env():
    for key in ("ENV_SECRET_NAME", "AWS_SECRET_NAME"):
        if key in os.environ:
            secret_name = os.environ[key]
            logging.info(f"Getting application environment from {secret_name}")
            response = get_secrets_client().get_secret_value(SecretId=secret_name)
            secrets = json.loads(response["SecretString"])
            for k, v in secrets.items():
                if k in os.environ:
                    logging.warning(f"'{k}' has already been defined in environment")
                os.environ[k] = str(v)
