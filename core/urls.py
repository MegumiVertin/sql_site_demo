# core/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path("", views.index, name="home"),
    path("api/run/", views.translate, name="run_legacy"),

    path("api/translate/", views.translate, name="translate"),
    path("api/progress/<uuid:job_id>/", views.progress, name="progress"),
]
