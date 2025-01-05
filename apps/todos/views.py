from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.http import HttpRequest
from django.shortcuts import render
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

        todos += Todo.get_to_dos_user(request.user, cls).filter(f)
    todos = list_sort(todos, lambda t: t.completed_sort)
    notes = NotesTodo.objects.filter(user=request.user, status="ACTIVE")
    return render(request, "todos.html", {"todos": todos, "notes": notes})
