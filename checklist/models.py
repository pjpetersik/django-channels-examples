from django.contrib.auth.models import User
from django.db import models


class Task(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=128)


class Item(models.Model):
    name = models.CharField(max_length=128)
    task = models.ForeignKey(Task, on_delete=models.CASCADE)
    done_at = models.DateTimeField(null=True, blank=True)
    done_by = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL)
