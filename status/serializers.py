from django.contrib.auth import get_user_model 
from rest_framework import serializers
from .models import Status
from chat.serializers import UserSerializer

class StatusSerializer(serializers.ModelSerializer):
    creator  = serializers.StringRelatedField()
    seen_by = serializers.StringRelatedField(many=True)
    num_of_views= serializers.SerializerMethodField() 
    class Meta:
        fields = ('id', 'creator', 'created_at','caption','image', 'seen_by', 'num_of_views')
        model = Status
        #read_only_fields = ['id', 'timestamp', 'seen_by']
    
    def get_num_of_views(self,obj):
        if obj.seen_by:
            return obj.seen_by.count()
        else:
            return 0