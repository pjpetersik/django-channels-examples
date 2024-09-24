from django.contrib.auth.models import User
from rest_framework import serializers

from checklist.models import Item, Task


class ItemSerializer(serializers.ModelSerializer):
    done_by = serializers.SlugRelatedField(
        slug_field="username", queryset=User.objects.all(), allow_null=True
    )

    class Meta:
        model = Item
        fields = ["id", "done_at", "done_by", "name", "task"]


class TaskSerializer(serializers.ModelSerializer):
    user = serializers.SlugRelatedField(
        slug_field="username", queryset=User.objects.all(), allow_null=True
    )
    item_set = ItemSerializer(many=True, read_only=True)

    class Meta:
        model = Task
        fields = ["id", "item_set", "name", "user"]
