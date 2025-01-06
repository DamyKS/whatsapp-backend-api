from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404
from .models import Chat, Message, CallSession
from .serializers import ChatSerializer , MessageSerializer, CallSessionSerializer, DecryptedMessageSerializer

class ChatList(APIView):
    def get(self, request):
        #chats = Chat.objects.all()
        chats = Chat.objects.filter(participants=request.user)
        data = ChatSerializer(chats, many=True, context={'request': request}).data
        return Response(data)
    
    def post(self, request):
        serializer = ChatSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        chat = serializer.save()
        return Response(ChatSerializer(chat).data, status=status.HTTP_201_CREATED)

class ChatDetail(APIView):
    def get(self, request, pk):
        chat = get_object_or_404(Chat, pk=pk)
        messages = chat.messages
        for msg in messages.all():
            msg.read_by.add(request.user)
        data = MessageSerializer(messages, many=True).data
        return Response(data)
    
    def post(self, request, pk):
        chat = get_object_or_404(Chat, pk=pk)
        serializer = MessageSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        message= serializer.save()
        message.read_by.add(request.user)
        chat.messages.add(message)
        chat.save()
        return Response(MessageSerializer(message).data, status=status.HTTP_201_CREATED)


class MessageDetail(APIView):
    def get(self, request, pk):
        message = get_object_or_404(Message, pk=pk)
        data = MessageSerializer(message).data
        return Response(data)
    
    def put(self, request,pk ):
        message = get_object_or_404(Message, pk=pk)  # Find message
        serializer = MessageSerializer(message, data=request.data, context={'request': request}, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()  # Update existing message
        return Response(serializer.data)

    def delete(self, request, pk):
        message= get_object_or_404(Message, pk=pk)
        message.delete()  # Delete the message
        return Response(status=status.HTTP_204_NO_CONTENT)

def room(request,room_id):
    chat = Chat.objects.get(pk=room_id)
    messages = chat.messages.order_by('timestamp').all()
    messages= DecryptedMessageSerializer(messages,many=True, context={'request': request}).data

    return render(request, 'chatroom.html', {
        'room_id': room_id,
        'messages':messages,
        'request': request, 
    })


class CallSessionList(APIView):
    def get(self, request):
        call_sessions = CallSession.objects.all()
        data = CallSessionSerializer(call_sessions, many=True).data
        return Response(data)
    
    def post(self, request):
        serializer = CallSessionSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        call_session = serializer.save()
        return Response(CallSessionSerializer(call_session).data, status=status.HTTP_201_CREATED)


class CallSessionDetail(APIView):
    pass

class ChatSearch(APIView):
    def post(self, request, pk):
        """
        Searches for messages within a specific chat.
        """
        chat = get_object_or_404(Chat, pk=pk)
        search_text = request.data.get('search_text', None)

        if not search_text:
            return Response([], status=status.HTTP_200_OK) 

        messages = chat.messages.filter(content__icontains=search_text)
        serializer = MessageSerializer(messages, many=True)
        return Response(serializer.data)
        