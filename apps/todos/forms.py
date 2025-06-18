from typing import Any, TypeVar

from django import forms
from django.contrib.auth.models import AbstractBaseUser, AnonymousUser
from django.db import models
from django.utils import timezone

from apps.todos.models import (
    NeverEndingTodo,
    NormalTodo,
    NotesTodo,
    Page,
    PipelineTodo,
    RepetitiveTodo,
    Todo,
)
from apps.todos.utils import (
    add_week,
    get_datetime_widget,
    get_end_of_week,
    get_specific_todo,
    get_start_of_next_week,
    get_start_of_week,
    setup_datetime_field,
    setup_duration_field,
)
from apps.users.models import CustomUser
from config.form_class import FormClass
from config.mixins import OptsAnonymousUserInstance, OptsUserInstance

USER = AbstractBaseUser | AnonymousUser | CustomUser
OPTS = dict[str, Any]
T = TypeVar("T", bound=models.Model)


class CreatePage(FormClass, OptsUserInstance[Page], forms.ModelForm):
    addons = {"navs": ["todos"]}

    class Meta:
        model = Page
        fields = ["name"]

    def ok(self):
        self.instance.user = self.user
        self.instance.save()
        return self.instance.pk


class UpdatePage(FormClass, OptsUserInstance[Page], forms.ModelForm):
    addons = {"navs": ["todos"]}

    class Meta:
        model = Page
        fields = ["name"]

    def get_instance(self):
        return Page.objects.get(pk=self.opts["pk"], user=self.user)

    def ok(self) -> int:
        self.instance.save()
        return self.instance.pk


class SharePage(FormClass, OptsUserInstance[Page], forms.ModelForm):
    addons = {"navs": ["todos"]}

    class Meta:
        model = Page
        fields = []

    @property
    def text(self) -> str:
        instance = self.get_instance()
        if instance.is_shared:
            return "Do you want to stop sharing this page?"
        return "Do you want to share this page with everybody who has the link?"

    @property
    def submit(self) -> str:
        instance = self.get_instance()
        if instance.is_shared:
            return "Stop sharing"
        return "Share"

    def get_instance(self):
        if not hasattr(self, "instance"):
            self.instance = Page.objects.get(pk=self.opts["pk"], user=self.user)
        return self.instance

    def ok(self) -> int:
        if self.instance.is_shared:
            self.instance.unshare()
        else:
            self.instance.share()
        self.instance.save()
        return self.instance.pk


class DeletePage(FormClass, OptsUserInstance[Page], forms.ModelForm):
    # addons = {"navs": ["todos"]}
    text = "Are you sure you want to delete this page?"
    submit = "Delete"

    class Meta:
        model = Page
        fields = []

    def get_instance(self):
        return Page.objects.get(pk=self.opts["pk"], user=self.user)

    def ok(self) -> int:
        self.instance.delete()
        return 0


class CreateTodoFast(FormClass, OptsUserInstance[Todo], forms.ModelForm):

    class Meta:
        model = NormalTodo
        fields = ["name", "page"]

    def ok(self):
        if self.opts.get("kind", "") == "next_week":
            activate = get_start_of_next_week()
        else:
            activate = timezone.now()
        self.instance.user = self.user
        self.instance.activate = activate
        self.instance.save()
        return self.instance.pk


class CreateNormalTodo(FormClass, OptsUserInstance[NormalTodo], forms.ModelForm):
    addons = {"navs": ["todos", "create"]}

    class Meta:
        model = NormalTodo
        fields = ["name", "activate", "deadline"]

    def init(self):
        self.fields["activate"].widget = get_datetime_widget()
        self.fields["deadline"].widget = get_datetime_widget()
        variant = self.opts.get("variant", "this_week")
        if variant == "this_week":
            self.fields["activate"].initial = get_start_of_week()
            self.fields["deadline"].initial = get_end_of_week()
        elif variant == "next_week":
            self.fields["activate"].initial = add_week(get_start_of_week())
            self.fields["deadline"].initial = add_week(get_end_of_week())

    def ok(self):
        self.instance.user = self.user
        self.instance.save()
        return self.instance.pk


class CreateNeverEndingTodo(
    FormClass, OptsUserInstance[NeverEndingTodo], forms.ModelForm
):
    addons = {"navs": ["todos", "create"]}
    text = "A never ending todo will reappear after the completion date + the duration time."
    submit = "Create"

    class Meta:
        model = NeverEndingTodo
        fields = ["name", "duration"]

    def init(self):
        setup_duration_field(self.fields["duration"])

    def ok(self):
        self.instance.user = self.user
        self.instance.activate = timezone.now()
        self.instance.save()
        return self.instance.pk


