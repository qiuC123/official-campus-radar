from django.urls import path

from . import views

urlpatterns = [
    path("", views.dashboard, name="dashboard"),
    path("history/", views.history, name="history"),
    path("applications/", views.application_progress_list, name="application_progress_list"),
    path("preview/phase-02/", views.phase02_preview, name="phase02_preview"),
    path("batches/<int:batch_id>/positions/", views.batch_positions, name="batch_positions"),
    path("batches/<int:batch_id>/progress/", views.update_progress, name="update_progress"),
]
