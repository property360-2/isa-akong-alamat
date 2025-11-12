from django.urls import path
from . import freshman_views

app_name = 'freshman'

urlpatterns = [
    path('', freshman_views.freshman_landing, name='landing'),
    path('create-credentials/', freshman_views.freshman_create_credentials, name='create_credentials'),
    path('select-course/', freshman_views.freshman_select_course, name='select_course'),
    path('confirm-credentials/', freshman_views.freshman_confirm_credentials, name='confirm_credentials'),
    path('complete/', freshman_views.freshman_enrollment_complete, name='enrollment_complete'),
]
