from django.urls import path

from apps.core import views

app_name = 'core'

urlpatterns = [
    path('success-page/', views.SuccessPageView.as_view(), name='success_page'),
    path('error-page/', views.ErrorPageView.as_view(), name='error_page'),
]
