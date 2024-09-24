import json

from asgiref.sync import async_to_sync
from channels.generic.websocket import WebsocketConsumer

from checklist.models import Item, Task
from checklist.serializers import ItemSerializer, TaskSerializer


class ReceiverError(Exception):
    pass


class BaseReceiver:
    serializer_class = None

    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)

    def get_queryset():
        raise NotImplementedError

    def get_object(self, pk):
        return self.get_queryset().get(pk=pk)

    def create(self, data):
        serializer = self.serializer_class(data=data)
        if not serializer.is_valid():
            raise ReceiverError(str(serializer.errors))
        serializer.save()
        data = serializer.data.copy()
        return data

    def update(self, data):
        instance = self.get_object(pk=data["id"])
        return self.perform_update(instance, data)

    def perform_update(self, instance, data):
        serializer = self.serializer_class(instance=instance, data=data)
        if not serializer.is_valid():
            raise ReceiverError(str(serializer.errors))
        
        serializer.save()
        data = serializer.data.copy()
        return data

    def delete(self, data):
        instance = self.get_object(pk=data["id"])
        instance.delete()
        return {"id": data["id"]}


class TaskReceiver(BaseReceiver):
    serializer_class = TaskSerializer

    def get_queryset(self):
        return Task.objects.filter(user=self.user)

    def create(self, data):
        data["user"] = self.user
        return super().create(data)

    def update(self, data):
        data["user"] = self.user
        return super().update(data)


class ItemReceiver(BaseReceiver):
    serializer_class = ItemSerializer

    def get_queryset(self):
        return Item.objects.filter(task__user=self.user)

    def create(self, data):
        data["done_by"] = self.user
        return super().create(data)

    def perform_update(self, instance, data):
        data["task"] = instance.task.pk
        data["name"] = instance.name
        data["done_by"] = self.user.username if instance.done_at else None
        return super().perform_update(instance, data)


class ChecklistConsumer(WebsocketConsumer):

    def __init__(self, *args, **kwargs):
        super().__init__(args, kwargs)
        self.group_name = None
        self.receivers = {}

    def connect(self):
        self.user = self.scope["user"]
        self.accept()

        if self.user.is_authenticated:
            self.group_name = f"checklist_{self.user.pk}"
            
            async_to_sync(self.channel_layer.group_add)(
                self.group_name,
                self.channel_name
            )

            queryset = Task.objects.filter(user=self.user)
            self.task_list({
                "type": "task.list",
                "tasks": TaskSerializer(queryset, many=True).data
            })

            self.receivers["task"] = TaskReceiver(user=self.user)
            self.receivers["item"] = ItemReceiver(user=self.user)

    def disconnect(self, close_code):
        if self.user.is_authenticated:
            async_to_sync(self.channel_layer.group_discard)(
                self.group_name,
                self.channel_name
            )

    def receive(self, text_data=None, bytes_data=None):
        data = json.loads(text_data)
        message_type = data.pop("type")
        try:
            if self.user.is_authenticated:
                split = message_type.split(".")
                if len(split) != 2:
                    msg = "Format must by 'ENTITY.ACTION'"
                    raise ReceiverError(msg)
                
                entity, action = split
                receiver = self.receivers.get(entity)

                if not receiver:
                    msg = f"No entity found with name {entity}"
                    raise ReceiverError(msg)

                if action not in ["create", "update", "delete"]:
                    msg = f"No action found with name {action}"
                    raise ReceiverError(msg)

                data = getattr(receiver, action)(data)
                data["type"] = message_type
                async_to_sync(self.channel_layer.group_send)(
                    self.group_name,
                    data,
                )
        
        except ReceiverError as e:
            msg = f"Message type '{message_type}' cannot be processed: " + str(e)
            self.send(json.dumps({"type": "error", "message": msg}))

    def task_list(self, event):
        self.send(json.dumps(event))

    def task_create(self, event):
        self.send(json.dumps(event))

    def task_update(self, event):
        self.send(json.dumps(event))

    def task_delete(self, event):
        self.send(json.dumps(event))

    def item_create(self, event):
        self.send(json.dumps(event))

    def item_update(self, event):
        self.send(json.dumps(event))

    def item_delete(self, event):
        self.send(json.dumps(event))
