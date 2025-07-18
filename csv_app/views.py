from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.generics import CreateAPIView
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework_simplejwt.tokens import RefreshToken
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
import uuid
import pandas as pd
from .serializers import (
    UserRegistrationSerializer,
    LoginSerializer,
    CSVFileUploadSerializer,
    OperationRequestSerializer,
    TaskStatusSerializer
)
from .models import CSVFile, TaskResult
from .tasks import process_csv_dedup, process_csv_unique, process_csv_filter


class RegisterView(APIView):
    permission_classes = [AllowAny]

    @swagger_auto_schema(
        operation_description="Register a new user",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['email', 'password', 'confirm_password'],
            properties={
                'email': openapi.Schema(
                    type=openapi.TYPE_STRING,
                    format=openapi.FORMAT_EMAIL,
                    description='User email address'
                ),
                'password': openapi.Schema(
                    type=openapi.TYPE_STRING,
                    format=openapi.FORMAT_PASSWORD,
                    description='User password (min 8 characters)'
                ),
                'confirm_password': openapi.Schema(
                    type=openapi.TYPE_STRING,
                    format=openapi.FORMAT_PASSWORD,
                    description='Confirm password (must match password)'
                ),
            }
        ),
        responses={
            201: openapi.Response(
                description="Registration successful",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'message': openapi.Schema(
                            type=openapi.TYPE_STRING,
                            example='Registration successful'
                        ),
                        'user_id': openapi.Schema(
                            type=openapi.TYPE_INTEGER,
                            example=1
                        )
                    }
                )
            ),
            400: openapi.Response(
                description="Registration failed",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'error': openapi.Schema(
                            type=openapi.TYPE_STRING,
                            example='Email already exists'
                        ),
                        'confirm_password': openapi.Schema(
                            type=openapi.TYPE_STRING,
                            example='Password and confirm password do not match'
                        )
                    }
                )
            )
        },
        consumes=['application/x-www-form-urlencoded', 'application/json']
    )
    def post(self, request):
        """Register a new user"""
        serializer = UserRegistrationSerializer(data=request.data)

        if serializer.is_valid():
            user = serializer.save()
            return Response({
                'message': 'Registration successful',
                'user_id': user.id
            }, status=status.HTTP_201_CREATED)

        # Return first error message
        errors = serializer.errors
        if 'email' in errors:
            error_msg = errors['email'][0]
        elif 'password' in errors:
            error_msg = errors['password'][0]
        elif 'confirm_password' in errors:
            error_msg = errors['confirm_password'][0]
        else:
            error_msg = 'Registration failed'

        return Response({
            'error': error_msg
        }, status=status.HTTP_400_BAD_REQUEST)


class LoginView(APIView):
    permission_classes = [AllowAny]

    @swagger_auto_schema(
        operation_description="Login user and get JWT tokens",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['email', 'password'],
            properties={
                'email': openapi.Schema(
                    type=openapi.TYPE_STRING,
                    format=openapi.FORMAT_EMAIL,
                    description='User email address'
                ),
                'password': openapi.Schema(
                    type=openapi.TYPE_STRING,
                    format=openapi.FORMAT_PASSWORD,
                    description='User password'
                ),
            }
        ),
        responses={
            200: openapi.Response(
                description="Login successful",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'message': openapi.Schema(
                            type=openapi.TYPE_STRING,
                            example='Login successful'
                        ),
                        'access_token': openapi.Schema(
                            type=openapi.TYPE_STRING,
                            example='eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...'
                        ),
                        'refresh_token': openapi.Schema(
                            type=openapi.TYPE_STRING,
                            example='eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...'
                        )
                    }
                )
            ),
            401: openapi.Response(
                description="Login failed",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'error': openapi.Schema(
                            type=openapi.TYPE_STRING,
                            example='Invalid email or password'
                        )
                    }
                )
            )
        },
        consumes=['application/x-www-form-urlencoded', 'application/json']
    )
    def post(self, request):
        """Login user and return JWT tokens"""
        serializer = LoginSerializer(
            data=request.data,
            context={'request': request}
        )

        if serializer.is_valid():
            user = serializer.validated_data['user']

            # Generate JWT tokens
            refresh = RefreshToken.for_user(user)
            access_token = refresh.access_token

            return Response({
                'message': 'Login successful',
                'access_token': str(access_token),
                'refresh_token': str(refresh)
            }, status=status.HTTP_200_OK)

        # Return error message
        errors = serializer.errors
        if 'non_field_errors' in errors:
            error_msg = errors['non_field_errors'][0]
        elif 'email' in errors:
            error_msg = errors['email'][0]
        else:
            error_msg = 'Invalid email or password'

        return Response({
            'error': error_msg
        }, status=status.HTTP_401_UNAUTHORIZED)


