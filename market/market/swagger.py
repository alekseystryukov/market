from django.conf import settings
from drf_yasg import openapi
from drf_yasg.generators import OpenAPISchemaGenerator
from drf_yasg.views import get_schema_view
from rest_framework import permissions


schema_view = get_schema_view(
    generator_class=OpenAPISchemaGenerator,
    info=openapi.Info(
        title="payment system API",
        default_version=f"{settings.PROJECT_VERSION} {settings.ENV_NAME}",
        terms_of_service="https://www.google.com/policies/terms/",
        license=openapi.License(name="BSD License"),
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
    authentication_classes=(),
)
