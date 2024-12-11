from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404
from .models import Profile
from .serializers import ProfileSerializer
from rest_framework.permissions import IsAuthenticated

class ProfileDetail(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        profile = get_object_or_404(Profile, owner=request.user)
        data = ProfileSerializer(profile, context={'request': request}).data
        return Response(data)
    
    def post(self, request):
        # Check if the user already has a profile
        existing_profile = Profile.objects.filter(owner=request.user).exists()
        if existing_profile:
            return Response(
                {"error": "Profile already exists for this user"}, 
                status=status.HTTP_400_BAD_REQUEST
            )

        # Create a new profile
        serializer = ProfileSerializer(data=request.data, context={'request': request})
        
        if serializer.is_valid():
            # Automatically set the owner to the current user
            serializer.save(owner=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def patch(self, request):
        # Get the existing profile
        profile = get_object_or_404(Profile, owner=request.user)
        
        # Partial update
        serializer = ProfileSerializer(
            profile, 
            data=request.data, 
            partial=True, 
            context={'request': request}
        )
        
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)