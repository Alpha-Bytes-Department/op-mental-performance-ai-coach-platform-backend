# users/views.py
from rest_framework import status, generics, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView
from django.contrib.auth.tokens import default_token_generator
from django.contrib.auth import get_user_model
from django.core.mail import send_mail
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.conf import settings
from rest_framework.exceptions import ValidationError
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema, extend_schema_view
import requests
from .models import User, SocialAccount
from .serializers import (
    UserRegistrationSerializer,
    UserLoginSerializer,
    UserProfileSerializer,
    UserProfileUpdateSerializer,
    PasswordResetSerializer,
    PasswordResetConfirmSerializer
)

User = get_user_model()

@extend_schema(tags=["Registration"])
class UserRegistrationView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = UserRegistrationSerializer
    permission_classes = [permissions.AllowAny]
    
    def create(self, request, *args, **kwargs):
        email = request.data.get('email', '').lower()
        try:
            user = User.objects.get(email=email)
            if not user.is_active:
                # User exists but is not active, resend verification email
                token = default_token_generator.make_token(user)
                uid = urlsafe_base64_encode(force_bytes(user.pk))
                verify_link = f"{settings.FRONTEND_URL}/verify?uid={uid}&token={token}"
                subject = 'Verify Your Email Address (Resent)'
                message = f"""Hello {user.username},

Please verify your email by clicking the link below:

{verify_link}

If you did not request this, please ignore this email.

Best regards,
Optimal Performance Team"""
                html_message = f"""
                <html>
                    <body style="font-family: Arial, sans-serif; margin: 0; padding: 0;">
                        <table width="100%" border="0" cellspacing="0" cellpadding="0">
                            <tr>
                                <td align="center" style="padding: 20px 0;">
                                    <table width="600" border="0" cellspacing="0" cellpadding="0" style="border: 1px solid #ddd;">
                                        <tr>
                                            <td align="center" style="padding: 40px; background-color: #f7f7f7;">
                                                <h1 style="color: #333;">Verify Your Email</h1>
                                            </td>
                                        </tr>
                                        <tr>
                                            <td style="padding: 40px;">
                                                <p style="color: #333;">Hello {user.username},</p>
                                                <p style="color: #333;">It looks like you already have an account. Please click the button below to verify your email address.</p>
                                                <table width="100%" border="0" cellspacing="0" cellpadding="0">
                                                    <tr>
                                                        <td align="center" style="padding: 20px 0;">
                                                            <a href="{verify_link}" style="background-color: #007bff; color: #ffffff; padding: 15px 25px; text-decoration: none; border-radius: 5px; display: inline-block;">Verify Email</a>
                                                        </td>
                                                    </tr>
                                                </table>
                                                <p style="color: #333;">If you did not create an account, no further action is required.</p>
                                                <p style="color: #333;">Best regards,<br>The Optimal Performance Team</p>
                                            </td>
                                        </tr>
                                        <tr>
                                            <td align="center" style="padding: 20px; background-color: #f7f7f7; color: #888; font-size: 12px;">
                                                &copy; 2025 Optimal Performance. All rights reserved.
                                            </td>
                                        </tr>
                                    </table>
                                </td>
                            </tr>
                        </table>
                    </body>
                </html>
                """
                send_mail(
                    subject,
                    message,
                    settings.DEFAULT_FROM_EMAIL,
                    [user.email],
                    fail_silently=False,
                    html_message=html_message,
                )
                return Response({
                    'message': 'An account with this email already exists. A new verification email has been sent.'
                }, status=status.HTTP_200_OK)
            # If user is active, the serializer will handle the uniqueness error below
        except User.DoesNotExist:
            # No user with this email, proceed with normal registration
            pass

        serializer = self.get_serializer(data=request.data)
        try:
            serializer.is_valid(raise_exception=True)
        except ValidationError as e:
            return Response(
                {"errors": serializer.errors},
                status=status.HTTP_400_BAD_REQUEST
            )
    
        user = serializer.save() # Assumes serializer creates inactive user
        token = default_token_generator.make_token(user)
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        verify_link = f"{settings.FRONTEND_URL}/verify?uid={uid}&token={token}"
        subject = 'Verify Your Email Address'
        message = f"""Hello {user.username},

Please verify your email by clicking the link below:

{verify_link}

If you did not register, please ignore this email.

Best regards,
Optimal Performance Team"""
        html_message = f"""
        <html>
            <body style="font-family: Arial, sans-serif; margin: 0; padding: 0;">
                <table width="100%" border="0" cellspacing="0" cellpadding="0">
                    <tr>
                        <td align="center" style="padding: 20px 0;">
                            <table width="600" border="0" cellspacing="0" cellpadding="0" style="border: 1px solid #ddd;">
                                <tr>
                                    <td align="center" style="padding: 40px; background-color: #080000;">
                                        <h1 style="color: #b3a107;">Verify Your Email</h1>
                                    </td>
                                </tr>
                                <tr>
                                    <td style="padding: 40px;">
                                        <p style="color: #333;">Hello {user.username},</p>
                                        <p style="color: #333;">Thank you for registering. Please click the button below to verify your email address.</p>
                                        <table width="100%" border="0" cellspacing="0" cellpadding="0">
                                            <tr>
                                                <td align="center" style="padding: 20px 0;">
                                                    <a href="{verify_link}" style="background-color: #007bff; color: #ffffff; padding: 15px 25px; text-decoration: none; border-radius: 5px; display: inline-block;">Verify Email</a>
                                                </td>
                                            </tr>
                                        </table>
                                        <p style="color: #333;">If you did not create an account, no further action is required.</p>
                                        <p style="color: #333;">Best regards,<br>The Optimal Performance Team</p>
                                    </td>
                                </tr>
                                <tr>
                                    <td align="center" style="padding: 20px; background-color: #080000; color: #b3a107; font-size: 12px;">
                                        &copy; 2025 Optimal Performance. All rights reserved.
                                    </td>
                                </tr>
                            </table>
                        </td>
                    </tr>
                </table>
            </body>
        </html>
        """
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [user.email],
            fail_silently=False,
            html_message=html_message,
        )
        return Response({
            'message': 'Registration successful. Please check your email to verify your account.'
        }, status=status.HTTP_201_CREATED)

