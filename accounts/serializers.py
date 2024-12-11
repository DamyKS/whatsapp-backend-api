from django.contrib.auth import get_user_model 
from rest_framework import serializers
from .models import Profile

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = get_user_model()
        fields = ('id', 'username')
        #read_only_fields = ['id', 'username']


class ProfileSerializer(serializers.ModelSerializer):
    owner = UserSerializer(read_only=True) 
    followers = UserSerializer(many=True, read_only=True)
    class Meta:
        model = Profile
        fields = [
            'id', 
            'owner',  
            'bio', 
            'profile_picture', 
            'cover_picture', 
            'phone_number',
            'online_status',
            'last_seen',
            'followers'
        ]
        read_only_fields = ['id', 'owner', 'followers']
