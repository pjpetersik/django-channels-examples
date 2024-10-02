from asgiref.sync import async_to_sync

from checklist.models import Item, Task
from checklist.serializers import ItemSerializer, TaskSerializer


class ReceiverError(Exception):
    pass


class Receiver:
    def create(self, data):
        raise NotImplementedError

    def update(self, data):
        raise NotImplementedError

    def delete(self, data):
        raise NotImplementedError


class GenericReceiver(Receiver):
    """A generic receiver class which uses functionalities of the `rest_framework` to 
    validate and serialize Model instances.

    The `get_queryset` must be implemented and return queryset of a Django model. 
    In addition, the `serializer_class` must be set with a `rest_framework` serializer 
    which can be used to validate and serialize objects of/for the corresponding Django model. 
    """
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


class ReceiverMixin:
    @property
    def allow_actions(self):
        return ["create", "update", "delete"]
    
    def get_receiver(self, entity):
        """Method that returns an instance of a receiver, e.g. instance from a class that inherited 
        from the`GenericReicver` class."""
        raise NotImplementedError

    def receive_json(self, data):
        message_type = data.pop("type")
        try:
            if self.user.is_authenticated:
                split = message_type.split(".")
                if len(split) != 2:
                    msg = "Format must by 'ENTITY.ACTION'"
                    raise ReceiverError(msg)

                entity, action = split
                receiver = self.get_receiver(entity)

                if not receiver:
                    msg = f"No entity found with name {entity}"
                    raise ReceiverError(msg)

                if action not in self.allow_actions:
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
            self.send_json({"type": "error", "message": msg})


class TaskReceiver(GenericReceiver):
    serializer_class = TaskSerializer

    def get_queryset(self):
        return Task.objects.filter(user=self.user)

    def create(self, data):
        data["user"] = self.user
        return super().create(data)

    def update(self, data):
        data["user"] = self.user
        return super().update(data)


class ItemReceiver(GenericReceiver):
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
