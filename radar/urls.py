from django.urls import path

from . import views

urlpatterns = [
    path("", views.dashboard, name="dashboard"),
    path("notices/<int:notice_id>/progress/", views.update_progress, name="update_progress"),
    path("update-now/", views.update_now, name="update_now"),
]
