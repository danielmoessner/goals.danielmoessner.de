from typing import TYPE_CHECKING

from django.db import models

from apps.users.models import CustomUser


class Upload(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    title = models.CharField(max_length=100)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    if TYPE_CHECKING:
        files: models.QuerySet["FileUpload"]

    class Meta:
        verbose_name = "Upload"
        verbose_name_plural = "Uploads"
        ordering = ["-updated"]

    def __str__(self):
        return self.title

    @property
    def file(self) -> "models.FieldFile":
        f = self.files.first()
        assert f is not None, "Upload must have at least one file."
        return f.file

    def create_file(self, file) -> "FileUpload":
        file_upload = FileUpload(upload=self, file=file)
        file_upload.save()
        return file_upload

    def delete(self, *args, **kwargs):
        for file_upload in self.files.all():
            file_upload.file.delete(save=False)
        return super().delete(*args, **kwargs)


class FileUpload(models.Model):
    upload = models.ForeignKey(Upload, on_delete=models.CASCADE, related_name="files")
    file = models.FileField(upload_to="files/")
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "File Upload"
        verbose_name_plural = "File Uploads"
        ordering = ["-uploaded_at"]

    def __str__(self):
        return self.file.name
