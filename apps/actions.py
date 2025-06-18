from typing import Any, Protocol

from django.contrib.auth.models import AbstractBaseUser, AnonymousUser

from apps.achievements.forms import (
    CreateAchievement,
    DeleteAchievement,
    UpdateAchievement,
)
from apps.goals.forms import (
    AddMonitor,
    CreateGoal,
    DecreaseProgress,
    DeleteGoal,
    DeleteMonitor,
    IncreaseProgress,
    UpdateGoal,
    UpdateGoalSettings,
    UpdateMonitor,
)
from apps.notes.forms import CreateNote, DeleteNote, UpdateNote
from apps.story.forms import UpdateStory
from apps.todos.forms import (
    CreateNeverEndingTodo,
    CreateNormalTodo,
    CreateNotesTodo,
    CreatePage,
    CreatePipelineTodo,
    CreateRepetitiveTodo,
    CreateTodoFast,
    DeletePage,
    DeleteTodo,
    SharePage,
    ToggleTodo,
    UpdateNeverEndingTodo,
    UpdateNormalTodo,
    UpdateNotesTodo,
    UpdatePage,
    UpdateRepetitiveTodo,
    UpdateTodoSettings,
)
from apps.uploads.forms import CreateUpload, DeleteUpload, UploadFile
from apps.users.forms import ChangeEmail, ChangePassword, Login, Register, ResetPassword
from apps.users.models import CustomUser
from config.form_addons import Addons


class FormClass(Protocol):
    addons: Addons

    def __init__(
        self,
        user: CustomUser | AbstractBaseUser | AnonymousUser,
        opts: dict[str, Any],
        *args,
        **kwargs,
    ): ...

    def ok(self) -> int: ...

    def is_valid(self) -> bool: ...

    def _has_addon(self, key: str) -> bool: ...


# improve to import automatically
FORMS: list[type[FormClass]] = [
    CreateTodoFast,
    CreateNormalTodo,
    UpdateNormalTodo,
    UpdateNeverEndingTodo,
    DeleteTodo,
    ToggleTodo,
    CreateNeverEndingTodo,
    CreateRepetitiveTodo,
    CreateNotesTodo,
    UpdateNotesTodo,
    UpdateRepetitiveTodo,
    CreatePipelineTodo,
    CreateAchievement,
    UpdateAchievement,
    DeleteAchievement,
    CreateNote,
    UpdateNote,
    DeleteNote,
    UpdateStory,
    Login,
    Register,
    ResetPassword,
    ChangeEmail,
    ChangePassword,
    CreateGoal,
    UpdateGoal,
    DeleteGoal,
    AddMonitor,
    IncreaseProgress,
    DecreaseProgress,
    UpdateMonitor,
    DeleteMonitor,
    UpdateTodoSettings,
    UpdateGoalSettings,
    CreateUpload,
    UploadFile,
    DeleteUpload,
    CreatePage,
    UpdatePage,
    SharePage,
    DeletePage,
]


NAVS = {
    "create": "create_nav.html",
    "todos": "todos/nav.html",
    "achievements": "achievements/nav.html",
    "notes": "notes/nav.html",
    "story": "story/nav.html",
    "settings": "users/nav.html",
    "goals": "goals/nav.html",
    "uploads": "uploads/nav.html",
}
