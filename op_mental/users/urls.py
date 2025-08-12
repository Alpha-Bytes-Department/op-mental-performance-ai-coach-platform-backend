from django.urls import path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView, TokenVerifyView
from . import views

app_name = 'users'

urlpatterns = [
    path('register/', views.UserRegistrationView.as_view(), name='register'),
    path('login/', views.UserLoginView.as_view(), name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('token/verify/', TokenVerifyView.as_view(), name='token_verify'),
    path('profile/', views.UserProfileView.as_view(), name='profile'),
    path('password/reset/', views.PasswordResetView.as_view(), name='password_reset'),
    path('password/reset/confirm/<str:uid>/<str:token>/', views.PasswordResetConfirmView.as_view(), name='password_reset_confirm'),
    path('auth/google/', views.GoogleLoginView.as_view(), name='google_login'),
    path('email/verify/<str:uidb64>/<str:token>/', views.EmailVerifyView.as_view(), name='email_verify'),
]
