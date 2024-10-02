# django-channels-examples

This Django project contains example apps that use the `channels` package to implement WebSocket-based real-time features. It currently includes two main apps:

- **Chat App:** A real-time chat application following the tutorial on [TestDriven.io](https://testdriven.io/blog/django-channels/).
- **Checklist App:** A task management app that leverages WebSocket connections to handle real-time task and item updates.

The focus of this repository is on the backend/Django part and not on the frontend/javascript part of the communication via WebSockets.

## Table of Contents

- [Getting started](#getting-started)
- [Running the Apps](#running-the-apps)
- [Checklist App Overview](#checklist-app-overview)
  - [ChecklistConsumer Explanation](#checklistconsumer-explanation)
  - [Receivers](#receivers)
- [Notes](#notes)

## Getting started
### 1. Install the necessary dependencies
Create a virtual environment and install the required dependencies:

```bash
python -m venv venv
source venv/bin/activate  # On Windows use `venv\Scripts\activate`
pip install -r requirements.txt
```

### 2. Migrate the database
Set up the database by running migrations:
```bash
python manage.py migrate
```

### 3. Run the Redis channels layer
Django Channels requires a message broker for handling WebSocket communication. In this example, Redis is used. Start a Redis instance using Docker:
```bash
docker run --rm -p 6379:6379 redis:7
```

### 4. Start the Django development server
Finally, start the development server:
```bash
python manage.py runserver
```

## Running the Apps
Both apps require to be logged in to be fully functional. You can login via the [Django Admin interface](http://localhost:8000/admin/).

### Chat App
You can find the chat app under http://localhost:8000/chat/. The Chat app is a simple real-time chat room application that primarily follows the tutorial from [TestDriven.io](https://testdriven.io/blog/django-channels/). You can explore real-time WebSocket functionality by opening multiple browser windows and joining a chat room.

### Checklist App
You can find the checklist app under http://localhost:8000/checklist/. The Checklist app has the same real-time functionality as the Chat app but here one consumer is used to perform all CRUD (create, read, update, delete) operations which are required by the app. Morevover, the `Receiver` class is introduced which is a specialized class that handles the business logic for processing the incoming create, update and delete events.

#### Receivers
In the `receivers` module, a `GenericReceiver` class is introduced which is a reusable handler for processing model instances (e.g. of `Task`s or `Item`s) through WebSocket actions. The `GenericReceiver` class expects that a `serializer_class` and `get_queryset` method are implemented. The serializer is must be a `rest_framework` serializer. It is used for the validation and serialization of instances.

Each specific entity (`Task` or `Item`) has its own receiver class (`TaskReceiver`, `ItemReceiver`) that extends `GenericReceiver`:
- **TaskReceiver:**
  - Handles creation, updating, and deletion of `Task` objects.
    Filters tasks by the authenticated user to ensure data privacy.
- **ItemReceiver:**
  - Handles creation, updating, and deletion of `Item` objects.
  - Ensures that only items belonging to the user's tasks are processed.

Finally, a `ReceiverMixin` class is built to extend a `JsonWebsocketConsumer` to work in a generic way with various receiver instances.