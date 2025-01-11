from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404
from .models import Profile, UserKey
from .serializers import ProfileSerializer
from rest_framework.permissions import IsAuthenticated

from .encryption import derive_master_key, generate_user_keys, encrypt_private_key, decrypt_private_key
from rest_framework.authtoken.models import Token
from dj_rest_auth.views import LoginView
from dj_rest_auth.views import LogoutView

from dj_rest_auth.registration.views import RegisterView
from nacl.pwhash import argon2id  
import nacl.utils
from .key_cache import UserKeyManager


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
    

class CustomRegisterView(RegisterView):
    def perform_create(self, serializer):
        password = serializer.validated_data.get('password1')
        user = serializer.save(self.request)
        
        # Generate salt and master key
        salt = nacl.utils.random(argon2id.SALTBYTES)
        master_key = derive_master_key(password, salt)
        
        # Generate and encrypt keys
        private_key, public_key = generate_user_keys()
        private_key_data = encrypt_private_key(private_key, master_key)
        # Create UserKey with the separated ciphertext and nonce
        UserKey.objects.create(
            user=user,
            public_key=public_key,
            encrypted_private_key=private_key_data['encrypted_key'],  # This is now just the ciphertext
            key_nonce=private_key_data['nonce'],
            master_key_salt=salt
        )
        
        # Create token
        Token.objects.create(user=user)
        
        # Decrypt and store in session
        try:
           
            print(private_key)
            UserKeyManager.store_session_key(user.id, private_key)
        except Exception as e:
            # Log the error but don't prevent user creation
            print(f"Failed to store session key: {str(e)}")
            
        return user


class CustomLoginView(LoginView):
    def post(self, request, *args, **kwargs):
        # Call parent class login first
        response = super().post(request, *args, **kwargs)
        
        # If login was successful
        if response.status_code == 200:
            try:
                # Get password from request data
                password = request.data.get('password')
                
                # Get user's key data
                user_key = UserKey.objects.get(user=self.user)
                
                # Derive master key using stored salt
                master_key = derive_master_key(password, user_key.master_key_salt)
                
                # Decrypt private key
                decrypted_key = decrypt_private_key(
                    encrypted_key=user_key.encrypted_private_key,
                    nonce=user_key.key_nonce,
                    master_key=master_key
                )
                
                # Store in cache
                UserKeyManager.store_session_key(request.user.id, decrypted_key)
                
                # Return original response
                return response
                
            except Exception as e:
                # Log the error but don't prevent login
                print(f"Failed to process keys during login: {str(e)}")
                
                # Add warning to response data
                response_data = response.data
                response_data['key_warning'] = 'Login successful but key processing failed'
                return Response(response_data, status=status.HTTP_200_OK)
        
        return response
    

class CustomLogoutView(LogoutView):
    def logout(self, request):
        try:
            # Clear cached key before logout
            if request.user.is_authenticated:
                UserKeyManager.clear_session_key(request.user.id)
        except Exception as e:
            print(f"Error clearing session key during logout: {str(e)}")
            
        # Proceed with normal logout
        response = super().logout(request)
        return response
    