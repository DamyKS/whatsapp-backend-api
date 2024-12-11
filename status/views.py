from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404
from .models import Status
from .serializers import StatusSerializer

from django.utils import timezone
from datetime import timedelta

class StatusList(APIView):
    def get(self, request):
        followings = request.user.follows.all()
        print(followings)
        data = {}
        for profile in followings:
            # Delete statuses older than 24 hours in a single query
            Status.objects.filter(
                creator=profile.owner, 
                created_at__lt=timezone.now() - timedelta(hours=24)
            ).delete()
            
            #fetch status for the user 
            user_status = Status.objects.filter(creator=profile.owner).all()
            username= profile.owner.username
            serialized_status = StatusSerializer(user_status, many=True).data
            data[username]= serialized_status
        return Response(data)
    
    def post(self, request):
        serializer = StatusSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        #if request.data['owner'] == request.user.username:
        new_status = serializer.save()
        return Response(StatusSerializer(new_status).data, status=status.HTTP_201_CREATED)

class StatusDetail(APIView):
    def get(self, request, status_id):
        current_status = get_object_or_404(Status, pk=status_id)
        current_status.seen_by.add(request.user)
        data = StatusSerializer(current_status).data
        return Response(data)

    def delete(self, request, status_id):
        current_status= get_object_or_404(Status, pk=status_id)
        current_status.delete()  # Delete the status
        return Response(status=status.HTTP_204_NO_CONTENT)
