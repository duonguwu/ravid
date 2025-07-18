import os
import uuid
import pandas as pd
import numpy as np

from celery import shared_task
from django.utils import timezone
from django.conf import settings
from .models import CSVFile, TaskResult


@shared_task(bind=True)
def process_csv_dedup(self, task_id, file_id):
    """Remove duplicate rows from CSV file"""
    try:
        # Update task status to PROGRESS
        task = TaskResult.objects.get(task_id=task_id)
        task.status = 'PROGRESS'
        task.started_at = timezone.now()
        task.save()

        # Load CSV file
        csv_file = CSVFile.objects.get(id=file_id)
        df = pd.read_csv(csv_file.file_path.path)
        df = df.replace([np.inf, -np.inf], np.nan)

        # Remove duplicates
        original_rows = len(df)
        df_dedup = df.drop_duplicates()
        processed_rows = len(df_dedup)

        # Create output directory if not exists
        output_dir = os.path.join(settings.MEDIA_ROOT, 'processed_csv')
        os.makedirs(output_dir, exist_ok=True)

        # Save result file
        output_filename = f"{uuid.uuid4()}_dedup.csv"
        output_path = os.path.join(output_dir, output_filename)
        df_dedup.to_csv(output_path, index=False)

        # Update task result
        task.status = 'SUCCESS'
        task.processed_rows = processed_rows
        task.original_rows = original_rows
        task.result_file_path = f'processed_csv/{output_filename}'
        task.completed_at = timezone.now()
        task.save()

        return (f"Deduplication completed: "
                f"{processed_rows}/{original_rows} rows")

    except Exception as exc:
        # Update task with error
        task = TaskResult.objects.get(task_id=task_id)
        task.status = 'FAILURE'
        task.error_message = str(exc)
        task.completed_at = timezone.now()
        task.save()
        raise


@shared_task(bind=True)
def process_csv_unique(self, task_id, file_id, column_name):
    """Extract unique values from specific column"""
    try:
        # Update task status to PROGRESS
        task = TaskResult.objects.get(task_id=task_id)
        task.status = 'PROGRESS'
        task.started_at = timezone.now()
        task.save()

        # Load CSV file
        csv_file = CSVFile.objects.get(id=file_id)
        df = pd.read_csv(csv_file.file_path.path)
        df = df.replace([np.inf, -np.inf], np.nan)

        # Validate column exists
        if column_name not in df.columns:
            raise ValueError(f"Column '{column_name}' not found in CSV file")

        # Extract unique values and create unique rows
        original_rows = len(df)
        unique_values = df[column_name].unique()
        df_unique = df.drop_duplicates(subset=[column_name])
        processed_rows = len(df_unique)

        # Create output directory if not exists
        output_dir = os.path.join(settings.MEDIA_ROOT, 'processed_csv')
        os.makedirs(output_dir, exist_ok=True)

        # Save result file
        output_filename = f"{uuid.uuid4()}_unique_{column_name}.csv"
        output_path = os.path.join(output_dir, output_filename)
        df_unique.to_csv(output_path, index=False)

        # Store operation metadata
        task.operation_params = {
            'column': column_name,
            'unique_count': len(unique_values),
            'unique_values_sample': [str(val) for val in unique_values[:10]]
        }

        # Update task result
        task.status = 'SUCCESS'
        task.processed_rows = processed_rows
        task.original_rows = original_rows
        task.result_file_path = f'processed_csv/{output_filename}'
        task.completed_at = timezone.now()
        task.save()

        return (f"Unique extraction completed: {processed_rows} "
                f"unique rows from column '{column_name}'")

    except Exception as exc:
        # Update task with error
        task = TaskResult.objects.get(task_id=task_id)
        task.status = 'FAILURE'
        task.error_message = str(exc)
        task.completed_at = timezone.now()
        task.save()
        raise


@shared_task(bind=True)
def process_csv_filter(self, task_id, file_id, filter_conditions):
    """Filter CSV data based on conditions"""
    try:
        # Update task status to PROGRESS
        task = TaskResult.objects.get(task_id=task_id)
        task.status = 'PROGRESS'
        task.started_at = timezone.now()
        task.save()

        # Load CSV file
        csv_file = CSVFile.objects.get(id=file_id)
        df = pd.read_csv(csv_file.file_path.path)
        df = df.replace([np.inf, -np.inf], np.nan)

        original_rows = len(df)
        filtered_df = df.copy()

        # Apply filters
        for condition in filter_conditions:
            column = condition['column']
            operator = condition['operator']
            value = condition['value']

            if column not in df.columns:
                raise ValueError(f"Column '{column}' not found in CSV file")
            else:
                dtype = df[column].dtype
                if pd.api.types.is_numeric_dtype(dtype):
                    try:
                        value = float(value)
                    except Exception:
                        raise ValueError(f"Value '{value}' for column '{column}' must be a number.")
                elif pd.api.types.is_datetime64_any_dtype(dtype):
                    value = pd.to_datetime(value)
            # Apply filter based on operator
            if operator == '>':
                filtered_df = filtered_df[filtered_df[column] > value]
            elif operator == '>=':
                filtered_df = filtered_df[filtered_df[column] >= value]
            elif operator == '<':
                filtered_df = filtered_df[filtered_df[column] < value]
            elif operator == '<=':
                filtered_df = filtered_df[filtered_df[column] <= value]
            elif operator == '==':
                filtered_df = filtered_df[filtered_df[column] == value]
            elif operator == '!=':
                filtered_df = filtered_df[filtered_df[column] != value]
            elif operator == 'contains':
                filtered_df = filtered_df[filtered_df[column].astype(str).str.contains(str(value), na=False)]
            elif operator == 'not_contains':
                filtered_df = filtered_df[~filtered_df[column].astype(str).str.contains(str(value), na=False)]
            else:
                raise ValueError(f"Unsupported operator: {operator}")

        processed_rows = len(filtered_df)

        # Create output directory if not exists
        output_dir = os.path.join(settings.MEDIA_ROOT, 'processed_csv')
        os.makedirs(output_dir, exist_ok=True)

        # Save result file
        output_filename = f"{uuid.uuid4()}_filtered.csv"
        output_path = os.path.join(output_dir, output_filename)
        filtered_df.to_csv(output_path, index=False)

        # Store filter metadata
        task.operation_params = {
            'filters_applied': filter_conditions,
            'filter_count': len(filter_conditions)
        }

        # Update task result
        task.status = 'SUCCESS'
        task.processed_rows = processed_rows
        task.original_rows = original_rows
        task.result_file_path = f'processed_csv/{output_filename}'
        task.completed_at = timezone.now()
        task.save()

        return f"Filter completed: {processed_rows}/{original_rows} rows match conditions"

    except Exception as exc:
        # Update task with error
        task = TaskResult.objects.get(task_id=task_id)
        task.status = 'FAILURE'
        task.error_message = str(exc)
        task.completed_at = timezone.now()
        task.save()
        raise
