from django.conf import settings


def project_name(request):
    return {'project_name': 'Market'}


def project_settings(request):
    return {'settings': settings}
