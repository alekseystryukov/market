from django.db import models
from django.utils.text import slugify
from uuid import uuid4


def category_file_name(instance, filename):
    ext = filename.split('.')[-1]
    return '/'.join(['core', 'categories', f"{uuid4().hex}.{ext}"])


class Category(models.Model):
    id = models.CharField(max_length=32, primary_key=True)
    parent = models.ForeignKey(
        'self', on_delete=models.CASCADE, related_name='sub_categories',
        null=True, blank=True
    )
    name = models.CharField(max_length=256)
    description = models.TextField(max_length=255, blank=True)
    image = models.ImageField(upload_to=category_file_name, blank=True)

    class Meta:
        verbose_name = 'category'
        verbose_name_plural = 'categories'
        get_latest_by = 'id'

    def __str__(self):
        return f"{self.id}: {self.name}"

    def save(self, *args, **kwargs):
        if not self.id:
            # category id is "{id_of_top_parent}{id_of_mid_parent}{id_of_direct_parent}{id_of_child}"
            # so it's easier to search by any lvl category with one index
            try:
                last_category = self.__class__.objects.filter(
                    parent_id=self.parent_id
                ).order_by("id").latest()
            except self.__class__.DoesNotExist:
                next_num = 1
            else:
                next_num = int(last_category.id[-4:]) + 1
            uid = f'{next_num:04}'
            if self.parent_id:
                uid = f"{self.parent_id}{uid}"
            self.id = uid
        super().save(*args, **kwargs)

    def slug(self):
        slug = slugify(self.name, allow_unicode=True)
        return f"{self.id}-{slug}"


class Attribute(models.Model):
    name = models.CharField(max_length=256, primary_key=True)

    def __str__(self):
        return self.name
