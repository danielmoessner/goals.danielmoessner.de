from datetime import timedelta
from typing import TYPE_CHECKING, Optional

from django.core.exceptions import ObjectDoesNotExist
from django.db import models
from django.utils import timezone

from apps.users.models import CustomUser


class Todo(models.Model):
    name = models.CharField(max_length=300)
    user = models.ForeignKey(
        CustomUser, on_delete=models.CASCADE, related_name="to_dos"
    )
    activate = models.DateTimeField(null=True, blank=True)
    deadline = models.DateTimeField(null=True, blank=True)
    completed = models.DateTimeField(null=True, blank=True)
    status_choices = (("ACTIVE", "Active"), ("DONE", "Done"), ("FAILED", "Failed"))
    status = models.CharField(choices=status_choices, max_length=20, default="ACTIVE")
    created = models.DateTimeField(auto_created=True, null=True)
    updated = models.DateTimeField(auto_now=True, null=True)

    if TYPE_CHECKING:
        pipeline_to_dos: models.QuerySet["PipelineTodo"]

    class Meta:
        ordering = ("status", "-completed", "name", "deadline", "activate")

    @staticmethod
    def get_to_dos(to_dos, include_old_todos=False):
        if not include_old_todos:
            to_dos = to_dos.exclude(completed__lt=timezone.now() - timedelta(days=40))
        return to_dos

    @staticmethod
    def get_to_dos_user(user, to_do_class):
        all_to_dos = to_do_class.objects.filter(user=user)
        to_dos = Todo.get_to_dos(all_to_dos, include_old_todos=user.show_old_todos)
        return to_dos

    @property
    def completed_sort(self):
        if not self.completed:
            if self.deadline:
                return 10 * int(self.deadline.strftime("%Y%m%d"))
            if self.activate:
                return 10 * 88888888
            return 99999999
        return 100 * int(self.completed.strftime("%Y%m%d"))

    @property
    def is_done(self) -> bool:
        return self.status == "DONE"

    @property
    def type(self) -> str:
        return self.__class__.__name__

    @property
    def due_in(self) -> timedelta:
        if self.deadline is None:
            return timedelta(days=0)
        return self.deadline - timezone.now()

    @property
    def is_active(self) -> bool:
        return self.status == "ACTIVE"

    @property
    def is_overdue(self) -> bool:
        if not self.is_active:
            return False
        return self.due_in < timedelta(0)

    @property
    def due_in_str(self) -> str:
        if self.is_done:
            return ""

        if self.is_overdue:
            return "Overdue"

        days, seconds = self.due_in.days, self.due_in.seconds
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        seconds = seconds % 60

        parts = []
        if days > 0:
            parts.append(f"{days} Day{'s' if days > 1 else ''}")
        if hours > 0:
            parts.append(f"{hours} Hour{'s' if hours > 1 else ''}")
        if minutes > 0:
            parts.append(f"{minutes} Minute{'s' if minutes > 1 else ''}")

        if parts:
            return ", ".join(parts)

        if seconds:
            return "Now"

        return ""

    def save(
        self, force_insert=False, force_update=False, using=None, update_fields=None
    ):
        # set completed
        if self.completed is None and (
            self.status == "DONE" or self.status == "FAILED"
        ):
            self.completed = timezone.now()
        if self.status == "ACTIVE":
            self.completed = None
        # activate pipeline to dos
        if self.status == "DONE":
            self.pipeline_to_dos.filter(activate=None).update(activate=timezone.now())
        elif self.status == "FAILED":
            self.pipeline_to_dos.filter(activate=None).update(
                status="FAILED", activate=timezone.now()
            )
        # save
        super().save(
            force_insert=force_insert,
            force_update=force_update,
            using=using,
            update_fields=update_fields,
        )

    def __str__(self):
        return "{}: {} - {}".format(
            self.name,
            self.get_activate(accuracy="medium"),
            self.get_deadline(accuracy="medium"),
        )

    def get_deadline(self, accuracy="high"):
        if self.deadline:
            if accuracy == "medium":
                return (self.deadline).strftime("%d.%m.%Y")
            else:
                return (self.deadline).strftime("%d.%m.%Y %H:%M")
        return "none"

    def get_activate(self, accuracy="high"):
        if self.activate:
            if accuracy == "medium":
                return (self.activate).strftime("%d.%m.%Y")
            else:
                return (self.activate).strftime("%d.%m.%Y %H:%M")
        return "none"

    def complete(self):
        self.status = "DONE"
        self.completed = timezone.now()

    def reset(self):
        self.status = "ACTIVE"
        self.completed = None

    def toggle(self):
        if self.is_done:
            self.reset()
        else:
            self.complete()


