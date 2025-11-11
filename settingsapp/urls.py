from django.urls import path
from . import views

app_name = 'settingsapp'

urlpatterns = [
    path('', views.settings_list, name='settings_list'),
    path('<int:pk>/update/', views.setting_update, name='setting_update'),
    path('toggle/<str:key>/', views.setting_toggle, name='setting_toggle'),
]
