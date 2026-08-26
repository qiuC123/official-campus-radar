from django.urls import path

from . import views

urlpatterns = [
    path("", views.dashboard, name="dashboard"),
    path("history/", views.history, name="history"),
    path("preview/phase-02/", views.phase02_preview, name="phase02_preview"),
    path("batches/<int:batch_id>/positions/", views.batch_positions, name="batch_positions"),
    path("positions/<int:position_id>/progress/", views.update_progress, name="update_progress"),
    path("update-now/", views.update_now, name="update_now"),
]
