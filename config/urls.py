from django.conf import settings
from django.conf.urls import include
from django.conf.urls.static import static
from django.contrib import admin
from django.shortcuts import redirect
from django.urls import path

from .filebrowser import site
from config.form import form_view, global_form_view

urlpatterns = [
    path("", lambda r: redirect("/todos/todos/")),
    path("filebrowser/", site.urls),
    path("tinymce/", include("tinymce.urls")),
    path("admin/", admin.site.urls),
    path("todos/", include("apps.todos.urls")),
    path("achievements/", include("apps.achievements.urls")),
    path("notes/", include("apps.notes.urls")),
    path("story/", include("apps.story.urls")),
    path("users/", include("apps.users.urls")),
    path("goals/", include("apps.goals.urls")),
    path("uploads/", include("apps.uploads.urls")),
    path("form/<str:form_name>/", form_view, name="form"),
    path("global-form/<str:form_name>/", global_form_view, name="global_form"),
]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    import debug_toolbar

    urlpatterns += [
        path("__debug__/", include(debug_toolbar.urls)),
    ]