class CSVUploadView(CreateAPIView):
    serializer_class = CSVFileUploadSerializer
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    @swagger_auto_schema(
        operation_description="Upload a CSV file for processing",
        manual_parameters=[
            openapi.Parameter(
                'Authorization',
                openapi.IN_HEADER,
                description="Bearer <JWT_ACCESS_TOKEN>",
                type=openapi.TYPE_STRING,
                required=True,
                example="Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
            ),
            openapi.Parameter(
                'file',
                openapi.IN_FORM,
                description="CSV file to upload",
                type=openapi.TYPE_FILE,
                required=True
            )
        ],
        responses={
            201: openapi.Response(
                description="File uploaded successfully",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'message': openapi.Schema(
                            type=openapi.TYPE_STRING,
                            example='File uploaded successfully'
                        ),
                        'file_id': openapi.Schema(
                            type=openapi.TYPE_INTEGER,
                            example=1,
                            description='ID of uploaded file'
                        )
                    }
                )
            ),
            400: openapi.Response(
                description="Upload failed",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'error': openapi.Schema(
                            type=openapi.TYPE_STRING,
                            example='Invalid file format. CSV only.'
                        )
                    }
                )
            ),
            401: openapi.Response(
                description="Authentication required",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'detail': openapi.Schema(
                            type=openapi.TYPE_STRING,
                            example='Authentication required.'
                        )
                    }
                )
            )
        },
        consumes=['multipart/form-data']
    )
    def post(self, request, *args, **kwargs):
        if 'file' not in request.data:
            return Response({
                'error': 'No file provided'
            }, status=status.HTTP_400_BAD_REQUEST)

        # Use serializer to validate and create
        serializer = self.get_serializer(data=request.data)

        if serializer.is_valid():
            csv_file = serializer.save()

            return Response({
                'message': 'File uploaded successfully',
                'file_id': csv_file.id
            }, status=status.HTTP_201_CREATED)

        # Handle validation errors
        errors = serializer.errors
        if 'file' in errors:
            error_msg = errors['file'][0]
        else:
            error_msg = 'File upload failed'

        return Response({
            'error': error_msg
        }, status=status.HTTP_400_BAD_REQUEST)


