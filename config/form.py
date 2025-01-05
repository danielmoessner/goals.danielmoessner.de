from typing import Any, Protocol

from django.conf import settings
from django.contrib.auth.models import AbstractBaseUser, AnonymousUser
from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect, render

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
    CreatePipelineTodo,
    CreateRepetitiveTodo,
    DeleteTodo,
    ToggleTodo,
    UpdateNeverEndingTodo,
    UpdateNormalTodo,
    UpdateNotesTodo,
    UpdateRepetitiveTodo,
    UpdateTodoSettings,
)
from apps.users.forms import ChangeEmail, ChangePassword, Login, Register, ResetPassword
from apps.users.models import CustomUser
from apps.utils.functional import list_map


class FormClass(Protocol):
    def __init__(
        self,
        user: CustomUser | AbstractBaseUser | AnonymousUser,
        opts: dict[str, Any],
        *args,
        **kwargs,
    ): ...

    def ok(self) -> int: ...

    def is_valid(self) -> bool: ...


# improve to import automatically
FORMS: list[type[FormClass]] = [
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
]


NAVS = {
    "create": "create_nav.html",
    "todos": "todos/nav.html",
    "achievements": "achievements/nav.html",
    "notes": "notes/nav.html",
    "story": "story/nav.html",
    "settings": "users/nav.html",
    "goals": "goals/nav.html",
}


def get_name(cls: type[object]):
    return cls.__name__


FORMS_DICT: dict[str, type[FormClass]] = {get_name(c): c for c in FORMS}


class GetFormError(Exception):
    pass


def get_form_class(form_name: str | None) -> type[FormClass]:
    if form_name is None:
        raise GetFormError("form needs to be supplied")
    form_class = FORMS_DICT.get(form_name, None)
    if form_class is None:
        raise GetFormError(f"form with name '{form_name}' not found")
    return form_class


def get_navs(form: FormClass) -> list[str]:
    return list_map(getattr(form, "navs", []), lambda n: NAVS.get(n, ""))


def set_request(form: FormClass, request: HttpRequest) -> None:
    if hasattr(form, "inject_request"):
        form.inject_request(request)  # type: ignore


def form_view(
    request: HttpRequest, form_name: str, template_name="form_view.html"
) -> HttpResponse:
    if request.method not in ["GET", "POST"]:
        return HttpResponse("only get and post allowed", 400)

    success_url = request.GET.get("success", request.get_full_path())
    assert isinstance(success_url, str)
    cancel_url = request.GET.get("cancel_url")

    try:
        form_class = get_form_class(form_name)
    except GetFormError as e:
        return HttpResponse(str(e), 400)

    data = None
    if request.method == "POST":
        data = {}
        for key in request.POST.keys():
            v = request.POST.getlist(key)
            if len(v) == 1:
                data[key] = v[0]
            else:
                data[key] = v

    form = form_class(request.user, opts=request.GET.dict(), data=data)
    set_request(form, request)
    if request.method == "POST" and form.is_valid():
        ret = form.ok()
        success = getattr(form, "success", None)
        if success:
            return redirect(success)
        success_url = success_url.replace("0", str(ret))
        return redirect(success_url)

    response = render(
        request,
        template_name,
        {"form": form, "cancel_url": cancel_url, "navs": get_navs(form)},
    )
    return response


def global_form_view(request: HttpRequest, form_name: str) -> HttpResponse:
    if request.user.is_authenticated:
        return redirect(settings.LOGIN_REDIRECT_URL)
    return form_view(request, form_name, "global_form_view.html")
