from django.urls import path

from . import views

urlpatterns = [
    path("uploads/", views.uploads, name="uploads"),
    path("download/<int:pk>/", views.download, name="download"),
]
