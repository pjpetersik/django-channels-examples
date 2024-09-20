from asgiref.sync import async_to_sync
from django.core.management.base import BaseCommand
from channels.layers import get_channel_layer


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument(
            "--room_name",
            action="store",
            type=str
        )

        parser.add_argument(
            "--message",
            action="store",
            type=str
        )
    
    def handle(self, *args, **options):
        channel_layer = get_channel_layer()

        group_name = f"chat_{options['room_name']}"
        async_to_sync(channel_layer.group_send)(
            group_name,
            {
                "type": "chat.message", 
                "user": "ADMIN",
                "message": options["message"]
            },
        )
