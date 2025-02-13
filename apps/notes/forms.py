from django import forms
from tinymce.widgets import TinyMCE

from apps.notes.models import Note
from config.mixins import OptsUserInstance


class CreateNote(OptsUserInstance[Note], forms.ModelForm):
    navs = ["notes"]
    submit = "Create"
    stay_on_page = True

    class Meta:
        model = Note
        fields = ["content"]

    def ok(self):
        self.instance.user = self.user
        self.instance.save()
        return self.instance.pk


class UpdateNote(OptsUserInstance[Note], forms.ModelForm):
    navs = ["notes"]
    stay_on_page = True

    class Meta:
        model = Note
        fields = CreateNote.Meta.fields

    def get_instance(self):
        return Note.objects.get(pk=self.opts["pk"], user=self.user)

    def ok(self):
        self.instance.save()
        return self.instance.pk


class DeleteNote(OptsUserInstance[Note], forms.ModelForm):
    navs = ["notes"]
    text = "Are you sure you want to delete this note?"
    submit = "Delete"

    class Meta:
        model = Note
        fields = []
        widgets = {"content": TinyMCE(attrs={"cols": 80, "rows": 30})}

    def get_instance(self):
        return Note.objects.get(pk=self.opts["pk"], user=self.user)

    def ok(self):
        self.instance.delete()
        return self.instance.pk
