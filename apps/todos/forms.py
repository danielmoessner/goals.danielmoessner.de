from typing import Any, TypeVar

from django import forms
from django.contrib.auth.models import AbstractBaseUser, AnonymousUser
from django.db import models
from django.utils import timezone

from apps.todos.models import (
    NeverEndingTodo,
    NormalTodo,
    NotesTodo,
    PipelineTodo,
    RepetitiveTodo,
    Todo,
)
from apps.todos.utils import (
    add_week,
    get_datetime_widget,
    get_end_of_week,
    get_specific_todo,
    get_start_of_week,
    setup_datetime_field,
    setup_duration_field,
)
from apps.users.models import CustomUser
from config.mixins import OptsUserInstance

USER = AbstractBaseUser | AnonymousUser | CustomUser
OPTS = dict[str, Any]
T = TypeVar("T", bound=models.Model)


class CreateTodoFast(OptsUserInstance[Todo], forms.ModelForm):
    class Meta:
        model = NormalTodo
        fields = ["name"]

    def ok(self):
        self.instance.user = self.user
        self.instance.activate = timezone.now()
        self.instance.save()
        return self.instance.pk


class CreateNormalTodo(OptsUserInstance[NormalTodo], forms.ModelForm):
    navs = ["todos", "create"]

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


class CreateNeverEndingTodo(OptsUserInstance[NeverEndingTodo], forms.ModelForm):
    navs = ["todos", "create"]
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


class CreateRepetitiveTodo(OptsUserInstance[RepetitiveTodo], forms.ModelForm):
    navs = ["todos", "create"]
    submit = "Create"

    class Meta:
        model = RepetitiveTodo
        fields = ["name", "duration", "repetitions"]

    def init(self):
        setup_duration_field(self.fields["duration"])

    def ok(self):
        self.instance.user = self.user
        self.instance.activate = timezone.now()
        self.instance.deadline = timezone.now() + self.cleaned_data["duration"]
        self.instance.save()
        return self.instance.pk


class CreatePipelineTodo(OptsUserInstance[PipelineTodo], forms.ModelForm):
    navs = ["todos", "create"]
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


class UpdateRepetitiveTodo(OptsUserInstance[RepetitiveTodo], forms.ModelForm):
    navs = ["todos"]

    class Meta:
        model = RepetitiveTodo
        fields = ["name", "status", "activate", "deadline", "repetitions"]

    def get_instance(self):
        return RepetitiveTodo.objects.get(pk=self.opts["pk"], user=self.user)

    def init(self):
        setup_datetime_field(self.fields["activate"])
        setup_datetime_field(self.fields["deadline"])

    def ok(self) -> int:
        self.instance.save()
        return self.instance.pk


class UpdateNormalTodo(OptsUserInstance[NormalTodo], forms.ModelForm):
    navs = ["todos"]

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


class UpdateNeverEndingTodo(OptsUserInstance[NeverEndingTodo], forms.ModelForm):
    navs = ["todos"]

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


class CreateNotesTodo(OptsUserInstance[NotesTodo], forms.ModelForm):
    navs = ["todos", "create"]

    class Meta:
        model = NotesTodo
        fields = ["position", "name", "notes"]

    def ok(self):
        self.instance.user = self.user
        self.instance.activate = timezone.now()
        self.instance.save()
        return self.instance.pk


class UpdateNotesTodo(OptsUserInstance[NotesTodo], forms.ModelForm):
    navs = ["todos"]

    class Meta:
        model = NotesTodo
        fields = ["position", "name", "notes"]

    def get_instance(self):
        return NotesTodo.objects.get(pk=self.opts["pk"], user=self.user)

    def ok(self) -> int:
        self.instance.save()
        return self.instance.pk


class DeleteTodo(OptsUserInstance[NormalTodo], forms.ModelForm):
    navs = ["todos"]
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


class ToggleTodo(OptsUserInstance[Todo], forms.ModelForm):
    class Meta:
        model = Todo
        fields = []

    def get_instance(self):
        return get_specific_todo(pk=self.opts["pk"], user=self.user)

    def ok(self) -> int:
        self.instance.toggle()
        self.instance.save()
        return self.instance.pk


class UpdateTodoSettings(OptsUserInstance[CustomUser], forms.ModelForm):
    navs = ["settings"]
    submit = "Save"

    class Meta:
        model = CustomUser
        fields = ["show_old_todos"]

    def get_instance(self):
        return self.user

    def ok(self):
        self.instance.save()
        return self.instance.pk
