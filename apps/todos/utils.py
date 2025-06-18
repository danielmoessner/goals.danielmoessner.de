from datetime import datetime, timedelta

from django import forms
from django.core.exceptions import ObjectDoesNotExist

from apps.todos.models import (
    NeverEndingTodo,
    NormalTodo,
    NotesTodo,
    PipelineTodo,
    RepetitiveTodo,
)


def get_end_of_week():
    now = datetime.now()
    week_start = now - timedelta(days=now.weekday())
    end_of_week = (week_start + timedelta(days=6)).replace(
        hour=23, minute=59, second=59, microsecond=0
    )
    return end_of_week


def get_start_of_week():
    now = datetime.now()
    week_start = now - timedelta(days=now.weekday())
    week_start_with_time = (week_start).replace(
        hour=0, minute=0, second=0, microsecond=0
    )
    return week_start_with_time


def get_start_of_next_week():
    start = get_start_of_week()
    return start + timedelta(days=7)


def get_end_of_next_week():
    end = get_end_of_week()
    return end + timedelta(days=7)


def add_week(dt: datetime) -> datetime:
    return dt + timedelta(weeks=1)


def get_datetime_widget():
    return forms.DateTimeInput(
        attrs={"type": "datetime-local"}, format="%Y-%m-%dT%H:%M"
    )


def get_date_widget():
    return forms.DateInput(attrs={"type": "date"}, format="%Y-%m-%d")


def get_specific_todo(pk: int | str, **kwargs):
    for cls in [NormalTodo, NeverEndingTodo, RepetitiveTodo, PipelineTodo, NotesTodo]:
        try:
            return cls.objects.get(pk=pk, **kwargs)
        except ObjectDoesNotExist:
            pass
    raise ObjectDoesNotExist()


def setup_duration_field(field: forms.Field):
    field.help_text = "Ex.: 7 9:30:10 for 7 days, 9 hours, 30 minutes and 10 seconds"
    field.initial = "0 00:00:00"


def setup_datetime_field(field: forms.Field):
    field.widget = get_datetime_widget()


def setup_date_field(field: forms.Field):
    field.widget = get_date_widget()
