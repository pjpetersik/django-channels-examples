from asgiref.sync import sync_to_async
from django.contrib.auth import get_user_model
from django.test import TransactionTestCase
from channels.testing import WebsocketCommunicator

from chat.models import Room, Message
from core.asgi import application

User = get_user_model()


class ChatConsumerTestCase(TransactionTestCase):
    def setUp(self):
        # Create test users and a room
        self.user1 = User.objects.create_user(username="user1", password="password")
        self.user2 = User.objects.create_user(username="user2", password="password")
        self.room = Room.objects.create(name="testroom")
    
    async def test_connect_unauthenticated_user(self):
        # Test WebSocket connection for an authenticated user
        communicator = WebsocketCommunicator(application, f"/ws/chat/{self.room.name}/")
        connected, subprotocol = await communicator.connect()
        self.assertFalse(connected)

        await communicator.disconnect()

    async def test_connect_authenticated_user(self):
        # Test WebSocket connection for an authenticated user
        communicator = WebsocketCommunicator(application, f"/ws/chat/{self.room.name}/")
        communicator.scope["user"] = self.user1
        connected, subprotocol = await communicator.connect()
        
        self.assertTrue(connected)

        response = await communicator.receive_json_from()
        self.assertEqual(response["type"], "user.list")
        self.assertIn(self.user1.username, response["users"])

        response = await communicator.receive_json_from()
        self.assertEqual(response["type"], "user.join")
        self.assertEqual(response["user"], self.user1.username)

        # Send a chat message
        message = {"message": "Hello, World!"}
        await communicator.send_json_to(message)

        response = await communicator.receive_json_from()
        self.assertEqual(response["type"], "chat.message")
        self.assertEqual(response["user"], "user1")
        self.assertEqual(response["message"], "Hello, World!")

        # Verify that the message was saved to the database
        exists = await sync_to_async(Message.objects.filter(user=self.user1, room=self.room, content="Hello, World!").exists)()
        self.assertTrue(exists)
       
        await communicator.disconnect()

    async def test_private_message(self):
        # Simulate private messaging between two authenticated users
        communicator_sender = WebsocketCommunicator(application, f"/ws/chat/{self.room.name}/")
        communicator_sender.scope["user"] = self.user1
        await communicator_sender.connect()
        response = await communicator_sender.receive_json_from()
        response = await communicator_sender.receive_json_from()

        communicator_receiver = WebsocketCommunicator(application, f"/ws/chat/{self.room.name}/")
        communicator_receiver.scope["user"] = self.user2
        await communicator_receiver.connect()
        response = await communicator_receiver.receive_json_from()
        response = await communicator_receiver.receive_json_from()

        # User1 sends a private message to User2
        pm_message = "/pm user2 Hello, this is a private message!"
        await communicator_sender.send_json_to({"message": pm_message})

        # User2 receives the private message
        response = await communicator_receiver.receive_json_from()
        self.assertEqual(response["type"], "private.message")
        self.assertEqual(response["user"], "user1")
        self.assertEqual(response["message"], "Hello, this is a private message!")

        await communicator_sender.disconnect()
        await communicator_receiver.disconnect()

    async def test_user_join_and_leave(self):
        # User1 joins the room
        communicator1 = WebsocketCommunicator(application, f"/ws/chat/{self.room.name}/")
        communicator1.scope["user"] = self.user1
        await communicator1.connect()
        response = await communicator1.receive_json_from()
        response = await communicator1.receive_json_from()

        # User2 joins the room
        communicator2 = WebsocketCommunicator(application, f"/ws/chat/{self.room.name}/")
        communicator2.scope["user"] = self.user2
        await communicator2.connect()
        response = await communicator2.receive_json_from()
        response = await communicator2.receive_json_from()

        # User1 should receive notification of User2 joining
        response = await communicator1.receive_json_from()
        self.assertEqual(response["type"], "user.join")
        self.assertEqual(response["user"], "user2")

        # User1 leaves the room
        await communicator1.disconnect()

        # User2 should receive notification of User1 leaving
        response = await communicator2.receive_json_from()
        self.assertEqual(response["type"], "user.leave")
        self.assertEqual(response["user"], "user1")

        await communicator2.disconnect()
