from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from . import views

app_name = 'csv_app'

urlpatterns = [
    # Authentication endpoints
    path('api/register/', views.RegisterView.as_view(), name='register'),
    path('api/login/', views.LoginView.as_view(), name='login'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),

]