class CreateRepetitiveTodo(
    FormClass, OptsUserInstance[RepetitiveTodo], forms.ModelForm
):
    addons = {"navs": ["todos", "create"]}
    submit = "Create"

    class Meta:
        model = RepetitiveTodo
        fields = ["name", "activate", "deadline", "duration"]

    def init(self):
        setup_duration_field(self.fields["duration"])
        setup_datetime_field(self.fields["activate"])
        setup_datetime_field(self.fields["deadline"])

    def ok(self):
        self.instance.user = self.user
        self.instance.save()
        return self.instance.pk


class CreatePipelineTodo(FormClass, OptsUserInstance[PipelineTodo], forms.ModelForm):
    addons = {"navs": ["todos", "create"]}
    submit = "Create"
    text = "A pipeline todo activates once its previous todo completes"

    class Meta:
        model = PipelineTodo
        fields = ["name", "previous"]

    def init(self):
        qs = Todo.objects.filter(status="ACTIVE", user=self.user).order_by("name")
        self.fields["previous"].queryset = qs  # type: ignore

    def ok(self) -> int:
        self.instance.user = self.user
        self.instance.save()
        return self.instance.pk


class UpdateRepetitiveTodo(
    FormClass, OptsUserInstance[RepetitiveTodo], forms.ModelForm
):
    addons = {"navs": ["todos"]}

    class Meta:
        model = RepetitiveTodo
        fields = ["name", "status", "activate", "deadline", "duration"]

    def get_instance(self):
        return RepetitiveTodo.objects.get(pk=self.opts["pk"], user=self.user)

    def init(self):
        setup_datetime_field(self.fields["activate"])
        setup_datetime_field(self.fields["deadline"])

    def ok(self) -> int:
        self.instance.save()
        return self.instance.pk


class UpdateNormalTodo(FormClass, OptsUserInstance[NormalTodo], forms.ModelForm):
    addons = {"navs": ["todos"]}

    class Meta:
        model = NormalTodo
        fields = ["name", "status", "activate", "deadline"]

    def get_instance(self):
        return NormalTodo.objects.get(pk=self.opts["pk"], user=self.user)

    def init(self):
        setup_datetime_field(self.fields["activate"])
        setup_datetime_field(self.fields["deadline"])

    def ok(self) -> int:
        self.instance.save()
        return self.instance.pk


class UpdateNeverEndingTodo(
    FormClass, OptsUserInstance[NeverEndingTodo], forms.ModelForm
):
    addons = {"navs": ["todos"]}

    class Meta:
        model = NeverEndingTodo
        fields = ["name", "status", "activate", "duration"]

    def get_instance(self):
        return NeverEndingTodo.objects.get(pk=self.opts["pk"], user=self.user)

    def init(self):
        setup_datetime_field(self.fields["activate"])

    def ok(self) -> int:
        self.instance.save()
        return self.instance.pk


class CreateNotesTodo(FormClass, OptsUserInstance[NotesTodo], forms.ModelForm):
    addons = {"navs": ["todos", "create"]}

    class Meta:
        model = NotesTodo
        fields = ["position", "name", "notes"]

    def ok(self):
        self.instance.user = self.user
        self.instance.activate = timezone.now()
        self.instance.save()
        return self.instance.pk


class UpdateNotesTodo(FormClass, OptsUserInstance[NotesTodo], forms.ModelForm):
    addons = {"navs": ["todos"]}

    class Meta:
        model = NotesTodo
        fields = ["position", "name", "notes"]

    def get_instance(self):
        return NotesTodo.objects.get(pk=self.opts["pk"], user=self.user)

    def ok(self) -> int:
        self.instance.save()
        return self.instance.pk


class DeleteTodo(FormClass, OptsUserInstance[NormalTodo], forms.ModelForm):
    addons = {"navs": ["todos"]}
    text = "Are you sure you want to delete this todo?"
    submit = "Delete"

    class Meta:
        model = Todo
        fields = []

    def get_instance(self):
        return get_specific_todo(pk=self.opts["pk"], user=self.user)

    def ok(self) -> int:
        self.instance.delete()
        return 0


class ToggleTodo(FormClass, OptsAnonymousUserInstance[Todo], forms.ModelForm):
    page_uuid = forms.UUIDField(required=False, widget=forms.HiddenInput)

    class Meta:
        model = Todo
        fields = ["page_uuid"]

    def get_instance(self):
        if isinstance(self.user, CustomUser):
            return get_specific_todo(pk=self.opts["pk"], user=self.user)
        return get_specific_todo(
            pk=self.opts["pk"], page__share_uuid=self.opts["page_uuid"]
        )

    def ok(self) -> int:
        self.instance.toggle()
        self.instance.save()
        return self.instance.pk


class UpdateTodoSettings(FormClass, OptsUserInstance[CustomUser], forms.ModelForm):
    addons = {"navs": ["settings"]}
    submit = "Save"

    class Meta:
        model = CustomUser
        fields = ["show_old_todos"]

    def get_instance(self):
        return self.user

    def ok(self):
        self.instance.save()
        return self.instance.pk
