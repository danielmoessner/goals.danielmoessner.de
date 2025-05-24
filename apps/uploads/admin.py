from django.contrib import admin

from apps.uploads.models import FileUpload, Upload

admin.site.register(Upload)
admin.register(FileUpload)
