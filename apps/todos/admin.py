from django.contrib import admin

from apps.todos.models import (
    NeverEndingTodo,
    NormalTodo,
    NotesTodo,
    Page,
    PipelineTodo,
    RepetitiveTodo,
)

admin.site.register(NormalTodo)
admin.site.register(NeverEndingTodo)
admin.site.register(PipelineTodo)
admin.site.register(RepetitiveTodo)
admin.site.register(NotesTodo)
admin.site.register(Page)
