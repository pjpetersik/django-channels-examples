from asyncio.exceptions import TimeoutError
from asgiref.sync import sync_to_async
from channels.testing import WebsocketCommunicator
from django.contrib.auth import get_user_model
from django.test import TransactionTestCase

from checklist.models import Task, Item
from core.asgi import application

User = get_user_model()


class ChecklistConsumerTestCase(TransactionTestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="user1", password="password")
        self.task = Task.objects.create(
            name="Test Task",
            user=self.user
        )
        
        self.item = Item.objects.create(
            task=self.task,
            name="Test Item 1"
        )

    async def test_connect_unauthenticated_user(self):
        communicator = WebsocketCommunicator(application, "/ws/checklist/")
        connected, subprotocol = await communicator.connect()
        self.assertTrue(connected)
        
        with self.assertRaises(TimeoutError):
            await communicator.receive_json_from()
        await communicator.disconnect()

    async def test_connect_authenticated_user(self):
        communicator = WebsocketCommunicator(application, "/ws/checklist/")
        communicator.scope["user"] = self.user
        connected, subprotocol = await communicator.connect()
        
        self.assertTrue(connected)

        response = await communicator.receive_json_from()
        self.assertEqual(response["type"], "task.list")

        with self.assertRaises(TimeoutError):
            await communicator.receive_json_from()
        await communicator.disconnect()
