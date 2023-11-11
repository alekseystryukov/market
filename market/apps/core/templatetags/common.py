from django import template

register = template.Library()


@register.filter
def get_item(dictionary, key):
    return dictionary.get(key)


@register.filter
def get_model_field(instance: 'models.Model', field_name: str):  # noqa: F821
    return instance._meta.get_field(field_name)


@register.filter
def get_display_or_value(instance: 'models.Model', field_name: str):  # noqa: F821
    if instance._meta.get_field(field_name).choices:
        return getattr(instance, f'get_{field_name}_display')()

    return getattr(instance, field_name)
