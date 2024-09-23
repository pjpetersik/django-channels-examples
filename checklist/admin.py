from django.contrib import admin
from checklist.models import Task, Item


class ItemInline(admin.TabularInline):
    model = Item
    extra = 1


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    model = Task
    inlines = [ItemInline]
