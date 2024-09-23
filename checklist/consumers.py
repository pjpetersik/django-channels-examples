import json

from asgiref.sync import async_to_sync
from channels.generic.websocket import WebsocketConsumer
from django.core.serializers.json import DjangoJSONEncoder

from .models import Task, Item


class ChecklistConsumer(WebsocketConsumer):
    def __init__(self, *args, **kwargs):
        super().__init__(args, kwargs)
        self.group_name = None

    def connect(self):
        self.user = self.scope["user"]
        self.accept()

        if self.user.is_authenticated:
            self.group_name = f"checklist_{self.user.pk}"
            
            async_to_sync(self.channel_layer.group_add)(
                self.group_name,
                self.channel_name
            )

            self._send_task_list()

    def disconnect(self, close_code):
        if self.user.is_authenticated:
            async_to_sync(self.channel_layer.group_discard)(
                self.group_name,
                self.channel_name
            )

    def receive(self, text_data=None, bytes_data=None):
        data = json.loads(text_data)
        message_type = data.pop("type")
        
        if self.user.is_authenticated:
            if message_type == "task.add":
                task = Task.objects.create(
                    user=self.user,
                    name=data["name"]
                )
                data = self._get_task_data(task)
                data["type"] = "task.add"
                async_to_sync(self.channel_layer.group_send)(
                    self.group_name,
                    data,
                )
                return

            elif message_type == "task.update":
                task = Task.objects.get(pk=data.pop("id"))
                for k, v in data.items():
                    setattr(task, k, v)
                task.save()

                data = self._get_task_data(task)
                data["type"] = "task.update"
                data_json = json.loads(json.dumps(data, cls=DjangoJSONEncoder))
                
                async_to_sync(self.channel_layer.group_send)(
                    self.group_name,
                    data_json,
                )
                return

            elif message_type == "task.delete":
                task_id = data.pop("id")
                task = Task.objects.get(id=task_id)
                task.delete()

                data = {"type": "task.delete", "id": task_id}
                async_to_sync(self.channel_layer.group_send)(
                    self.group_name,
                    data,
                )
                return

            elif message_type == "item.add":
                task = self.get_queryset().get(id=data.pop("taskId"))
                item = Item.objects.create(
                    task=task,
                    name=data["name"]
                )
                data = {
                    "type": "item.add",
                    "id": item.id,
                    "taskId": item.task.id, 
                    "name": item.name,
                    "done_at": item.done_at
                }
                async_to_sync(self.channel_layer.group_send)(
                    self.group_name,
                    data,
                )
                return

            elif message_type == "item.update":
                item = Item.objects.get(pk=data.pop("id"))

                for k, v in data.items():
                    setattr(item, k, v)
                    item.save()
                item.save()
                data = {
                    "type": "item.update",
                    "id": item.id,
                    "name": item.name,
                    "done_at": item.done_at
                }
                async_to_sync(self.channel_layer.group_send)(
                    self.group_name,
                    data,
                )
                return

            elif message_type == "item.delete":
                item_id = data.pop("id")
                item = Item.objects.get(pk=item_id)
                item.delete()
                data = {
                    "type": "item.delete",
                    "id": item_id,
                }
                async_to_sync(self.channel_layer.group_send)(
                    self.group_name,
                    data,
                )
                return

            else:
                msg = f"Message type '{message_type}' cannot be processed."
                self.send(json.dumps({"type": "error", "message": msg}))
                return 
            
            self._group_send_task_list()

    def get_queryset(self):
        return Task.objects.filter(user=self.user)

    def _get_task_data(self, task):
        item_list = []
        for item in task.item_set.all():
            item_list.append({"id": item.id, "name": item.name, "done_at": item.done_at})
        return {"id": task.id, "name": task.name, "items": item_list}
    
    def _get_task_list(self):
        data_list = []

        for task in self.get_queryset():
            data = self._get_task_data(task)
            data_list.append(data)
        return data_list

    def _send_task_list(self):
        data_list = self._get_task_list()
        
        self.send(json.dumps({
            "type": "task.list",
            "tasks": data_list
        }, cls=DjangoJSONEncoder))

    def _group_send_task_list(self):
        task_list = self._get_task_list()
        task_list_json = json.dumps(task_list, cls=DjangoJSONEncoder)
        async_to_sync(self.channel_layer.group_send)(
            self.group_name, 
            {
                "type": "task.list",
                "tasks": task_list_json
            }
        )

    def task_list(self, event):
        data = event.copy()
        data["tasks"] = json.loads(event["tasks"])
        self.send(json.dumps(data))

    def task_add(self, event):
        self.send(json.dumps(event, cls=DjangoJSONEncoder))

    def task_update(self, event):
        self.send(json.dumps(event, cls=DjangoJSONEncoder))

    def task_delete(self, event):
        self.send(json.dumps(event, cls=DjangoJSONEncoder))

    def item_add(self, event):
        self.send(json.dumps(event, cls=DjangoJSONEncoder))

    def item_update(self, event):
        self.send(json.dumps(event, cls=DjangoJSONEncoder))

    def item_delete(self, event):
        self.send(json.dumps(event, cls=DjangoJSONEncoder))