@extend_schema(tags=["Registration"])
class EmailVerifyView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request, uidb64, token):
        try:
            user_id = force_str(urlsafe_base64_decode(uidb64))
            user = User.objects.get(pk=user_id)
            if not default_token_generator.check_token(user, token):
                return Response(
                    {'detail': 'This verification link has expired or is invalid.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            if not user.is_active:
                user.is_active = True
                user.save()
            refresh = RefreshToken.for_user(user)
            return Response({
                'detail': 'Email verified successfully!',
                'access': str(refresh.access_token),
                'refresh': str(refresh),
                'user': UserProfileSerializer(user).data
            }, status=status.HTTP_200_OK)
        except Exception as e:
            return Response(
                {'detail': f'Invalid verification link. Reason: {str(e)}'},
                status=status.HTTP_400_BAD_REQUEST
            )

@extend_schema(tags=["Login & Logout"])
class UserLoginView(TokenObtainPairView):
    serializer_class = UserLoginSerializer
    permission_classes = [permissions.AllowAny]
    
    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']
        refresh = RefreshToken.for_user(user)
        return Response({
            'user': UserProfileSerializer(user).data,
            'refresh': str(refresh),
            'access': str(refresh.access_token),
            'message': 'Login successful'
        }, status=status.HTTP_200_OK)

@extend_schema_view(
    get=extend_schema(tags=["User Profile"]),
    put=extend_schema(tags=["User Profile"]),
    patch=extend_schema(tags=["User Profile"])
)
class UserProfileView(generics.RetrieveUpdateAPIView):
    permission_classes = [permissions.IsAuthenticated]
    
    def get_object(self):
        return self.request.user

    def get_serializer_class(self):
        if self.request.method == 'GET':
            return UserProfileSerializer
        return UserProfileUpdateSerializer

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)

        return Response({"message": "Profile updated successfully"}, status=status.HTTP_200_OK)

@extend_schema(tags=["Password Management"])
class PasswordResetView(APIView):
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        serializer = PasswordResetSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data['email']
        try:
            user = User.objects.get(email=email)
            token = default_token_generator.make_token(user)
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            reset_link = f"{settings.FRONTEND_URL}/users/verify?uid={uid}&token={token}/"
            subject = 'Password Reset Request'
            message = f"""
            Hello {user.username},
            
            You have requested to reset your password. Please click the link below to reset your password:
            
            {reset_link}
            
            If you did not request this, please ignore this email.
            
            Best regards,
            Optimal Performance Team
            """
            send_mail(
                subject,
                message,
                settings.DEFAULT_FROM_EMAIL,
                [email],
                fail_silently=False,
            )
        except User.DoesNotExist:
            pass
        return Response({'message': 'If the email exists, a reset link has been sent'}, status=status.HTTP_200_OK)

@extend_schema(tags=["Password Management"])
class PasswordResetConfirmView(APIView):
    permission_classes = [permissions.AllowAny]
    
    def post(self, request, uid, token):
        try:
            user_id = force_str(urlsafe_base64_decode(uid))
            user = User.objects.get(pk=user_id)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            return Response({'error': 'Invalid reset link'}, status=status.HTTP_400_BAD_REQUEST)
        
        if not default_token_generator.check_token(user, token):
            return Response({'error': 'Invalid or expired token'}, status=status.HTTP_400_BAD_REQUEST)
        
        serializer = PasswordResetConfirmSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user.set_password(serializer.validated_data['new_password'])
        user.save()
        return Response({'message': 'Password reset successful'}, status=status.HTTP_200_OK)

@extend_schema(tags=["Social Login"])
class GoogleLoginView(APIView):
    permission_classes = [permissions.AllowAny]
    
    def post(self, request, *args, **kwargs):
        try:
            # Get the access token from the request
            access_token = request.data.get('access_token')
            if not access_token:
                return Response(
                    {'error': 'Access token is required'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            print(f"Received access token: {access_token}")
            
            # Verify the token with Google and get user info
            google_user_info = self.get_google_user_info(access_token)
            if not google_user_info:
                return Response(
                    {'error': 'Invalid or expired Google access token'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            print(f"Google user info: {google_user_info}")
            
            # Extract user data
            email = google_user_info.get('email')
            google_id = google_user_info.get('id')
            name = google_user_info.get('name', '')
            
            if not email:
                return Response(
                    {'error': 'Email not provided by Google'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            user = None
            created = False
            
            # Check if user exists with this email
            try:
                user = User.objects.get(email=email)
                print(f"Found existing user: {user.email}")
            except User.DoesNotExist:
                # Create new user
                print(f"Creating new user with email: {email}")
                
                # Generate unique username from email
                username = email.split('@')[0]
                original_username = username
                counter = 1
                while User.objects.filter(username=username).exists():
                    username = f"{original_username}{counter}"
                    counter += 1
                
                user = User.objects.create_user(
                    username=username,
                    email=email,
                    name=name,
                    is_active=True
                )
                created = True
                print(f"Created new user: {user.email}")
            
            # Create or update social account
            social_account, social_created = SocialAccount.objects.get_or_create(
                user=user,
                provider='google',
                defaults={
                    'uid': google_id,
                    'extra_data': google_user_info
                }
            )
            
            if not social_created:
                # Update existing social account data
                social_account.uid = google_id
                social_account.extra_data = google_user_info
                social_account.save()
                print(f"Updated existing social account for user: {user.email}")
            else:
                print(f"Created new social account for user: {user.email}")
            
            # Update user name if it's empty and we have one from Google
            if not user.name and name:
                user.name = name
                user.save()
            
            # Generate JWT tokens
            refresh = RefreshToken.for_user(user)
            
            return Response({
                'user': UserProfileSerializer(user).data,
                'refresh': str(refresh),
                'access': str(refresh.access_token),
                'message': 'Google login successful',
                'created': created
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            print(f"Google login failed with exception: {e}")
            import traceback
            traceback.print_exc()
            return Response(
                {'error': f'Google login failed: {str(e)}'},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    def get_google_user_info(self, access_token):
        """Fetch user info from Google using the access token"""
        try:
            headers = {'Authorization': f'Bearer {access_token}'}
            response = requests.get(
                'https://www.googleapis.com/oauth2/v2/userinfo',
                headers=headers,
                timeout=10
            )
            
            print(f"Google API response status: {response.status_code}")
            print(f"Google API response: {response.text}")
            
            response.raise_for_status()
            user_info = response.json()
            
            # Validate required fields
            if not user_info.get('email'):
                print("Google user info missing email")
                return None
                
            return user_info
            
        except requests.RequestException as e:
            print(f"Error fetching Google user info: {e}")
            return None

@extend_schema(tags=["Login & Logout"])
@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def logout_view(request):
    try:
        refresh_token = request.data.get('refresh_token')
    
        if refresh_token:
            token = RefreshToken(refresh_token)
            token.blacklist()
        return Response({'message': 'Logout successful'}, status=status.HTTP_200_OK)
    except Exception:
        return Response({'error': 'Invalid token'}, status=status.HTTP_400_BAD_REQUEST)