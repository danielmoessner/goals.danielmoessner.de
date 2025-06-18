from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.http import HttpRequest
from django.shortcuts import render
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
    get_end_of_next_week,
    get_end_of_week,
    get_start_of_next_week,
    get_start_of_week,
)
from apps.utils.functional import list_sort


@login_required
def todos(request: HttpRequest):
    todos: list[Todo] = []
    kind = request.GET.get("kind", "week")
    for cls in [NormalTodo, PipelineTodo, NeverEndingTodo, RepetitiveTodo]:
        f = Q()
        if kind == "week":
            start_of_week = get_start_of_week()
            end_of_week = get_end_of_week()
            now = timezone.now()
            f = Q(activate__lte=now, status="ACTIVE") | Q(
                completed__gte=start_of_week, completed__lte=end_of_week
            )
        if kind == "next_week":
            start_of_next_week = get_start_of_next_week()
            end_of_next_week = get_end_of_next_week()
            f = Q(activate__lte=start_of_next_week, status="ACTIVE") | Q(
                completed__gte=start_of_next_week, completed__lte=end_of_next_week
            )
        elif kind == "activated":
            f = Q(activate__lte=timezone.now())
        elif kind == "open":
            f = Q(status="ACTIVE")

        todos += Todo.get_todos_user(request.user, cls).filter(f).filter(page=None)
    todos = list_sort(todos, lambda t: t.completed_sort)
    top_notes = NotesTodo.objects.filter(
        user=request.user, status="ACTIVE", position=NotesTodo.POSITION_TOP
    )
    bottom_notes = NotesTodo.objects.filter(
        user=request.user, status="ACTIVE", position=NotesTodo.POSITION_BOTTOM
    )
    pages = Page.objects.filter(user=request.user).order_by("name")
    return render(
        request,
        "todos.html",
        {
            "todos": todos,
            "top_notes": top_notes,
            "bottom_notes": bottom_notes,
            "pages": pages,
        },
    )


@login_required
def page(request: HttpRequest, pk: int):
    page = Page.objects.get(pk=pk, user=request.user)
    todos: list[Todo] = []
    for cls in [NormalTodo, PipelineTodo, NeverEndingTodo, RepetitiveTodo]:
        todos += Todo.get_todos_user(request.user, cls).filter(page=page)
    top_notes = NotesTodo.objects.filter(
        page=page, status="ACTIVE", position=NotesTodo.POSITION_TOP
    )
    bottom_notes = NotesTodo.objects.filter(
        page=page, status="ACTIVE", position=NotesTodo.POSITION_BOTTOM
    )
    pages = Page.objects.filter(user=request.user).order_by("name")
    return render(
        request,
        "todos.html",
        {
            "page": page,
            "todos": todos,
            "top_notes": top_notes,
            "bottom_notes": bottom_notes,
            "pages": pages,
        },
    )


def shared_page(request: HttpRequest, uuid: int):
    page = Page.objects.get(share_uuid=uuid, is_shared=True)
    todos: list[Todo] = []
    for cls in [NormalTodo, PipelineTodo, NeverEndingTodo, RepetitiveTodo]:
        todos += Todo.get_todos(cls.objects.filter(page=page), False).filter(page=page)
    top_notes = NotesTodo.objects.filter(
        page=page, status="ACTIVE", position=NotesTodo.POSITION_TOP
    )
    bottom_notes = NotesTodo.objects.filter(
        page=page, status="ACTIVE", position=NotesTodo.POSITION_BOTTOM
    )
    return render(
        request,
        "shared.html",
        {
            "page": page,
            "todos": todos,
            "top_notes": top_notes,
            "bottom_notes": bottom_notes,
        },
    )
