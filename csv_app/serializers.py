from rest_framework import serializers
from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from .models import User, CSVFile, TaskResult
import re


class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(
        write_only=True,
        min_length=8,
        style={'input_type': 'password'}
    )

    class Meta:
        model = User
        fields = ('email', 'password')

    def validate_email(self, value):
        email_regex = r'^[\w\-\.]+@([\w\-]+\.)+[\w\-]{2,4}$'
        if not re.match(email_regex, value):
            raise serializers.ValidationError("Invalid email format")

        # Check if email already exists
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("Email already exists")

        return value.lower()

    def validate_password(self, value):
        try:
            validate_password(value)
        except ValidationError as e:
            raise serializers.ValidationError(list(e.messages))
        return value

    def create(self, validated_data):
        user = User.objects.create_user(
            email=validated_data['email'],
            password=validated_data['password'],
        )
        return user


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(
        style={'input_type': 'password'},
        trim_whitespace=False
    )

    def validate_email(self, value):
        email_regex = r'^[\w\-\.]+@([\w\-]+\.)+[\w\-]{2,4}$'
        if not re.match(email_regex, value):
            raise serializers.ValidationError("Invalid email format")
        return value.lower()

    def validate(self, attrs):
        email = attrs.get('email')
        password = attrs.get('password')

        if email and password:
            user = authenticate(
                request=self.context.get('request'),
                username=email,
                password=password
            )

            if not user:
                raise serializers.ValidationError(
                    "Invalid email or password",
                    code='authorization'
                )

            if not user.is_active:
                raise serializers.ValidationError(
                    "User account is disabled",
                    code='authorization'
                )

            attrs['user'] = user
            return attrs
        else:
            raise serializers.ValidationError(
                "Must include email and password",
                code='authorization'
            )

