from django.shortcuts import render

from chat.models import Room


def index_view(request):
    context = {"rooms": Room.objects.all()}
    return render(request, "chat/index.html", context)


def room_view(request, room_name):
    chat_room, created = Room.objects.get_or_create(name=room_name)
    context = {"room": chat_room}
    return render(request, "chat/room.html", context)
