"""
URL configuration for scheduler_ui app.
"""
from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('groups/', views.groups, name='groups'),
    path('generate/', views.generate, name='generate'),
]
