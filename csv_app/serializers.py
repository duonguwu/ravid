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
    confirm_password = serializers.CharField(
        write_only=True,
        min_length=8,
        style={'input_type': 'password'}
    )

    class Meta:
        model = User
        fields = ('email', 'password', 'confirm_password')

    def validate_email(self, value):
        email_regex = r'^[\w\-\.]+@([\w\-]+\.)+[\w\-]{2,4}$'
        if not re.match(email_regex, value):
            raise serializers.ValidationError("Invalid email format")
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("Email already exists")
        return value.lower()

    def validate(self, attrs):
        password = attrs.get('password')
        confirm_password = attrs.get('confirm_password')
        if password != confirm_password:
            raise serializers.ValidationError({
                'confirm_password': "Password and confirm password do not match"
            })
        return attrs

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


class CSVFileUploadSerializer(serializers.ModelSerializer):
    file = serializers.FileField()

    class Meta:
        model = CSVFile
        fields = ('file',)

    def validate_file(self, value):
        if not value.name.endswith('.csv'):
            raise serializers.ValidationError(
                "Invalid file format. Only CSV files are allowed."
            )

        return value

    def create(self, validated_data):
        file = validated_data['file']
        user = self.context['request'].user

        csv_file = CSVFile.objects.create(
            user=user,
            original_name=file.name,
            file_path=file,
            file_size=file.size
        )
        return csv_file


class OperationRequestSerializer(serializers.Serializer):
    OPERATION_CHOICES = [
        ('dedup', 'Deduplication'),
        ('unique', 'Unique Values'),
        ('filter', 'Filter Data'),
    ]

    file_id = serializers.IntegerField()
    operation = serializers.ChoiceField(choices=OPERATION_CHOICES)

    # Optional parameters for different operations
    column = serializers.CharField(required=False, allow_blank=True)
    filters = serializers.JSONField(required=False, default=list)

    def validate_file_id(self, value):
        """Validate file exists and belongs to user"""
        user = self.context['request'].user
        try:
            CSVFile.objects.get(id=value, user=user)
        except CSVFile.DoesNotExist:
            raise serializers.ValidationError(
                "File not found or access denied"
            )
        return value

    def validate(self, attrs):
        """Validate operation-specific parameters"""
        operation = attrs.get('operation')

        if operation == 'unique':
            if not attrs.get('column'):
                raise serializers.ValidationError(
                    "Column name is required for unique operation"
                )

        elif operation == 'filter':
            filters = attrs.get('filters', [])
            if not filters:
                raise serializers.ValidationError(
                    "Filter conditions are required for filter operation"
                )

            for filter_item in filters:
                if not isinstance(filter_item, dict):
                    raise serializers.ValidationError(
                        "Each filter must be an object"
                    )

                required_fields = ['column', 'operator', 'value']
                for field in required_fields:
                    if field not in filter_item:
                        raise serializers.ValidationError(
                            f"Filter missing required field: {field}"
                        )

                # Validate operator
                valid_operators = [
                    '>', '>=', '<', '<=', '==', '!=', 'contains',
                    'not_contains'
                ]
                if filter_item['operator'] not in valid_operators:
                    raise serializers.ValidationError(
                        f"Invalid operator: {filter_item['operator']}"
                    )

        return attrs


class TaskStatusSerializer(serializers.ModelSerializer):
    file_link = serializers.SerializerMethodField()

    class Meta:
        model = TaskResult
        fields = (
            'task_id', 'status', 'operation', 'processed_rows', 
            'original_rows', 'error_message', 'file_link',
            'created_at', 'completed_at'
        )

    def get_file_link(self, obj):
        """Generate download link for processed file"""
        if obj.result_file_path and obj.status == 'SUCCESS':
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.result_file_path.url)
        return None 