class PerformOperationView(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_description="Perform CSV operation (dedup/unique/filter)",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['file_id', 'operation'],
            properties={
                'file_id': openapi.Schema(
                    type=openapi.TYPE_INTEGER,
                    description='ID of uploaded CSV file'
                ),
                'operation': openapi.Schema(
                    type=openapi.TYPE_STRING,
                    enum=['dedup', 'unique', 'filter'],
                    description='Type of operation to perform'
                ),
                'column': openapi.Schema(
                    type=openapi.TYPE_STRING,
                    description='Column name (required for unique operation)'
                ),
                'filters': openapi.Schema(
                    type=openapi.TYPE_ARRAY,
                    items=openapi.Schema(
                        type=openapi.TYPE_OBJECT,
                        properties={
                            'column': openapi.Schema(type=openapi.TYPE_STRING),
                            'operator': openapi.Schema(
                                type=openapi.TYPE_STRING,
                                enum=['>', '>=', '<', '<=', '==', '!=', 'contains', 'not_contains']
                            ),
                            'value': openapi.Schema(type=openapi.TYPE_STRING)
                        }
                    ),
                    description='Filter conditions (required for filter operation)'
                )
            }
        ),
        responses={
            201: openapi.Response(
                description="Operation started",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'message': openapi.Schema(
                            type=openapi.TYPE_STRING,
                            example='Operation started'
                        ),
                        'task_id': openapi.Schema(
                            type=openapi.TYPE_STRING,
                            example='abc123-def456-ghi789'
                        )
                    }
                )
            ),
            400: openapi.Response(
                description="Invalid request",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'error': openapi.Schema(
                            type=openapi.TYPE_STRING,
                            example='Invalid operation or file not found.'
                        )
                    }
                )
            )
        }
    )
    def post(self, request):
        """Perform CSV operation (dedup/unique/filter)"""
        serializer = OperationRequestSerializer(
            data=request.data,
            context={'request': request}
        )

        if serializer.is_valid():
            file_id = serializer.validated_data['file_id']
            operation = serializer.validated_data['operation']

            # Generate unique task ID
            task_id = str(uuid.uuid4())

            # Create TaskResult record
            task_result = TaskResult.objects.create(
                task_id=task_id,
                user=request.user,
                csv_file_id=file_id,
                operation=operation,
                status='PENDING',
                operation_params=serializer.validated_data
            )

            try:
                if operation == 'dedup':
                    process_csv_dedup.delay(task_id, file_id)

                elif operation == 'unique':
                    column = serializer.validated_data.get('column')
                    process_csv_unique.delay(task_id, file_id, column)

                elif operation == 'filter':
                    filters = serializer.validated_data.get('filters', [])
                    process_csv_filter.delay(task_id, file_id, filters)

                return Response({
                    'message': 'Operation started',
                    'task_id': task_id
                }, status=status.HTTP_201_CREATED)

            except Exception as e:
                # Update task status to failed
                task_result.status = 'FAILURE'
                task_result.error_message = str(e)
                task_result.save()

                return Response({
                    'error': 'Failed to start operation'
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        # Handle validation errors
        errors = serializer.errors
        if 'file_id' in errors:
            error_msg = errors['file_id'][0]
        elif 'operation' in errors:
            error_msg = errors['operation'][0]
        else:
            error_msg = 'Invalid operation or file not found.'

        return Response({
            'error': error_msg
        }, status=status.HTTP_400_BAD_REQUEST)


class TaskStatusView(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_description="Get task status and results",
        manual_parameters=[
            openapi.Parameter(
                'task_id',
                openapi.IN_QUERY,
                description="Task ID to check status",
                type=openapi.TYPE_STRING,
                required=True,
                example="abc123-def456-ghi789"
            ),
            openapi.Parameter(
                'n',
                openapi.IN_QUERY,
                description="Number of records to return (default: 100)",
                type=openapi.TYPE_INTEGER,
                required=False,
                example=50
            )
        ],
        responses={
            200: openapi.Response(
                description="Task status retrieved",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'task_id': openapi.Schema(type=openapi.TYPE_STRING),
                        'status': openapi.Schema(
                            type=openapi.TYPE_STRING,
                            enum=['PENDING', 'PROGRESS', 'SUCCESS', 'FAILURE']
                        ),
                        'result': openapi.Schema(
                            type=openapi.TYPE_OBJECT,
                            properties={
                                'data': openapi.Schema(
                                    type=openapi.TYPE_ARRAY,
                                    items=openapi.Schema(type=openapi.TYPE_OBJECT)
                                ),
                                'file_link': openapi.Schema(type=openapi.TYPE_STRING)
                            }
                        ),
                        'error': openapi.Schema(type=openapi.TYPE_STRING)
                    }
                )
            ),
            404: openapi.Response(
                description="Task not found",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'error': openapi.Schema(
                            type=openapi.TYPE_STRING,
                            example='Task not found'
                        )
                    }
                )
            )
        }
    )
    def get(self, request):
        """Get task status and results"""
        task_id = request.query_params.get('task_id')
        n = int(request.query_params.get('n', 100))

        if not task_id:
            return Response({
                'error': 'task_id parameter is required'
            }, status=status.HTTP_400_BAD_REQUEST)

        try:
            task = TaskResult.objects.get(
                task_id=task_id, 
                user=request.user
            )
        except TaskResult.DoesNotExist:
            return Response({
                'error': 'Task not found'
            }, status=status.HTTP_404_NOT_FOUND)

        response_data = {
            'task_id': task.task_id,
            'status': task.status
        }

        if task.status == 'SUCCESS' and task.result_file_path:
            try:
                # Read first n rows from result file
                df = pd.read_csv(task.result_file_path.path)
                data_records = df.head(n).to_dict('records')

                # Generate file download link
                file_link = None
                if request:
                    file_link = request.build_absolute_uri(
                        task.result_file_path.url
                    )

                response_data['result'] = {
                    'file_link': file_link,
                    'data': data_records
                }

            except Exception as e:
                response_data['error'] = f"Error reading result file: {str(e)}"

        # If task failed, include error message
        elif task.status == 'FAILURE':
            response_data['error'] = task.error_message

        return Response(response_data, status=status.HTTP_200_OK)
