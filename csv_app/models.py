from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.db import models
from django.utils import timezone
from django.contrib.auth.base_user import BaseUserManager
import re


class UserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('Email is required')

        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self.create_user(email, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(unique=True, max_length=255)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    date_joined = models.DateTimeField(default=timezone.now)

    objects = UserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    class Meta:
        db_table = 'auth_user'
        verbose_name = 'User'
        verbose_name_plural = 'Users'

    def __str__(self):
        return self.email


class CSVFile(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='csv_files')
    original_name = models.CharField(max_length=255)
    file_path = models.FileField(upload_to='csv_files/%Y/%m/%d/')
    file_size = models.PositiveIntegerField()  # in bytes
    upload_date = models.DateTimeField(auto_now_add=True)
    is_processed = models.BooleanField(default=False)

    class Meta:
        db_table = 'csv_files'
        ordering = ['-upload_date']

    def __str__(self):
        return f"{self.original_name} - {self.user.email}"


class TaskResult(models.Model):
    OPERATION_CHOICES = [
        ('dedup', 'Deduplication'),
        ('unique', 'Unique Values'),
        ('filter', 'Filter Data'),
    ]

    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('PROGRESS', 'In Progress'),
        ('SUCCESS', 'Success'),
        ('FAILURE', 'Failed'),
        ('RETRY', 'Retrying'),
    ]

    task_id = models.CharField(max_length=255, unique=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='tasks')
    csv_file = models.ForeignKey(CSVFile, on_delete=models.CASCADE, related_name='tasks')
    operation = models.CharField(max_length=10, choices=OPERATION_CHOICES)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='PENDING')

    # Operation parameters
    operation_params = models.JSONField(default=dict, blank=True)

    # Results
    result_file_path = models.FileField(upload_to='processed_csv/%Y/%m/%d/', null=True, blank=True)
    processed_rows = models.PositiveIntegerField(null=True, blank=True)
    original_rows = models.PositiveIntegerField(null=True, blank=True)
    error_message = models.TextField(blank=True, null=True)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'task_results'
        ordering = ['-created_at']

    def __str__(self):
        return f"Task {self.task_id} - {self.operation} - {self.status}"
