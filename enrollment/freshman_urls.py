from django.urls import path
from . import freshman_views

app_name = 'freshman'

urlpatterns = [
    path('', freshman_views.freshman_landing, name='landing'),
    path('register/', freshman_views.freshman_register, name='register'),
    path('select-program/', freshman_views.freshman_select_program, name='select_program'),
    path('review-account/', freshman_views.freshman_review_account, name='review_account'),
    path('enroll-subjects/', freshman_views.freshman_enroll_subjects, name='enroll_subjects'),
]
