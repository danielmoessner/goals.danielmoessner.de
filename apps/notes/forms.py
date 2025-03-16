from django import forms
from tinymce.widgets import TinyMCE

from apps.notes.models import Note
from config.form_class import FormClass
from config.mixins import OptsUserInstance


class CreateNote(FormClass, OptsUserInstance[Note], forms.ModelForm):
    addons = {
        "navs": ["notes"],
        "stay_on_page": {"submit": "Create & Keep Editing"},
    }
    submit = "Create"

    class Meta:
        model = Note
        fields = ["content"]

    def ok(self):
        self.instance.user = self.user
        self.instance.save()
        return self.instance.pk


class UpdateNote(FormClass, OptsUserInstance[Note], forms.ModelForm):
    addons = {
        "navs": ["notes"],
        "stay_on_page": {"submit": "Save & Keep Editing"},
    }

    class Meta:
        model = Note
        fields = CreateNote.Meta.fields

    def get_instance(self):
        return Note.objects.get(pk=self.opts["pk"], user=self.user)

    def ok(self):
        self.instance.save()
        return self.instance.pk


class DeleteNote(FormClass, OptsUserInstance[Note], forms.ModelForm):
    addons = {"navs": ["notes"]}
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
