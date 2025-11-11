from django.urls import path
from . import views

app_name = 'academics'

urlpatterns = [
    # Main academics page (with tabs for programs, curricula, subjects)
    path('', views.academics_index, name='index'),

    # Programs
    path('programs/', views.programs_list, name='programs_list'),
    path('programs/create/', views.program_create, name='program_create'),
    path('programs/<int:pk>/update/', views.program_update, name='program_update'),
    path('programs/<int:pk>/delete/', views.program_delete, name='program_delete'),
    path('programs/<int:pk>/subjects/', views.program_subjects, name='program_subjects'),
    path('programs/<int:program_pk>/subjects/<int:subject_pk>/archive/', views.program_subject_archive, name='program_subject_archive'),
    path('programs/search/', views.program_search, name='program_search'),

    # Curricula
    path('curricula/', views.curricula_list, name='curricula_list'),
    path('curricula/create/', views.curriculum_create, name='curriculum_create'),
    path('curricula/<int:pk>/', views.curriculum_detail, name='curriculum_detail'),
    path('curricula/<int:pk>/update/', views.curriculum_update, name='curriculum_update'),
    path('curricula/<int:pk>/add-subjects/', views.curriculum_add_subjects, name='curriculum_add_subjects'),
    path('curricula/<int:pk>/duplicate/', views.curriculum_duplicate, name='curriculum_duplicate'),
    path('curricula/<int:pk>/toggle-active/', views.curriculum_toggle_active, name='curriculum_toggle_active'),

    # Subjects
    path('subjects/', views.subjects_list, name='subjects_list'),
    path('subjects/create/', views.subject_create, name='subject_create'),
    path('subjects/<int:pk>/update/', views.subject_update, name='subject_update'),
    path('subjects/<int:pk>/delete/', views.subject_delete, name='subject_delete'),
    path('subjects/search/', views.subject_search, name='subject_search'),

    # Prerequisites
    path('prerequisites/add/', views.prerequisite_add, name='prerequisite_add'),
    path('prerequisites/<int:pk>/delete/', views.prerequisite_delete, name='prerequisite_delete'),
]
