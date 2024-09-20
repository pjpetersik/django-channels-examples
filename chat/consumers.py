import json

from asgiref.sync import async_to_sync
from channels.generic.websocket import WebsocketConsumer

from .models import Message, Room


class ChatConsumer(WebsocketConsumer):
    def __init__(self, *args, **kwargs):
        super().__init__(args, kwargs)
        self.room_name = None
        self.room_group_name = None
        self.room = None
        self.user = None
        self.user_inbox = None

    def connect(self):
        self.room_name = self.scope["url_route"]["kwargs"]["room_name"]
        self.room_group_name = f"chat_{self.room_name}"
        self.room = Room.objects.get(name=self.room_name)
        self.user = self.scope["user"]
        self.user_inbox = f"inbox_{self.user.username}"

        if not self.user.is_authenticated:
            self.close()
        else:
            self.accept()
            async_to_sync(self.channel_layer.group_add)(
                self.room_group_name,
                self.channel_name
            )
            self.room.online.add(self.user)
            self.send(json.dumps({
                "type": "user.list",
                "users": [user.username for user in self.room.online.all()]
            }))
        
            async_to_sync(self.channel_layer.group_add)(
                self.user_inbox,
                self.channel_name
            )
            async_to_sync(self.channel_layer.group_send)(
                self.room_group_name,
                {
                    "type": "user.join",
                    "user": self.user.username
                }
            )

    def disconnect(self, close_code):
        async_to_sync(self.channel_layer.group_discard)(
            self.room_group_name,
            self.channel_name
        )

        if self.user.is_authenticated:
            async_to_sync(self.channel_layer.group_discard)(
                self.user_inbox,
                self.channel_name
            )
            async_to_sync(self.channel_layer.group_send)(
                self.room_group_name,
                {
                    "type": "user.leave",
                    "user": self.user.username
                }
            )

            self.room.online.remove(self.user)

    def receive(self, text_data=None, bytes_data=None):
        text_data_json = json.loads(text_data)
        message = text_data_json["message"]

        if not self.user.is_authenticated:
            return 

        if message.startswith("/pm"):
            split = message.split(" ", 2)
            target = split[1]
            target_msg = split[2]

            async_to_sync(self.channel_layer.group_send)(
                f"inbox_{target}",
                {
                    "type": "private.message",
                    "user": self.user.username,
                    "message": target_msg
                }
            )
            self.send(json.dumps({
                "type": "private.message.delivered",
                "target": target,
                "message": target_msg
            }))
            return

        async_to_sync(self.channel_layer.group_send)(
            self.room_group_name,
            {
                "type": "chat.message",
                "user": self.user.username,
                "message": message
            }
        )
        Message.objects.create(user=self.user, room=self.room, content=message)

    def chat_message(self, event):
        self.send(text_data=json.dumps(event))

    def user_join(self, event):
        self.send(text_data=json.dumps(event))

    def user_leave(self, event):
        self.send(text_data=json.dumps(event))

    def private_message(self, event):
        self.send(text_data=json.dumps(event))

    def private_message_delivered(self, event):
        self.send(text_data=json.dumps(event))
