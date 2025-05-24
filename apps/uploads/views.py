from django.contrib.auth.decorators import login_required
from django.http import FileResponse, HttpRequest
from django.shortcuts import render

from apps.uploads.models import Upload


@login_required
def uploads(request: HttpRequest):
    context = {"uploads": Upload.objects.filter(user=request.user)}
    return render(request, "uploads.html", context)


@login_required
def download(request: HttpRequest, pk: int):
    upload = Upload.objects.get(pk=pk, user=request.user)
    return FileResponse(upload.file.open(), filename=upload.title, as_attachment=False)
