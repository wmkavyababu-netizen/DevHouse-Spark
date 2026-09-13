"""Initial complete schema migration for TARANG Platform.

Revision ID: 001_initial_schema
Revises: None
Create Date: 2026-09-12 17:00:00.000000

Baseline: TARANG Implementation Guide v6.2 (30-table/view schema)
"""

from typing import Sequence, Union
import json
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from geoalchemy2 import Geography

# revision identifiers, used by Alembic.
revision: str = '001_initial_schema'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # --------------------------------------------------------------------------
    # 0. Enable PostgreSQL & PostGIS Extensions
    # --------------------------------------------------------------------------
    op.execute('CREATE EXTENSION IF NOT EXISTS "uuid-ossp";')
    op.execute('CREATE EXTENSION IF NOT EXISTS "pgcrypto";')
    op.execute('CREATE EXTENSION IF NOT EXISTS "postgis";')

    # --------------------------------------------------------------------------
    # 1. organizations
    # --------------------------------------------------------------------------
    op.create_table(
        'organizations',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('slug', sa.String(length=100), nullable=False),
        sa.Column('org_type', sa.String(length=50), nullable=False),
        sa.Column('status', sa.String(length=50), server_default='active', nullable=False),
        sa.Column('settings', postgresql.JSONB(astext_type=sa.Text()), server_default='{}', nullable=False),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('updated_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('slug', name='uq_organizations_slug'),
        comment='Organizations, maritime authorities, research institutes, and NGOs.',
    )
    op.create_index('idx_organizations_status', 'organizations', ['status'])

    # --------------------------------------------------------------------------
    # 2. roles
    # --------------------------------------------------------------------------
    op.create_table(
        'roles',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('permissions', postgresql.JSONB(astext_type=sa.Text()), server_default='{}', nullable=False),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('updated_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name', name='uq_roles_name'),
        comment='RBAC role definitions and granular JSONB permission matrices.',
    )

    # --------------------------------------------------------------------------
    # 3. users
    # --------------------------------------------------------------------------
    op.create_table(
        'users',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('password_hash', sa.String(length=255), nullable=False),
        sa.Column('full_name', sa.String(length=255), nullable=False),
        sa.Column('status', sa.String(length=50), server_default='active', nullable=False),
        sa.Column('is_verified', sa.Boolean(), server_default='false', nullable=False),
        sa.Column('two_factor_enabled', sa.Boolean(), server_default='false', nullable=False),
        sa.Column('profile', postgresql.JSONB(astext_type=sa.Text()), server_default='{}', nullable=False),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('updated_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('email', name='uq_users_email'),
        comment='Platform user profiles owned and authenticated by Spring Boot identity layer.',
    )
    op.create_index('idx_users_organization_id', 'users', ['organization_id'])
    op.create_index('idx_users_status', 'users', ['status'])

    # --------------------------------------------------------------------------
    # 4. user_roles
    # --------------------------------------------------------------------------
    op.create_table(
        'user_roles',
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('role_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('assigned_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.ForeignKeyConstraint(['role_id'], ['roles.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('user_id', 'role_id'),
        comment='Many-to-many junction mapping users to assigned RBAC roles.',
    )

    # --------------------------------------------------------------------------
    # 5. refresh_tokens
    # --------------------------------------------------------------------------
    op.create_table(
        'refresh_tokens',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('token_hash', sa.String(length=255), nullable=False),
        sa.Column('key_id', sa.String(length=100), nullable=False),
        sa.Column('expires_at', sa.TIMESTAMP(timezone=True), nullable=False),
        sa.Column('revoked_at', sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('token_hash', name='uq_refresh_tokens_token_hash'),
        comment='Hashed refresh token lifecycle management; plaintext tokens never persisted.',
    )
    op.create_index('idx_refresh_tokens_user_id', 'refresh_tokens', ['user_id'])
    op.create_index('idx_refresh_tokens_expires_at', 'refresh_tokens', ['expires_at'])

    # --------------------------------------------------------------------------
    # 6. sonar_devices
    # --------------------------------------------------------------------------
    op.create_table(
        'sonar_devices',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('manufacturer', sa.String(length=100), nullable=True),
        sa.Column('model', sa.String(length=100), nullable=True),
        sa.Column('supported_formats', postgresql.JSONB(astext_type=sa.Text()), server_default='["xtf", "jsf"]', nullable=False),
        sa.Column('operating_frequencies_khz', postgresql.JSONB(astext_type=sa.Text()), server_default='[]', nullable=False),
        sa.Column('default_range_meters', sa.Numeric(precision=8, scale=2), nullable=True),
        sa.Column('calibration_profile', postgresql.JSONB(astext_type=sa.Text()), server_default='{}', nullable=False),
        sa.Column('beam_width_degrees', sa.Numeric(precision=5, scale=2), nullable=True),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('updated_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        comment='Sonar hardware profiles, telemetry specs, and device calibration parameters.',
    )

    # --------------------------------------------------------------------------
    # 7. target_classes
    # --------------------------------------------------------------------------
    op.create_table(
        'target_classes',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('display_name', sa.String(length=150), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('color_hex', sa.String(length=7), server_default='#06b6d4', nullable=False),
        sa.Column('risk_level', sa.String(length=50), server_default='medium', nullable=False),
        sa.Column('is_active', sa.Boolean(), server_default='true', nullable=False),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name', name='uq_target_classes_name'),
        comment='Detection ontology and target classification taxonomy matching model outputs.',
    )

    # --------------------------------------------------------------------------
    # 8. storage_artifacts
    # --------------------------------------------------------------------------
    op.create_table(
        'storage_artifacts',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('artifact_type', sa.String(length=100), nullable=False),
        sa.Column('storage_uri', sa.String(length=1024), nullable=False),
        sa.Column('filename', sa.String(length=255), nullable=False),
        sa.Column('mime_type', sa.String(length=100), nullable=False),
        sa.Column('file_size_bytes', sa.BigInteger(), nullable=False),
        sa.Column('checksum_sha256', sa.String(length=64), nullable=False),
        sa.Column('metadata_json', postgresql.JSONB(astext_type=sa.Text()), server_default='{}', nullable=False),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.CheckConstraint('file_size_bytes >= 0', name='ck_storage_artifacts_size_positive'),
        sa.PrimaryKeyConstraint('id'),
        comment='Registry of large external binary files (sonar raw, processed tiles, masks, reports).',
    )
    op.create_index('idx_storage_artifacts_type', 'storage_artifacts', ['artifact_type'])
    op.create_index('idx_storage_artifacts_checksum', 'storage_artifacts', ['checksum_sha256'])

    # --------------------------------------------------------------------------
    # 9. surveys
    # --------------------------------------------------------------------------
    op.create_table(
        'surveys',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('operator_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('sonar_device_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('mission_code', sa.String(length=100), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('status', sa.String(length=50), server_default='uploaded', nullable=False),
        sa.Column('start_time', sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column('end_time', sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column('survey_area', Geography(geometry_type='POLYGON', srid=4326), nullable=True),
        sa.Column('metadata_json', postgresql.JSONB(astext_type=sa.Text()), server_default='{}', nullable=False),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('updated_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.ForeignKeyConstraint(['operator_id'], ['users.id'], ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['sonar_device_id'], ['sonar_devices.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
        comment='Top-level survey domain record managing SSS acquisition files and jobs.',
    )
    op.create_index('idx_surveys_operator_id', 'surveys', ['operator_id'])
    op.create_index('idx_surveys_organization_id', 'surveys', ['organization_id'])
    op.create_index('idx_surveys_status', 'surveys', ['status'])
    op.execute('CREATE INDEX idx_surveys_survey_area ON surveys USING GIST (survey_area);')

    # --------------------------------------------------------------------------
    # 10. sss_files
    # --------------------------------------------------------------------------
    op.create_table(
        'sss_files',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('survey_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('storage_artifact_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('filename', sa.String(length=255), nullable=False),
        sa.Column('file_format', sa.String(length=50), nullable=False),
        sa.Column('file_size_bytes', sa.BigInteger(), nullable=False),
        sa.Column('channel_count', sa.Integer(), server_default='2', nullable=False),
        sa.Column('sample_rate', sa.Numeric(precision=10, scale=2), nullable=True),
        sa.Column('ping_count', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.CheckConstraint('file_size_bytes >= 0', name='ck_sss_files_size_positive'),
        sa.CheckConstraint('ping_count IS NULL OR ping_count >= 0', name='ck_sss_files_ping_count_positive'),
        sa.ForeignKeyConstraint(['storage_artifact_id'], ['storage_artifacts.id'], ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['survey_id'], ['surveys.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        comment='Uploaded raw side-scan sonar files (XTF, JSF, HSX, SDF) associated with surveys.',
    )
    op.create_index('idx_sss_files_survey_id', 'sss_files', ['survey_id'])
    op.create_index('idx_sss_files_storage_artifact_id', 'sss_files', ['storage_artifact_id'])

    # --------------------------------------------------------------------------
    # 11. survey_frames
    # --------------------------------------------------------------------------
    op.create_table(
        'survey_frames',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('survey_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('sss_file_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('frame_number', sa.Integer(), nullable=False),
        sa.Column('timestamp', sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column('location', Geography(geometry_type='POINT', srid=4326), nullable=True),
        sa.Column('altitude_meters', sa.Numeric(precision=8, scale=2), nullable=True),
        sa.Column('heading_degrees', sa.Numeric(precision=6, scale=2), nullable=True),
        sa.Column('speed_knots', sa.Numeric(precision=6, scale=2), nullable=True),
        sa.Column('raw_image_artifact_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('enhanced_image_artifact_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('shadow_map_artifact_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('quality_score', sa.Numeric(precision=5, scale=2), nullable=True),
        sa.Column('dropout_flags', postgresql.JSONB(astext_type=sa.Text()), server_default='{}', nullable=False),
        sa.Column('metadata_json', postgresql.JSONB(astext_type=sa.Text()), server_default='{}', nullable=False),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.CheckConstraint('frame_number >= 0', name='ck_survey_frames_frame_number_positive'),
        sa.CheckConstraint('heading_degrees IS NULL OR (heading_degrees >= 0 AND heading_degrees <= 360)', name='ck_survey_frames_heading_range'),
        sa.CheckConstraint('speed_knots IS NULL OR speed_knots >= 0', name='ck_survey_frames_speed_positive'),
        sa.CheckConstraint('quality_score IS NULL OR (quality_score >= 0 AND quality_score <= 100)', name='ck_survey_frames_quality_score_range'),
        sa.ForeignKeyConstraint(['enhanced_image_artifact_id'], ['storage_artifacts.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['raw_image_artifact_id'], ['storage_artifacts.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['shadow_map_artifact_id'], ['storage_artifacts.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['sss_file_id'], ['sss_files.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['survey_id'], ['surveys.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('survey_id', 'frame_number', name='uq_survey_frame_number'),
        comment='Individual acoustic scan waterfall frames, navigation telemetry, and quality scores.',
    )
    op.create_index('idx_survey_frames_survey_id', 'survey_frames', ['survey_id'])
    op.execute('CREATE INDEX idx_survey_frames_location ON survey_frames USING GIST (location);')

    # --------------------------------------------------------------------------
    # 12. processing_jobs
    # --------------------------------------------------------------------------
    op.create_table(
        'processing_jobs',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('survey_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('status', sa.String(length=50), server_default='queued', nullable=False),
        sa.Column('progress_percentage', sa.Numeric(precision=5, scale=2), server_default='0.0', nullable=False),
        sa.Column('celery_task_id', sa.String(length=255), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('started_at', sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column('completed_at', sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('updated_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.CheckConstraint('progress_percentage >= 0 AND progress_percentage <= 100', name='ck_processing_jobs_progress_range'),
        sa.ForeignKeyConstraint(['survey_id'], ['surveys.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        comment='High-level Celery workflow jobs orchestrating SSS pipeline execution.',
    )
    op.create_index('idx_processing_jobs_survey_id', 'processing_jobs', ['survey_id'])
    op.create_index('idx_processing_jobs_status', 'processing_jobs', ['status'])

    # --------------------------------------------------------------------------
    # 13. processing_stages
    # --------------------------------------------------------------------------
    op.create_table(
        'processing_stages',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('processing_job_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('stage_name', sa.String(length=100), nullable=False),
        sa.Column('stage_order', sa.Integer(), nullable=False),
        sa.Column('status', sa.String(length=50), server_default='pending', nullable=False),
        sa.Column('progress_percentage', sa.Numeric(precision=5, scale=2), server_default='0.0', nullable=False),
        sa.Column('attempt_count', sa.Integer(), server_default='0', nullable=False),
        sa.Column('retry_count', sa.Integer(), server_default='0', nullable=False),
        sa.Column('execution_log', sa.Text(), nullable=True),
        sa.Column('parameters_used', postgresql.JSONB(astext_type=sa.Text()), server_default='{}', nullable=False),
        sa.Column('started_at', sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column('completed_at', sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('updated_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.CheckConstraint('progress_percentage >= 0 AND progress_percentage <= 100', name='ck_processing_stages_progress_range'),
        sa.CheckConstraint('attempt_count >= 0', name='ck_processing_stages_attempt_count_positive'),
        sa.CheckConstraint('retry_count >= 0', name='ck_processing_stages_retry_count_positive'),
        sa.CheckConstraint('stage_order >= 0', name='ck_processing_stages_order_positive'),
        sa.ForeignKeyConstraint(['processing_job_id'], ['processing_jobs.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('processing_job_id', 'stage_name', name='uq_processing_job_stage'),
        comment='Progress, retries, and execution audit for individual pipeline stages.',
    )
    op.create_index('idx_processing_stages_job_id', 'processing_stages', ['processing_job_id'])
    op.create_index('idx_processing_stages_status', 'processing_stages', ['status'])

    # --------------------------------------------------------------------------
    # 14. preprocessing_runs
    # --------------------------------------------------------------------------
    op.create_table(
        'preprocessing_runs',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('survey_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('frame_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('sonar_device_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('tvg_applied', sa.Boolean(), server_default='false', nullable=False),
        sa.Column('destriping_applied', sa.Boolean(), server_default='false', nullable=False),
        sa.Column('denoising_applied', sa.Boolean(), server_default='false', nullable=False),
        sa.Column('quality_score', sa.Numeric(precision=5, scale=2), nullable=True),
        sa.Column('run_parameters', postgresql.JSONB(astext_type=sa.Text()), server_default='{}', nullable=False),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.CheckConstraint('quality_score IS NULL OR (quality_score >= 0 AND quality_score <= 100)', name='ck_preprocessing_runs_quality_range'),
        sa.ForeignKeyConstraint(['frame_id'], ['survey_frames.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['sonar_device_id'], ['sonar_devices.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['survey_id'], ['surveys.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        comment='Audit record of acoustic preprocessing transformations and reproducible parameter states.',
    )
    op.create_index('idx_preprocessing_runs_survey_id', 'preprocessing_runs', ['survey_id'])
    op.create_index('idx_preprocessing_runs_frame_id', 'preprocessing_runs', ['frame_id'])

    # --------------------------------------------------------------------------
    # 15. dataset_versions
    # --------------------------------------------------------------------------
    op.create_table(
        'dataset_versions',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('version_tag', sa.String(length=100), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('total_samples', sa.Integer(), server_default='0', nullable=False),
        sa.Column('split_ratios', postgresql.JSONB(astext_type=sa.Text()), server_default='{"train": 0.7, "val": 0.15, "test": 0.15}', nullable=False),
        sa.Column('storage_artifact_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('is_frozen', sa.Boolean(), server_default='true', nullable=False),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.CheckConstraint('total_samples >= 0', name='ck_dataset_versions_samples_positive'),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['storage_artifact_id'], ['storage_artifacts.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('version_tag', name='uq_dataset_versions_version_tag'),
        comment='Immutable training/evaluation dataset snapshots used in model retraining loops.',
    )

    # --------------------------------------------------------------------------
    # 16. ai_models
    # --------------------------------------------------------------------------
    op.create_table(
        'ai_models',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('version', sa.String(length=50), nullable=False),
        sa.Column('model_type', sa.String(length=50), nullable=False),
        sa.Column('framework', sa.String(length=50), nullable=False),
        sa.Column('dataset_version_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('storage_artifact_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('parameters', postgresql.JSONB(astext_type=sa.Text()), server_default='{}', nullable=False),
        sa.Column('status', sa.String(length=50), server_default='registered', nullable=False),
        sa.Column('is_active', sa.Boolean(), server_default='false', nullable=False),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('updated_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.ForeignKeyConstraint(['dataset_version_id'], ['dataset_versions.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['storage_artifact_id'], ['storage_artifacts.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name', 'version', name='uq_ai_models_name_version'),
        comment='Registry of deployed and candidate neural network weights (YOLO, U-Net).',
    )
    op.create_index('idx_ai_models_status', 'ai_models', ['status'])

    # --------------------------------------------------------------------------
    # 17. model_evaluations
    # --------------------------------------------------------------------------
    op.create_table(
        'model_evaluations',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('ai_model_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('dataset_version_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('precision_score', sa.Numeric(precision=5, scale=4), nullable=True),
        sa.Column('recall_score', sa.Numeric(precision=5, scale=4), nullable=True),
        sa.Column('map50_score', sa.Numeric(precision=5, scale=4), nullable=True),
        sa.Column('map50_95_score', sa.Numeric(precision=5, scale=4), nullable=True),
        sa.Column('iou_score', sa.Numeric(precision=5, scale=4), nullable=True),
        sa.Column('f1_score', sa.Numeric(precision=5, scale=4), nullable=True),
        sa.Column('evaluation_metrics', postgresql.JSONB(astext_type=sa.Text()), server_default='{}', nullable=False),
        sa.Column('evaluated_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.CheckConstraint('precision_score IS NULL OR (precision_score >= 0 AND precision_score <= 1)', name='ck_eval_precision_range'),
        sa.CheckConstraint('recall_score IS NULL OR (recall_score >= 0 AND recall_score <= 1)', name='ck_eval_recall_range'),
        sa.CheckConstraint('map50_score IS NULL OR (map50_score >= 0 AND map50_score <= 1)', name='ck_eval_map50_range'),
        sa.CheckConstraint('map50_95_score IS NULL OR (map50_95_score >= 0 AND map50_95_score <= 1)', name='ck_eval_map50_95_range'),
        sa.CheckConstraint('iou_score IS NULL OR (iou_score >= 0 AND iou_score <= 1)', name='ck_eval_iou_range'),
        sa.CheckConstraint('f1_score IS NULL OR (f1_score >= 0 AND f1_score <= 1)', name='ck_eval_f1_range'),
        sa.ForeignKeyConstraint(['ai_model_id'], ['ai_models.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['dataset_version_id'], ['dataset_versions.id'], ondelete='RESTRICT'),
        sa.PrimaryKeyConstraint('id'),
        comment='Benchmark evaluation results and split metrics for trained AI models.',
    )
    op.create_index('idx_model_evaluations_model_id', 'model_evaluations', ['ai_model_id'])
    op.create_index('idx_model_evaluations_dataset_id', 'model_evaluations', ['dataset_version_id'])

    # --------------------------------------------------------------------------
    # 18. detections
    # --------------------------------------------------------------------------
    op.create_table(
        'detections',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('survey_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('survey_frame_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('processing_stage_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('ai_model_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('target_class_id', sa.Integer(), nullable=False),
        sa.Column('bounding_box', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('confidence', sa.Numeric(precision=5, scale=4), nullable=False),
        sa.Column('segmentation_mask_artifact_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('status', sa.String(length=50), server_default='unreviewed', nullable=False),
        sa.Column('raw_lat', sa.Float(), nullable=True),
        sa.Column('raw_lon', sa.Float(), nullable=True),
        sa.Column('metadata_json', postgresql.JSONB(astext_type=sa.Text()), server_default='{}', nullable=False),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('updated_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.CheckConstraint('confidence >= 0 AND confidence <= 1', name='ck_detections_confidence_range'),
        sa.ForeignKeyConstraint(['ai_model_id'], ['ai_models.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['processing_stage_id'], ['processing_stages.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['segmentation_mask_artifact_id'], ['storage_artifacts.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['survey_frame_id'], ['survey_frames.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['survey_id'], ['surveys.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['target_class_id'], ['target_classes.id'], ondelete='RESTRICT'),
        sa.PrimaryKeyConstraint('id'),
        comment='Raw neural network inference outputs, bounding boxes [x1,y1,x2,y2], and initial confidence.',
    )
    op.create_index('idx_detections_survey_id', 'detections', ['survey_id'])
    op.create_index('idx_detections_frame_id', 'detections', ['survey_frame_id'])
    op.create_index('idx_detections_target_class_id', 'detections', ['target_class_id'])
    op.create_index('idx_detections_status', 'detections', ['status'])

    # --------------------------------------------------------------------------
    # 19. xai_evidence
    # --------------------------------------------------------------------------
    op.create_table(
        'xai_evidence',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('detection_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('method', sa.String(length=50), server_default='grad_cam', nullable=False),
        sa.Column('heatmap_artifact_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('saliency_score', sa.Numeric(precision=5, scale=4), nullable=True),
        sa.Column('explanation_json', postgresql.JSONB(astext_type=sa.Text()), server_default='{}', nullable=False),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.CheckConstraint('saliency_score IS NULL OR (saliency_score >= 0 AND saliency_score <= 1)', name='ck_xai_saliency_range'),
        sa.ForeignKeyConstraint(['detection_id'], ['detections.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['heatmap_artifact_id'], ['storage_artifacts.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('detection_id', name='uq_xai_evidence_detection_id'),
        comment='One-to-one explainability evidence (Grad-CAM heatmaps) proving prediction rationale.',
    )

    # --------------------------------------------------------------------------
    # 20. physics_validation
    # --------------------------------------------------------------------------
    op.create_table(
        'physics_validation',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('detection_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('slant_range_meters', sa.Numeric(precision=8, scale=2), nullable=True),
        sa.Column('acoustic_shadow_length_meters', sa.Numeric(precision=8, scale=2), nullable=True),
        sa.Column('expected_size_meters', sa.Numeric(precision=8, scale=2), nullable=True),
        sa.Column('shadow_consistency_score', sa.Numeric(precision=5, scale=4), nullable=True),
        sa.Column('is_plausible', sa.Boolean(), server_default='true', nullable=False),
        sa.Column('validation_details', postgresql.JSONB(astext_type=sa.Text()), server_default='{}', nullable=False),
        sa.Column('validated_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.CheckConstraint('shadow_consistency_score IS NULL OR (shadow_consistency_score >= 0 AND shadow_consistency_score <= 1)', name='ck_physics_shadow_consistency_range'),
        sa.ForeignKeyConstraint(['detection_id'], ['detections.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('detection_id', name='uq_physics_validation_detection_id'),
        comment='One-to-one acoustic geometry validation: slant-range plausibility and shadow consistency.',
    )

    # --------------------------------------------------------------------------
    # 21. geotags
    # --------------------------------------------------------------------------
    op.create_table(
        'geotags',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('detection_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('survey_frame_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('location', Geography(geometry_type='POINT', srid=4326), nullable=False),
        sa.Column('uncertainty_radius_meters', sa.Numeric(precision=8, scale=2), nullable=True),
        sa.Column('depth_meters', sa.Numeric(precision=8, scale=2), nullable=True),
        sa.Column('is_authoritative', sa.Boolean(), server_default='false', nullable=False),
        sa.Column('calculation_method', sa.String(length=100), server_default='slant_range_nav', nullable=False),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.CheckConstraint('uncertainty_radius_meters IS NULL OR uncertainty_radius_meters >= 0', name='ck_geotags_uncertainty_positive'),
        sa.ForeignKeyConstraint(['detection_id'], ['detections.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['survey_frame_id'], ['survey_frames.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        comment='Calculated geographic coordinates for detections with uncertainty bounding radius.',
    )
    op.create_index('idx_geotags_detection_id', 'geotags', ['detection_id'])
    op.create_index('idx_geotags_frame_id', 'geotags', ['survey_frame_id'])
    op.execute('CREATE INDEX idx_geotags_location ON geotags USING GIST (location);')
    # Partial unique index: at most one authoritative geotag per detection
    op.execute('CREATE UNIQUE INDEX uq_geotag_authoritative ON geotags (detection_id) WHERE is_authoritative = TRUE;')

    # --------------------------------------------------------------------------
    # 22. targets
    # --------------------------------------------------------------------------
    op.create_table(
        'targets',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('target_class_id', sa.Integer(), nullable=False),
        sa.Column('location', Geography(geometry_type='POINT', srid=4326), nullable=False),
        sa.Column('best_survey_frame_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('status', sa.String(length=50), server_default='detected', nullable=False),
        sa.Column('fused_confidence', sa.Numeric(precision=5, scale=4), nullable=False),
        sa.Column('observation_count', sa.Integer(), server_default='1', nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('metadata_json', postgresql.JSONB(astext_type=sa.Text()), server_default='{}', nullable=False),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('updated_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.CheckConstraint('fused_confidence >= 0 AND fused_confidence <= 1', name='ck_targets_confidence_range'),
        sa.CheckConstraint('observation_count >= 1', name='ck_targets_observation_count_positive'),
        sa.ForeignKeyConstraint(['best_survey_frame_id'], ['survey_frames.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['target_class_id'], ['target_classes.id'], ondelete='RESTRICT'),
        sa.PrimaryKeyConstraint('id'),
        comment='Fused real-world underwater targets deduplicated across multiple frame passes.',
    )
    op.create_index('idx_targets_class_id', 'targets', ['target_class_id'])
    op.create_index('idx_targets_status', 'targets', ['status'])
    op.execute('CREATE INDEX idx_targets_location ON targets USING GIST (location);')

    # --------------------------------------------------------------------------
    # 23. target_history
    # --------------------------------------------------------------------------
    op.create_table(
        'target_history',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('target_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('updated_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('previous_status', sa.String(length=50), nullable=True),
        sa.Column('new_status', sa.String(length=50), nullable=False),
        sa.Column('previous_confidence', sa.Numeric(precision=5, scale=4), nullable=True),
        sa.Column('new_confidence', sa.Numeric(precision=5, scale=4), nullable=True),
        sa.Column('change_reason', sa.Text(), nullable=True),
        sa.Column('metadata_json', postgresql.JSONB(astext_type=sa.Text()), server_default='{}', nullable=False),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.CheckConstraint('previous_confidence IS NULL OR (previous_confidence >= 0 AND previous_confidence <= 1)', name='ck_target_hist_prev_conf_range'),
        sa.CheckConstraint('new_confidence IS NULL OR (new_confidence >= 0 AND new_confidence <= 1)', name='ck_target_hist_new_conf_range'),
        sa.ForeignKeyConstraint(['target_id'], ['targets.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['updated_by'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
        comment='Audit trail tracking lifecycle and status transitions of underwater targets.',
    )
    op.create_index('idx_target_history_target_id', 'target_history', ['target_id'])

    # --------------------------------------------------------------------------
    # 24. detection_target_mapping
    # --------------------------------------------------------------------------
    op.create_table(
        'detection_target_mapping',
        sa.Column('detection_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('target_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('association_score', sa.Numeric(precision=5, scale=4), nullable=True),
        sa.Column('associated_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.CheckConstraint('association_score IS NULL OR (association_score >= 0 AND association_score <= 1)', name='ck_mapping_association_score_range'),
        sa.ForeignKeyConstraint(['detection_id'], ['detections.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['target_id'], ['targets.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('detection_id', 'target_id'),
        comment='Many-to-many spatial association linking raw detections into unified real-world targets.',
    )
    op.create_index('idx_detection_target_target_id', 'detection_target_mapping', ['target_id'])

    # --------------------------------------------------------------------------
    # 25. review_assignments
    # --------------------------------------------------------------------------
    op.create_table(
        'review_assignments',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('detection_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('assigned_to', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('status', sa.String(length=50), server_default='claimed', nullable=False),
        sa.Column('claimed_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('expires_at', sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column('completed_at', sa.TIMESTAMP(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['assigned_to'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['detection_id'], ['detections.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        comment='Marine expert review work queue claims preventing concurrent review collisions.',
    )
    op.create_index('idx_review_assignments_assigned_to', 'review_assignments', ['assigned_to'])
    op.create_index('idx_review_assignments_status', 'review_assignments', ['status'])
    # Partial unique index: at most one active claimed assignment per detection
    op.execute("CREATE UNIQUE INDEX uq_review_assignment_claimed ON review_assignments (detection_id) WHERE status = 'claimed';")

    # --------------------------------------------------------------------------
    # 26. reviews
    # --------------------------------------------------------------------------
    op.create_table(
        'reviews',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('detection_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('target_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('reviewer_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('decision', sa.String(length=50), nullable=False),
        sa.Column('corrected_target_class_id', sa.Integer(), nullable=True),
        sa.Column('corrected_bbox', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('corrected_mask_artifact_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('comments', sa.Text(), nullable=True),
        sa.Column('reviewed_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.ForeignKeyConstraint(['corrected_mask_artifact_id'], ['storage_artifacts.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['corrected_target_class_id'], ['target_classes.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['detection_id'], ['detections.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['reviewer_id'], ['users.id'], ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['target_id'], ['targets.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
        comment='Expert annotations, validation decisions, and bounding box corrections.',
    )
    op.create_index('idx_reviews_detection_id', 'reviews', ['detection_id'])
    op.create_index('idx_reviews_reviewer_id', 'reviews', ['reviewer_id'])

    # --------------------------------------------------------------------------
    # 27. dataset_samples
    # --------------------------------------------------------------------------
    op.create_table(
        'dataset_samples',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('dataset_version_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('detection_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('survey_frame_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('target_class_id', sa.Integer(), nullable=False),
        sa.Column('split_type', sa.String(length=20), nullable=False),
        sa.Column('quality_score', sa.Numeric(precision=5, scale=2), nullable=True),
        sa.Column('annotation_data', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.CheckConstraint("split_type IN ('train', 'val', 'test')", name='ck_dataset_samples_split_type'),
        sa.CheckConstraint('quality_score IS NULL OR (quality_score >= 0 AND quality_score <= 100)', name='ck_dataset_samples_quality_range'),
        sa.ForeignKeyConstraint(['dataset_version_id'], ['dataset_versions.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['detection_id'], ['detections.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['survey_frame_id'], ['survey_frames.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['target_class_id'], ['target_classes.id'], ondelete='RESTRICT'),
        sa.PrimaryKeyConstraint('id'),
        comment='Curated training samples generated from expert reviews for retraining loops.',
    )
    op.create_index('idx_dataset_samples_version_id', 'dataset_samples', ['dataset_version_id'])
    op.create_index('idx_dataset_samples_class_id', 'dataset_samples', ['target_class_id'])

    # --------------------------------------------------------------------------
    # 28. notifications
    # --------------------------------------------------------------------------
    op.create_table(
        'notifications',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('message', sa.Text(), nullable=False),
        sa.Column('notification_type', sa.String(length=50), nullable=False),
        sa.Column('link_url', sa.String(length=512), nullable=True),
        sa.Column('is_read', sa.Boolean(), server_default='false', nullable=False),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        comment='Asynchronous user notifications for survey processing, reviews, and alerts.',
    )
    op.create_index('idx_notifications_user_read', 'notifications', ['user_id', 'is_read'])

    # --------------------------------------------------------------------------
    # 29. audit_logs
    # --------------------------------------------------------------------------
    op.create_table(
        'audit_logs',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('correlation_id', sa.String(length=100), nullable=True),
        sa.Column('action', sa.String(length=100), nullable=False),
        sa.Column('resource_type', sa.String(length=100), nullable=False),
        sa.Column('resource_id', sa.String(length=255), nullable=True),
        sa.Column('details', postgresql.JSONB(astext_type=sa.Text()), server_default='{}', nullable=False),
        sa.Column('ip_address', sa.String(length=45), nullable=True),
        sa.Column('user_agent', sa.String(length=512), nullable=True),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
        comment='Security audit trail capturing user mutations, API events, and correlation IDs.',
    )
    op.create_index('idx_audit_logs_user_id', 'audit_logs', ['user_id'])
    op.create_index('idx_audit_logs_created_at', 'audit_logs', ['created_at'])
    op.create_index('idx_audit_logs_correlation_id', 'audit_logs', ['correlation_id'])

    # --------------------------------------------------------------------------
    # 30. Materialized View: mv_survey_stats
    # --------------------------------------------------------------------------
    op.execute("""
        CREATE MATERIALIZED VIEW mv_survey_stats AS
        SELECT
            s.operator_id,
            COUNT(DISTINCT s.id) AS total_surveys,
            COUNT(DISTINCT sf.id) AS total_frames_processed,
            COUNT(DISTINCT d.id) AS total_detections,
            COALESCE(AVG(d.confidence), 0.0)::DECIMAL(5,4) AS avg_confidence
        FROM surveys s
        LEFT JOIN survey_frames sf ON sf.survey_id = s.id
        LEFT JOIN detections d ON d.survey_id = s.id
        GROUP BY s.operator_id;
    """)
    op.execute("""
        CREATE UNIQUE INDEX idx_mv_survey_stats_operator_id ON mv_survey_stats (operator_id);
    """)

    # --------------------------------------------------------------------------
    # 31. Seed Data: Roles, Target Classes, Development Admin User
    # --------------------------------------------------------------------------
    admin_role_id = 'a0000000-0000-0000-0000-000000000001'
    admin_user_id = '00000000-0000-0000-0000-000000000001'

    # Seed 6 Blueprint Roles
    op.execute(f"""
        INSERT INTO roles (id, name, description, permissions) VALUES
        ('{admin_role_id}', 'admin', 'Full platform administrative access, user/org management, model monitoring and audit logs.',
         '{{"dashboard": ["read", "write"], "admin": ["read", "write", "delete"], "retraining": ["read", "write", "execute"], "surveys": ["read", "write", "delete"], "reviews": ["read", "write"], "targets": ["read", "write", "delete"], "missions": ["read", "write", "delete"], "analytics": ["read", "export"], "reports": ["read", "create", "export"]}}'::jsonb),
        ('a0000000-0000-0000-0000-000000000002', 'survey_operator', 'Survey operations, raw SSS file uploads, pipeline execution, and frame inspection.',
         '{{"dashboard": ["read"], "surveys": ["read", "write"], "pipeline": ["execute", "monitor"], "detections": ["read"], "reports": ["read", "create"]}}'::jsonb),
        ('a0000000-0000-0000-0000-000000000003', 'marine_expert', 'Domain expert review queue, detection annotation, correction, and dataset sample generation.',
         '{{"dashboard": ["read"], "reviews": ["read", "claim", "write"], "detections": ["read", "annotate", "correct"], "dataset_samples": ["create"]}}'::jsonb),
        ('a0000000-0000-0000-0000-000000000004', 'authority', 'Port and coastal authority monitoring verified debris, hotspots, risk, and cleanup operations.',
         '{{"dashboard": ["read"], "map": ["read", "filter"], "targets": ["read"], "analytics": ["read", "export"], "reports": ["read", "export"]}}'::jsonb),
        ('a0000000-0000-0000-0000-000000000005', 'ngo', 'Marine NGO cleanup missions, target prioritization, and recovery tracking.',
         '{{"dashboard": ["read"], "map": ["read"], "targets": ["read"], "missions": ["read", "write", "execute"], "reports": ["read", "create"]}}'::jsonb),
        ('a0000000-0000-0000-0000-000000000006', 'researcher', 'Scientific researcher studying historical marine debris trends and aggregate geospatial data.',
         '{{"dashboard": ["read"], "map": ["read_anonymized"], "analytics": ["read", "export_anonymized"], "reports": ["read"]}}'::jsonb)
        ON CONFLICT (name) DO NOTHING;
    """)

    # Seed 6 Target Debris Classes (0-4 + 5: unknown)
    op.execute("""
        INSERT INTO target_classes (id, name, display_name, description, color_hex, risk_level, is_active) VALUES
        (0, 'crab_pot', 'Crab Pot / Trap', 'Discarded or active commercial crab/lobster pot debris resting on seabed.', '#f59e0b', 'medium', true),
        (1, 'submarine_pipeline', 'Submarine Pipeline', 'Subsea pipeline structure or exposed marine infrastructure section.', '#3b82f6', 'high', true),
        (2, 'shipwreck', 'Shipwreck / Vessel Hull', 'Sunken vessel, shipwreck debris field, or structural hull fragments.', '#ef4444', 'critical', true),
        (3, 'ghost_net', 'Ghost Net / Derelict Gear', 'Entangled or drifting derelict monofilament fishing net posing severe marine hazard.', '#ec4899', 'critical', true),
        (4, 'mine_cylinder', 'Mine / Cylindrical Debris', 'Cylindrical ordnance, industrial drum, or metallic container on seafloor.', '#eab308', 'critical', true),
        (5, 'unknown', 'Unknown / Anomaly', 'Unclassified acoustic anomaly or out-of-distribution debris candidate.', '#94a3b8', 'low', true)
        ON CONFLICT (id) DO NOTHING;
    """)

    # Seed 1 development admin user (DEV ONLY - clearly marked, verified BCrypt hash)
    op.execute(f"""
        INSERT INTO users (id, email, password_hash, full_name, status, is_verified, two_factor_enabled, profile) VALUES
        ('{admin_user_id}', 'admin@tarang.dev', '$2b$12$tsW3w/6Mzi8APgE5nw69BOVNSnfoq4AlHHMEBw15o/qya0U55USE2',
         'TARANG Development Admin (DEV ONLY)', 'active', true, false,
         '{{"title": "System Administrator", "note": "DEVELOPMENT BOOTSTRAP USER ONLY. DO NOT USE IN PRODUCTION."}}'::jsonb)
        ON CONFLICT (email) DO NOTHING;
    """)

    # Link dev admin user to admin role
    op.execute(f"""
        INSERT INTO user_roles (user_id, role_id) VALUES
        ('{admin_user_id}', '{admin_role_id}')
        ON CONFLICT (user_id, role_id) DO NOTHING;
    """)


def downgrade() -> None:
    # --------------------------------------------------------------------------
    # Drop in exact reverse dependency order
    # --------------------------------------------------------------------------
    op.execute('DROP MATERIALIZED VIEW IF EXISTS mv_survey_stats CASCADE;')
    op.drop_table('audit_logs')
    op.drop_table('notifications')
    op.drop_table('dataset_samples')
    op.drop_table('reviews')
    op.drop_table('review_assignments')
    op.drop_table('detection_target_mapping')
    op.drop_table('target_history')
    op.drop_table('targets')
    op.drop_table('geotags')
    op.drop_table('physics_validation')
    op.drop_table('xai_evidence')
    op.drop_table('detections')
    op.drop_table('model_evaluations')
    op.drop_table('ai_models')
    op.drop_table('dataset_versions')
    op.drop_table('preprocessing_runs')
    op.drop_table('processing_stages')
    op.drop_table('processing_jobs')
    op.drop_table('survey_frames')
    op.drop_table('sss_files')
    op.drop_table('surveys')
    op.drop_table('storage_artifacts')
    op.drop_table('target_classes')
    op.drop_table('sonar_devices')
    op.drop_table('refresh_tokens')
    op.drop_table('user_roles')
    op.drop_table('users')
    op.drop_table('roles')
    op.drop_table('organizations')