class NormalTodo(Todo):
    pass


class RepetitiveTodo(Todo):
    duration = models.DurationField()
    previous = models.OneToOneField(
        "self", blank=True, null=True, on_delete=models.SET_NULL, related_name="next"  # type: ignore
    )
    blocked = models.BooleanField(default=False)

    if TYPE_CHECKING:
        next: "RepetitiveTodo"
        previous: Optional["RepetitiveTodo"]

    def __str__(self):
        return f"{self.name}"

    def complete(self):
        super().complete()
        if self.get_next() is None:
            self.generate_next()

    def reset(self):
        super().reset()
        if (n := self.get_next()) is not None:
            n.delete()

    def delete(self, using=None, keep_parents=False):
        next_rtd = self.get_next()
        if next_rtd and self.previous:
            next_rtd.previous = self.previous
            self.previous = None
            self.save()
            next_rtd.save()
        return super(RepetitiveTodo, self).delete(using, keep_parents)

    def get_next(self):
        try:
            next_rtd = self.next
        except ObjectDoesNotExist:
            next_rtd = None
        return next_rtd

    def get_all_after(self):
        repetitive_to_dos = [self]
        next_repetitive_to_do = self.get_next()
        if next_repetitive_to_do:
            repetitive_to_dos = (
                repetitive_to_dos + next_repetitive_to_do.get_all_after()
            )
        return repetitive_to_dos

    def get_all_before(self):
        q = RepetitiveTodo.objects.filter(pk=self.pk)
        if self.previous:
            q = q | self.previous.get_all_before()
        return q

    def generate_next(self):
        assert self.deadline is not None
        assert self.activate is not None
        next_activate = self.activate + self.duration
        next_deadline = self.deadline + self.duration
        RepetitiveTodo.objects.create(
            name=self.name,
            user=self.user,
            previous=self,
            deadline=next_deadline,
            activate=next_activate,
            repetitions=1,
            duration=self.duration,
        )


class NeverEndingTodo(Todo):
    duration = models.DurationField()
    previous = models.OneToOneField(
        "self", blank=True, null=True, on_delete=models.SET_NULL, related_name="next"
    )
    blocked = models.BooleanField(default=False)

    if TYPE_CHECKING:
        next: "NeverEndingTodo"

    def delete(self, *args, **kwargs):
        if self.previous is not None:
            self.previous.blocked = True
            self.previous.save()
        return super().delete(*args, **kwargs)

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        if (
            (self.status == "DONE" or self.status == "FAILED")
            and self.next_todo is None
            and self.blocked is False
        ):
            self.generate_next()

    # getters
    @property
    def next_todo(self):
        try:
            return self.next
        except ObjectDoesNotExist:
            return None

    @property
    def due_in_str(self):
        if not self.is_active:
            return ""
        days = self.duration.days
        seconds = self.duration.seconds
        return f"Reappears {days} days and {seconds} seconds after completion"

    # generate
    def generate_next(self):
        now = timezone.now()
        next_activate = now + self.duration
        NeverEndingTodo.objects.create(
            name=self.name,
            user=self.user,
            previous=self,
            activate=next_activate,
            duration=self.duration,
        )


class PipelineTodo(Todo):
    previous = models.ForeignKey(
        Todo, null=True, on_delete=models.SET_NULL, related_name="pipeline_to_dos"
    )


class NotesTodo(Todo):
    notes = models.TextField(null=True, blank=True)
    POSITION_TOP = "TOP"
    POSITION_BOTTOM = "BOTTOM"
    POSITION_CHOICES = ((POSITION_TOP, "Top"), (POSITION_BOTTOM, "Bottom"))
    position = models.CharField(choices=POSITION_CHOICES, max_length=20, default="TOP")
