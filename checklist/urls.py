from django.urls import path

from checklist import views

urlpatterns = [
    path("", views.index_view, name="checklist-index"),
]
