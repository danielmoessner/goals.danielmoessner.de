from django import forms
from django.db import transaction
from django.db.models.base import Model as Model

from apps.goals.models import Goal, ProgressMonitor
from apps.todos.utils import setup_datetime_field
from apps.users.models import CustomUser
from config.fields import CustomModelMultipleChoiceField
from config.form_class import FormClass
from config.mixins import OptsUserInstance


class CreateGoal(FormClass, OptsUserInstance[Goal], forms.ModelForm):
    addons = {"navs": ["goals"]}
    parent = forms.ModelChoiceField(queryset=Goal.objects.none(), required=False)
    field_order = ["parent", "name"]

    class Meta:
        fields = ["name", "why", "impact", "deadline"]
        model = Goal

    def init(self):
        setup_datetime_field(self.fields["deadline"])
        self.fields["parent"].queryset = Goal.objects.filter(user=self.user)  # type: ignore

    def ok(self):
        self.instance.user = self.user
        parent: Goal | None = self.cleaned_data["parent"]
        with transaction.atomic():
            self.instance.save()
            if parent:
                parent.sub_goals.add(self.instance)
        return self.instance.pk


class UpdateGoal(FormClass, OptsUserInstance[Goal], forms.ModelForm):
    addons = {"navs": ["goals"]}
    parents = CustomModelMultipleChoiceField(
        queryset=Goal.objects.none(), required=False
    )
    field_order = ["parents"] + CreateGoal.field_order  # type: ignore

    class Meta:
        fields = CreateGoal.Meta.fields + ["is_archived", "is_starred"]
        model = Goal

    def get_instance(self) -> Goal:
        return Goal.objects.get(user=self.user, pk=self.opts["pk"])

    def init(self):
        setup_datetime_field(self.fields["deadline"])
        self.fields["parents"].queryset = Goal.objects.filter(user=self.user)  # type: ignore
        self.fields["parents"].initial = self.instance.master_goals.all()

    def clean_parents(self):
        v = self.cleaned_data["parents"]
        for g1 in v:
            for g2 in self.instance.get_all_sub_goals():
                if g2 == g1:
                    raise forms.ValidationError(
                        f"Recursive relationship between '{self.instance.name}' and '{g2.name}'."
                    )
            if g1 == self.instance:
                raise forms.ValidationError("Goal can not have itself as parent.")
        return v

    def ok(self):
        parents: list[Goal] = self.cleaned_data["parents"]
        with transaction.atomic():
            self.instance.save()
            for g in self.instance.master_goals.all():
                g.sub_goals.remove(self.instance)
            for p in parents:
                p.sub_goals.add(self.instance)
        return self.instance.pk


class DeleteGoal(FormClass, OptsUserInstance[Goal], forms.ModelForm):
    addons = {"navs": ["goals"]}
    text = "Are you sure you want to delete this goal?"
    submit = "Delete"

    class Meta:
        model = Goal
        fields = []

    def get_instance(self) -> Goal:
        return Goal.objects.get(user=self.user, pk=self.opts["pk"])

    def ok(self):
        self.instance.delete()
        return self.instance.pk


class AddMonitor(FormClass, OptsUserInstance[ProgressMonitor], forms.ModelForm):
    addons = {"navs": ["goals"]}
    submit = "Add"

    class Meta:
        model = ProgressMonitor
        fields = ["goal", "name", "weight", "steps"]

    def init(self):
        self.fields["goal"].initial = Goal.objects.filter(user=self.user).get(
            pk=self.opts["goal_pk"]
        )
        self.fields["steps"].initial = 1

    def ok(self):
        self.instance.save()
        return self.instance.pk


def get_monitor(user: CustomUser, pk: int) -> ProgressMonitor:
    return ProgressMonitor.objects.get(goal__user=user, pk=pk)


class IncreaseProgress(FormClass, OptsUserInstance[ProgressMonitor], forms.ModelForm):
    addons = {"navs": ["goals"]}
    submit = "Increase"

    class Meta:
        model = ProgressMonitor
        fields = []

    def get_instance(self) -> ProgressMonitor:
        return get_monitor(self.user, self.opts["pk"])

    def ok(self):
        self.instance.increase_progress()
        self.instance.save()
        return self.instance.pk


class DecreaseProgress(FormClass, OptsUserInstance[ProgressMonitor], forms.ModelForm):
    addons = {"navs": ["goals"]}
    submit = "Decrease"

    class Meta:
        model = ProgressMonitor
        fields = []

    def get_instance(self) -> ProgressMonitor:
        return get_monitor(self.user, self.opts["pk"])

    def ok(self):
        self.instance.decrease_progress()
        self.instance.save()
        return self.instance.pk


class UpdateMonitor(FormClass, OptsUserInstance[ProgressMonitor], forms.ModelForm):
    addons = {"navs": ["goals"]}
    submit = "Save"

    class Meta:
        model = ProgressMonitor
        fields = ["name", "weight", "steps"]

    def get_instance(self) -> ProgressMonitor:
        return get_monitor(self.user, self.opts["pk"])

    def ok(self):
        self.instance.save()
        return self.instance.pk


class DeleteMonitor(FormClass, OptsUserInstance[ProgressMonitor], forms.ModelForm):
    addons = {"navs": ["goals"]}
    submit = "Delete"
    text = "Are you sure you want to delete this monitor?"

    class Meta:
        model = ProgressMonitor
        fields = []

    def get_instance(self) -> ProgressMonitor:
        return get_monitor(self.user, self.opts["pk"])

    def ok(self):
        self.instance.delete()
        return self.instance.pk


class UpdateGoalSettings(FormClass, OptsUserInstance[CustomUser], forms.ModelForm):
    addons = {"navs": ["settings"]}
    submit = "Save"

    class Meta:
        model = CustomUser
        fields = ["show_archived_objects"]

    def get_instance(self):
        return self.user

    def ok(self):
        self.instance.save()
        return self.instance.pk
