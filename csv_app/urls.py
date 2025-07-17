from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from . import views

app_name = 'csv_app'

urlpatterns = [
    # Authentication endpoints
    path('api/register/', views.RegisterView.as_view(), name='register'),
    path('api/login/', views.LoginView.as_view(), name='login'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),

    # CSV endpoints (placeholders for now)
    path('api/upload-csv/', views.CSVUploadView.as_view(), name='upload_csv'),
    path('api/perform-operation/', views.PerformOperationView.as_view(), name='perform_operation'),
    path('api/task-status/', views.TaskStatusView.as_view(), name='task_status'),
]
