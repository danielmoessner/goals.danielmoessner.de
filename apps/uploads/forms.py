from django import forms

from apps.uploads.models import Upload
from config.form_class import FormClass
from config.mixins import OptsUserInstance


class CreateUpload(FormClass, OptsUserInstance[Upload], forms.ModelForm):
    file = forms.FileField(label="File")
    addons = {"navs": ["uploads"]}
    submit = "Create"

    class Meta:
        model = Upload
        fields = ["title", "file"]

    def ok(self):
        self.instance.user = self.user
        file = self.cleaned_data["file"]
        self.instance.save()
        self.instance.create_file(file)
        return self.instance.pk


class UploadFile(FormClass, OptsUserInstance[Upload], forms.ModelForm):
    file = forms.FileField(
        label="File",
    )
    addons = {"navs": ["uploads"]}

    class Meta:
        model = Upload
        fields = CreateUpload.Meta.fields

    def get_instance(self):
        return Upload.objects.get(pk=self.opts["pk"], user=self.user)

    def ok(self):
        file = self.cleaned_data["file"]
        self.instance.save()
        self.instance.create_file(file)
        return self.instance.pk


class DeleteUpload(FormClass, OptsUserInstance[Upload], forms.ModelForm):
    addons = {"navs": ["uploads"]}
    text = "Are you sure you want to delete this file?"
    submit = "Delete"

    class Meta:
        model = Upload
        fields = []

    def get_instance(self):
        return Upload.objects.get(pk=self.opts["pk"], user=self.user)

    def ok(self):
        self.instance.delete()
        return self.instance.pk
