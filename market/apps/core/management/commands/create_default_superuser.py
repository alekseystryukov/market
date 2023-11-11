import logging
from django.contrib.auth import get_user_model
from django.core.management import BaseCommand

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument('--username', type=str, required=True)
        parser.add_argument('--email', type=str, required=True)
        parser.add_argument('--password', type=str, required=True)

    def handle(self, *args, **options):
        admin_username = options["username"]
        admin_email = options["email"]
        admin_password = options["password"]

        if get_user_model().objects.filter(username=admin_username).exists():
            logger.warning('Superuser exists already')
        else:
            get_user_model().objects.create_superuser(admin_username,
                                                      admin_email,
                                                      admin_password)
            logger.info('Superuser was created successfully')
