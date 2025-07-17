# Generated migration file

from django.db import migrations, models
import django.contrib.auth.models
import django.utils.timezone
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('auth', '0012_alter_user_first_name_max_length'),
    ]

    operations = [
        migrations.CreateModel(
            name='User',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('password', models.CharField(max_length=128, verbose_name='password')),
                ('last_login', models.DateTimeField(blank=True, null=True, verbose_name='last login')),
                ('is_superuser', models.BooleanField(default=False, help_text='Designates that this user has all permissions without explicitly assigning them.', verbose_name='superuser status')),
                ('email', models.EmailField(max_length=255, unique=True)),
                ('is_active', models.BooleanField(default=True)),
                ('is_staff', models.BooleanField(default=False)),
                ('date_joined', models.DateTimeField(default=django.utils.timezone.now)),
                ('groups', models.ManyToManyField(blank=True, help_text='The groups this user belongs to. A user will get all permissions granted to each of their groups.', related_name='user_set', related_query_name='user', to='auth.group', verbose_name='groups')),
                ('user_permissions', models.ManyToManyField(blank=True, help_text='Specific permissions for this user.', related_name='user_set', related_query_name='user', to='auth.permission', verbose_name='user permissions')),
            ],
            options={
                'verbose_name': 'User',
                'verbose_name_plural': 'Users',
                'db_table': 'auth_user',
            },
            managers=[
                ('objects', django.contrib.auth.models.UserManager()),
            ],
        ),
        migrations.CreateModel(
            name='CSVFile',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('original_name', models.CharField(max_length=255)),
                ('file_path', models.FileField(upload_to='csv_files/%Y/%m/%d/')),
                ('file_size', models.PositiveIntegerField()),
                ('upload_date', models.DateTimeField(auto_now_add=True)),
                ('is_processed', models.BooleanField(default=False)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='csv_files', to='csv_app.user')),
            ],
            options={
                'db_table': 'csv_files',
                'ordering': ['-upload_date'],
            },
        ),
        migrations.CreateModel(
            name='TaskResult',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('task_id', models.CharField(max_length=255, unique=True)),
                ('operation', models.CharField(choices=[('dedup', 'Deduplication'), ('unique', 'Unique Values'), ('filter', 'Filter Data')], max_length=10)),
                ('status', models.CharField(choices=[('PENDING', 'Pending'), ('PROGRESS', 'In Progress'), ('SUCCESS', 'Success'), ('FAILURE', 'Failed'), ('RETRY', 'Retrying')], default='PENDING', max_length=10)),
                ('operation_params', models.JSONField(blank=True, default=dict)),
                ('result_file_path', models.FileField(blank=True, null=True, upload_to='processed_csv/%Y/%m/%d/')),
                ('processed_rows', models.PositiveIntegerField(blank=True, null=True)),
                ('original_rows', models.PositiveIntegerField(blank=True, null=True)),
                ('error_message', models.TextField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('started_at', models.DateTimeField(blank=True, null=True)),
                ('completed_at', models.DateTimeField(blank=True, null=True)),
                ('csv_file', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='tasks', to='csv_app.csvfile')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='tasks', to='csv_app.user')),
            ],
            options={
                'db_table': 'task_results',
                'ordering': ['-created_at'],
            },
        ),
    ]
