from asgiref.sync import async_to_sync
from channels.generic.websocket import JsonWebsocketConsumer

from checklist.models import Task
from checklist.receivers import ItemReceiver, TaskReceiver, ReceiverMixin
from checklist.serializers import TaskSerializer


class ChecklistConsumer(ReceiverMixin, JsonWebsocketConsumer):
    def __init__(self, *args, **kwargs):
        super().__init__(args, kwargs)
        self.group_name = None
        self.receivers = {}

    def get_receiver(self, entity):
        return self.receivers.get(entity)

    def connect(self):
        self.user = self.scope["user"]
        self.accept()

        if self.user.is_authenticated:
            self.group_name = f"checklist_{self.user.pk}"

            async_to_sync(self.channel_layer.group_add)(
                self.group_name, self.channel_name
            )

            queryset = Task.objects.filter(user=self.user)
            self.task_list(
                {"type": "task.list", "tasks": TaskSerializer(queryset, many=True).data}
            )

            self.receivers = {
                "task": TaskReceiver(user=self.user),
                "item": ItemReceiver(user=self.user),
            }

    def disconnect(self, close_code):
        if self.user.is_authenticated:
            async_to_sync(self.channel_layer.group_discard)(
                self.group_name, self.channel_name
            )

    def task_list(self, event):
        self.send_json(event)

    def task_create(self, event):
        self.send_json(event)

    def task_update(self, event):
        self.send_json(event)

    def task_delete(self, event):
        self.send_json(event)

    def item_create(self, event):
        self.send_json(event)

    def item_update(self, event):
        self.send_json(event)

    def item_delete(self, event):
        self.send_json(event)
