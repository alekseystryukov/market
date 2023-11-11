import logging
from django.contrib import admin
from django.conf import settings
from .models import Category


admin.site.site_header = f'Market {settings.PROJECT_VERSION}'
admin.site.site_title = 'Market'
admin.site.index_title = 'Administration'


logger = logging.getLogger(__name__)


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "parent")
    readonly_fields = ("id", "parent")
