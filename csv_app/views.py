from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from .serializers import UserRegistrationSerializer, LoginSerializer


class RegisterView(APIView):
    permission_classes = [AllowAny]

    @swagger_auto_schema(
        operation_description="Register a new user",
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
                    description='User password (min 8 characters)'
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

