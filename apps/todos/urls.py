from django.shortcuts import render
from django.urls import path

from ..todos import views

urlpatterns = [
    path("todos/", views.todos, name="todos"),
    path("page/<int:pk>/", views.page, name="page"),
    path("shared/<uuid:uuid>/", views.shared_page, name="shared_page"),
    path("wuerfel/", lambda r: render(r, "wuerfel.html")),
]
