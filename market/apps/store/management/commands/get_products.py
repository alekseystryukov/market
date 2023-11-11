from django.core.management import BaseCommand
from django.conf import settings
from apps.store.models import Product, Store, ProductImage, ProductAttribute
from apps.core.models import Category, Attribute
from datetime import datetime
from uuid import uuid4
import json
import boto3
import tempfile


s3_client = None


def get_s3_client():
    global s3_client
    if s3_client is None:
        s3_client = boto3.client('s3')
    return s3_client


categories_cash = {}
attributes_cash = {}


class Command(BaseCommand):

    def add_arguments(self, parser):
        parser.add_argument('--store_id', type=str, required=True)
        # /Market/DEV/media/2/2023-11-04/data.json
        parser.add_argument('--file_name', type=str, required=True)

    def handle(self, *args, **options):
        store_id = options["store_id"]
        store = Store.objects.get(pk=int(store_id))

        def product_file_name(filename, date):
            prefix = settings.AWS_STORAGE_BUCKET_PREFIX
            return f"{prefix}/media/{store.id}/{date}/{filename}"

        file_name = options["file_name"]
        date = file_name.split("/")[-2]

        with tempfile.TemporaryFile() as f:
            get_s3_client().download_fileobj(
                settings.AWS_STORAGE_BUCKET_NAME,
                file_name,
                f,
            )
            f.seek(0)
            # read lines and create objects
            line = f.readline()
            while line:
                data = json.loads(line)

                # get or create categories
                categories = data.get("categories", [])
                category_id = None
                for category in categories:
                    if category == "Каталог товарів":
                        continue
                    if category not in categories_cash:
                        cat_obj, _ = Category.objects.get_or_create(
                            parent_id=category_id,
                            name=category,
                        )
                        categories_cash[category] = cat_obj.id
                    category_id = categories_cash[category]  # latest will be assigned to product

                # create product
                product, _ = Product.objects.update_or_create(
                    id=data["id"].split("-")[0],
                    defaults=dict(
                        store=store,
                        name=data["name"],
                        description=data["description"],
                        price=data["price"],
                        image=product_file_name(data["images"][0], date),
                        category_id=category_id,
                    )
                )
                # add gallery images
                for image in data["images"]:
                    ProductImage.objects.update_or_create(
                        id=image.split("_")[0],
                        defaults=dict(
                            product=product,
                            file=product_file_name(image, date),
                        )
                    )

                # attributes
                attributes = data.get("attributes", {})
                for name, value in attributes.items():
                    if name not in attributes_cash:
                        att_obj, _ = Attribute.objects.get_or_create(name=name)
                        attributes_cash[name] = att_obj
                    attribute = attributes_cash[name]
                    ProductAttribute.objects.update_or_create(
                        product=product,
                        attribute=attribute,
                        defaults=dict(
                            value=value,
                        )
                    )

                line = f.readline()
