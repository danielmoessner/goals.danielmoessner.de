from datetime import datetime, timedelta
from typing import TYPE_CHECKING, Optional, TypedDict
from uuid import uuid4

from asgiref.sync import sync_to_async
from django.core.exceptions import ObjectDoesNotExist
from django.db import models
from django.urls import reverse
from django.utils import timezone

from apps.users.models import CustomUser
from config.bot import get_bot


class Message(TypedDict):
    text: str
    datetime: datetime


class Page(models.Model):
    name = models.CharField(max_length=300)
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name="pages")
    created = models.DateTimeField(auto_created=True, null=True)
    updated = models.DateTimeField(auto_now=True, null=True)
    is_shared = models.BooleanField(default=False)
    share_uuid = models.UUIDField(null=True, blank=True, unique=True, editable=False)

    telegram_chat_id = models.CharField(max_length=100, null=True, blank=True)
    telegram_user_tag = models.CharField(max_length=100, null=True, blank=True)

    messages = models.JSONField(default=list, blank=True)

    if TYPE_CHECKING:
        todos: models.QuerySet["Todo"]

    class Meta:
        ordering = ("name",)

    def __str__(self):
        return self.name

    @property
    def link(self):
        if self.is_shared and self.share_uuid:
            return reverse("shared_page", kwargs={"uuid": self.share_uuid})
        return ""

    @property
    def last_message(self) -> Optional[Message]:
        if not self.messages:
            return None
        msg: dict = self.messages[-1]
        return Message(
            text=msg.get("text", ""),
            datetime=datetime.fromisoformat(msg.get("datetime", "1970-01-01T00:00:00")),
        )

    def can_send_updates(self) -> bool:
        return self.is_shared and self.telegram_chat_id is not None

    def share(self):
        self.is_shared = True
        self.share_uuid = uuid4()

    def unshare(self):
        self.is_shared = False
        self.share_uuid = None

    async def send_message(self, text: str):
        bot = get_bot()
        assert self.telegram_chat_id is not None
        await bot.send_message(chat_id=self.telegram_chat_id, text=text)

    def should_send_new_message(self) -> bool:
        last_msg = self.last_message
        if not last_msg:
            return True
        if last_msg["datetime"] + timedelta(hours=2) > timezone.now():
            return False
        if timezone.now().hour == 8:
            return True
        return False

    def _get_todo_names(self) -> tuple[int, str]:
        todos = self.todos.filter(status="ACTIVE")
        if not todos:
            return 0, "No active todos."
        return todos.count(), "\n".join(f"⏰ {todo.name}" for todo in todos)

    def _get_completed_since_last_message(self) -> list["Todo"]:
        last_msg = self.last_message
        if not last_msg:
            return []
        return list(
            self.todos.filter(
                completed__gt=last_msg["datetime"], status="DONE"
            ).order_by("-completed")
        )

    def _get_completed_names(self) -> str:
        completed_todos = self._get_completed_since_last_message()
        if not completed_todos:
            return ""
        return "\n".join(
            f"{todo.name} at {todo.completed.strftime('%d.%m.%Y %H:%M') if todo.completed else ''}"
            for todo in completed_todos
        )

    def _save_message(self, text: str):
        self.messages.append(
            {
                "text": text,
                "datetime": timezone.now().isoformat(),
            }
        )
        self.save()

    async def send_completed_todos(self):
        completed_names = await sync_to_async(self._get_completed_names)()
        if not completed_names:
            return
        text = f"{self.telegram_user_tag} thank you for completing the following todos:\n{completed_names}"
        await self.send_message(text)
        await sync_to_async(self._save_message)(text)

    async def send_current_todos(self):
        if not self.should_send_new_message():
            return
        pre = f"{self.telegram_user_tag} " if self.telegram_user_tag else ""
        count, names = await sync_to_async(self._get_todo_names)()
        if count == 0:
            return
        link = f"Check: https://goals.danielmoessner.de{self.link}"
        text = f"{pre}you have {count} active todos:\n{names}\n{link}"
        await self.send_message(text)
        await sync_to_async(self._save_message)(text)

    async def send_updates(self):
        await self.send_completed_todos()
        await self.send_current_todos()


class Todo(models.Model):
    page = models.ForeignKey(
        Page, null=True, blank=True, on_delete=models.CASCADE, related_name="todos"
    )
    name = models.CharField(max_length=300)
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name="todos")
    activate = models.DateTimeField(null=True, blank=True)
    deadline = models.DateTimeField(null=True, blank=True)
    completed = models.DateTimeField(null=True, blank=True)
    status_choices = (("ACTIVE", "Active"), ("DONE", "Done"), ("FAILED", "Failed"))
    status = models.CharField(choices=status_choices, max_length=20, default="ACTIVE")
    created = models.DateTimeField(auto_created=True, null=True)
    updated = models.DateTimeField(auto_now=True, null=True)

    if TYPE_CHECKING:
        pipeline_todos: models.QuerySet["PipelineTodo"]

    class Meta:
        ordering = ("status", "-completed", "name", "deadline", "activate")

    @staticmethod
    def get_todos(todos, include_old_todos=False):
        if not include_old_todos:
            todos = todos.exclude(completed__lt=timezone.now() - timedelta(days=40))
        return todos

    @staticmethod
    def get_todos_user(user, to_do_class):
        all_todos = to_do_class.objects.filter(user=user)
        todos = Todo.get_todos(all_todos, include_old_todos=user.show_old_todos)
        return todos

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
            self.pipeline_todos.filter(activate=None).update(activate=timezone.now())
        elif self.status == "FAILED":
            self.pipeline_todos.filter(activate=None).update(
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
        repetitive_todos = [self]
        next_repetitive_to_do = self.get_next()
        if next_repetitive_to_do:
            repetitive_todos = repetitive_todos + next_repetitive_to_do.get_all_after()
        return repetitive_todos

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
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        seconds = seconds % 60

        parts = []
        if days > 0:
            parts.append(f"{days} day{'s' if days > 1 else ''}")
        if hours > 0:
            parts.append(f"{hours} hour{'s' if hours > 1 else ''}")
        if minutes > 0:
            parts.append(f"{minutes} minute{'s' if minutes > 1 else ''}")
        if seconds > 0:
            parts.append(f"{seconds} second{'s' if seconds > 1 else ''}")

        if len(parts) == 0:
            return "Reappears"
        elif len(parts) == 1:
            return "Reappears " + parts[0] + " after completion"
        else:
            return (
                "Reappears "
                + ", ".join(parts[:-1])
                + " and "
                + parts[-1]
                + " after completion"
            )

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
        Todo, null=True, on_delete=models.SET_NULL, related_name="pipeline_todos"
    )


class NotesTodo(Todo):
    notes = models.TextField(blank=True)
    POSITION_TOP = "TOP"
    POSITION_BOTTOM = "BOTTOM"
    POSITION_CHOICES = ((POSITION_TOP, "Top"), (POSITION_BOTTOM, "Bottom"))
    position = models.CharField(choices=POSITION_CHOICES, max_length=20, default="TOP")

    @property
    def avg_line_length(self):
        return len(self.notes) / self.notes.count("\n")

    @property
    def is_wide(self):
        return self.avg_line_length > 45
