from django.shortcuts import render

from checklist.models import Task


def index_view(request):
    context = {"tasks": Task.objects.all()}
    return render(request, "checklist/index.html", context)
