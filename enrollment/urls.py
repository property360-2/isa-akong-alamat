from django.urls import path
from . import views

app_name = 'enrollment'

urlpatterns = [
    # Terms
    path('terms/', views.terms_list, name='terms_list'),
    path('terms/archived/', views.archived_terms_list, name='archived_terms_list'),
    path('terms/create/', views.term_create, name='term_create'),
    path('terms/<int:pk>/update/', views.term_update, name='term_update'),
    path('terms/<int:pk>/activate/', views.term_activate, name='term_activate'),
    path('terms/<int:pk>/close/', views.term_close, name='term_close'),
    path('terms/<int:pk>/delete/', views.term_delete, name='term_delete'),
    path('terms/<int:pk>/archive/', views.term_archive, name='term_archive'),
    path('terms/<int:pk>/unarchive/', views.term_unarchive, name='term_unarchive'),

    # Sections
    path('sections/', views.sections_list, name='sections_list'),
    path('sections/create/', views.section_create, name='section_create'),
    path('sections/<int:pk>/update/', views.section_update, name='section_update'),
    path('sections/<int:pk>/delete/', views.section_delete, name='section_delete'),
    path('sections/<int:pk>/change-status/', views.section_change_status, name='section_change_status'),
    path('sections/bulk-create/', views.sections_bulk_create, name='sections_bulk_create'),

    # AJAX endpoints
    path('professors/search/', views.professor_search, name='professor_search'),

    # Admissions (placeholder)
    path('admissions/', views.admissions_list, name='admissions_list'),
]
