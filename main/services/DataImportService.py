"""
DataImportService - Optimized background import job management service.

Handles creation, execution, pause/resume of dataset import jobs using Django-Q.
OPTIMIZED: Uses bulk operations, pre-caching, and minimal database queries.
"""
import traceback
from datetime import datetime

from django.utils import timezone
from django_q.tasks import async_task

from vvecon.zorion.core import Service
from vvecon.zorion.logger import Logger

from ..models import DataImportJob, Patient, Study, StudyResult, StudyVariable, UserStudy
from ..services import StudyService

__all__ = ['DataImportService']


class DataImportService(Service):
	"""Service for managing background data import jobs."""

	model = DataImportJob
	CONSECUTIVE_ERROR_THRESHOLD = 10
	BATCH_SIZE = 100  # Larger batches for better performance

	# ========================================================================
	# Job Lifecycle Methods
	# ========================================================================

	def create_job(  # noqa: PLR0913
		self,
		study_id: int,
		file_url: str,
		file_name: str,
		mapping: dict,
		column_types: dict,
		total_rows: int,
		user,
	) -> DataImportJob:
		"""Create a new import job in PENDING state."""
		# Check for existing active import on this dataset
		active_job = DataImportJob.objects.filter(
			study_id=study_id,
			status__in=['PENDING', 'RUNNING'],
		).first()

		if active_job:
			raise ValueError(f'An import is already in progress for this dataset (Job #{active_job.id})')

		job = DataImportJob.objects.create(
			study_id=study_id,
			file_url=file_url,
			file_name=file_name,
			mapping=mapping,
			column_types=column_types,
			total_rows=total_rows,
			created_by=user,
		)

		Logger.info(f'Created import job #{job.id} for study {study_id}')
		return job

	def start_job(self, job_id: int) -> DataImportJob:
		"""Start a pending import job by queueing it to Django-Q."""
		job = self.getById(job_id)

		if job.status not in ['PENDING', 'PAUSED']:
			raise ValueError(f'Cannot start job with status {job.status}')

		job.status = 'RUNNING'
		job.started_at = timezone.now()
		job.paused_reason = None
		job.save(update_fields=['status', 'started_at', 'paused_reason', 'updated_at'])

		# Queue background task - use module-level function for Django-Q
		task_id = async_task(
			'main.services.DataImportService.execute_import_task_sync',
			job_id,
			task_name=f'import_job_{job_id}',
		)

		job.task_id = task_id
		job.save(update_fields=['task_id', 'updated_at'])

		Logger.info(f'Started import job #{job_id}, task_id: {task_id}')
		return job

	def pause_job(self, job_id: int, reason: str = 'manual') -> DataImportJob:
		"""Pause a running import job."""
		job = self.getById(job_id)

		if job.status != 'RUNNING':
			raise ValueError(f'Cannot pause job with status {job.status}')

		job.status = 'PAUSED'
		job.paused_reason = reason
		job.save(update_fields=['status', 'paused_reason', 'updated_at'])

		Logger.info(f'Paused import job #{job_id}, reason: {reason}')
		return job

	def resume_job(self, job_id: int) -> DataImportJob:
		"""Resume a paused import job."""
		job = self.getById(job_id)

		if job.status != 'PAUSED':
			raise ValueError(f'Cannot resume job with status {job.status}')

		return self.start_job(job_id)

	def cancel_job(self, job_id: int) -> DataImportJob:
		"""Cancel an import job."""
		job = self.getById(job_id)

		if job.status in ['COMPLETED', 'FAILED', 'CANCELLED']:
			raise ValueError(f'Cannot cancel job with status {job.status}')

		job.status = 'CANCELLED'
		job.completed_at = timezone.now()
		job.save(update_fields=['status', 'completed_at', 'updated_at'])

		Logger.info(f'Cancelled import job #{job_id}')
		return job

	def get_job_status(self, job_id: int) -> dict:
		"""Get current job status for API response."""
		job = self.getById(job_id)

		return {
			'id': job.id,
			'status': job.status,
			'study_id': job.study_id,
			'file_name': job.file_name,
			'file_url': job.file_url,
			'total_rows': job.total_rows,
			'processed_rows': job.processed_rows,
			'progress_percent': job.progress_percent,
			'imported_count': job.imported_count,
			'updated_count': job.updated_count,
			'skipped_count': job.skipped_count,
			'error_count': job.error_count,
			'patients_created': job.patients_created,
			'variables_created': job.variables_created,
			'paused_reason': job.paused_reason,
			'started_at': job.started_at.isoformat() if job.started_at else None,
			'completed_at': job.completed_at.isoformat() if job.completed_at else None,
			'created_at': job.created_at.isoformat() if job.created_at else None,
			'created_by': {
				'id': job.created_by.id,
				'name': f'{job.created_by.firstName} {job.created_by.lastName}'.strip(),
			} if job.created_by else None,
			'errors': job.errors[-10:] if job.errors else [],
		}

	def get_jobs_for_study(self, study_id: int, include_all: bool = True):
		"""Get all import jobs for a study."""
		queryset = DataImportJob.objects.filter(study_id=study_id)
		if not include_all:
			queryset = queryset.exclude(status__in=['COMPLETED', 'CANCELLED'])
		return queryset.select_related('created_by').order_by('-created_at')

	def get_active_job_for_study(self, study_id: int) -> DataImportJob | None:
		"""Get the active (running or paused) import job for a study."""
		return DataImportJob.objects.filter(
			study_id=study_id,
			status__in=['PENDING', 'RUNNING', 'PAUSED'],
		).first()

	# ========================================================================
	# OPTIMIZED Import Execution (Called by Django-Q worker)
	# ========================================================================

	@staticmethod
	def execute_import_task(job_id: int) -> dict:  # noqa: PLR0915, PLR0912, PLR0911, C901
		"""
		Execute import task - OPTIMIZED version.
		Key optimizations:
		1. Pre-create all variables before processing rows
		2. Pre-cache all patients by name/reference
		3. Bulk create StudyResult records
		4. Minimal database queries during row processing
		"""
		service = DataImportService()
		study_service = StudyService()

		try:
			job = service.getById(job_id)
		except Exception as e:
			Logger.error(f'Failed to load job #{job_id}: {e}')
			return {'error': str(e)}

		Logger.info(f'[IMPORT] Starting optimized job #{job_id} from row {job.processed_rows}')

		try:
			# Read file content
			file_path = study_service._resolveFilePath(job.file_url)  # noqa: SLF001
			if not file_path.exists():
				service._fail_job(job, f'File not found: {file_path}')
				return {'error': 'File not found'}

			columns, all_rows = study_service._readFileContent(file_path)  # noqa: SLF001
			total_rows = len(all_rows)

			if total_rows != job.total_rows:
				job.total_rows = total_rows
				job.save(update_fields=['total_rows', 'updated_at'])

			# Pre-fetch study with variables
			study = Study.objects.prefetch_related('variables').get(id=job.study_id)

			# Extract mapping
			mapping = job.mapping
			patient_mapping = mapping.get('patient', {})
			variable_mapping = mapping.get('variables', {})

			# Get patient column names
			patient_col = patient_mapping.get('reference', '')
			first_name_col = patient_mapping.get('firstName', '')
			last_name_col = patient_mapping.get('lastName', '')
			dob_col = patient_mapping.get('dateOfBirth', '')
			age_col = patient_mapping.get('age', '')
			gender_col = patient_mapping.get('gender', '')
			lat_col = patient_mapping.get('latitude', '')
			lng_col = patient_mapping.get('longitude', '')

			patient_columns = {
				patient_col, first_name_col, last_name_col, dob_col, age_col, gender_col,
				lat_col, lng_col,
			}
			patient_columns.discard('')

			# Get data columns (excluding system columns)
			skip_patterns = study_service.SKIP_COLUMN_PATTERNS
			data_columns = [
				col for col in columns
				if not any(col.lower().startswith(p) for p in skip_patterns)
			]

			# ============================================================
			# STEP 1: Pre-create all variables (unmapped columns)
			# ============================================================
			all_vars = list(study.variables.all())
			existing_variables = {v.name.lower(): v for v in all_vars}
			variables_by_id = {str(v.id): v for v in all_vars}
			mapped_columns = set(variable_mapping.values())

			# Find unmapped data columns that need new variables
			new_var_names = [
				col for col in data_columns
				if col not in mapped_columns and col not in patient_columns and col.lower() not in existing_variables
			]

			# Create and link new variables
			if new_var_names:
				new_vars = []
				for name in new_var_names:
					# Create variable (no study FK)
					var = StudyVariable.objects.create(name=name, type='TEXT', field='TEXT')
					new_vars.append(var)

				# Link to study (Many-to-Many)
				study.variables.add(*new_vars)

				job.variables_created = len(new_vars)

				# Refresh variable cache
				all_vars = list(study.variables.all())
				existing_variables = {v.name.lower(): v for v in all_vars}
				variables_by_id = {str(v.id): v for v in all_vars}

				Logger.info(f'[IMPORT] Created {len(new_vars)} new variables')

			# ============================================================
			# STEP 2: Pre-cache ALL UserStudy records for this dataset
			# ============================================================
			existing_user_studies_by_ref = {}
			existing_user_studies_by_patient = {}
			for us in UserStudy.objects.filter(study=study).select_related('patient'):
				if us.reference:
					existing_user_studies_by_ref[us.reference] = us
				if us.patient_id:
					existing_user_studies_by_patient[us.patient_id] = us

			# ============================================================
			# STEP 3: Pre-cache ALL patients by name (first+last+dob key)
			# ============================================================
			all_patients = {}
			for p in Patient.objects.all().only('id', 'firstName', 'lastName', 'dateOfBirth'):
				key = f"{(p.firstName or '').lower()}|{(p.lastName or '').lower()}|{p.dateOfBirth or ''}"
				all_patients[key] = p

			# Skip to processed rows
			start_row = job.processed_rows
			rows_to_process = all_rows[start_row:]

			seen_signatures = set()
			results_to_create = []  # Bulk StudyResult buffer
			RESULT_FLUSH_SIZE = 500

			# ============================================================
			# STEP 4: Process rows in batches
			# ============================================================
			batch_start = 0
			while batch_start < len(rows_to_process):
				# Check if job was paused
				job.refresh_from_db()
				if job.status == 'PAUSED':
					# Flush pending results before pausing
					if results_to_create:
						service._bulk_upsert_results(results_to_create)
						results_to_create = []
					Logger.info(f'[IMPORT] Job #{job_id} paused at row {job.processed_rows}')
					return {'status': 'paused', 'processed': job.processed_rows}

				if job.status == 'CANCELLED':
					Logger.info(f'[IMPORT] Job #{job_id} cancelled')
					return {'status': 'cancelled'}

				batch_end = min(batch_start + service.BATCH_SIZE, len(rows_to_process))
				batch = rows_to_process[batch_start:batch_end]

				for idx, row in enumerate(batch):
					actual_row_num = start_row + batch_start + idx
					try:
						result = service._process_row_optimized(
							row=row,
							study=study,
							job=job,
							patient_mapping=patient_mapping,
							variable_mapping=variable_mapping,
							existing_user_studies_by_ref=existing_user_studies_by_ref,
							existing_user_studies_by_patient=existing_user_studies_by_patient,
							existing_variables=existing_variables,
							variables_by_id=variables_by_id,
							data_columns=data_columns,
							mapped_columns=mapped_columns,
							patient_columns=patient_columns,
							seen_signatures=seen_signatures,
							all_patients=all_patients,
							results_buffer=results_to_create,
						)

						# Update stats
						if result == 'imported':
							job.imported_count += 1
						elif result == 'updated':
							job.updated_count += 1
						elif result == 'skipped':
							job.skipped_count += 1
						elif result == 'patient_created':
							job.patients_created += 1
							job.imported_count += 1

						job.consecutive_errors = 0

					except Exception as e:
						job.error_count += 1
						job.consecutive_errors += 1
						if len(job.errors) < 100:  # noqa: PLR2004 (Limit error storage)
							job.errors = job.errors + [{'row': actual_row_num + 2, 'error': str(e)}]

						Logger.error(f'[IMPORT] Error at row {actual_row_num + 2}: {e}')

						# Check consecutive error threshold
						if job.consecutive_errors >= service.CONSECUTIVE_ERROR_THRESHOLD:
							if results_to_create:
								service._bulk_upsert_results(results_to_create)
							job.status = 'PAUSED'
							job.paused_reason = 'consecutive_errors'
							job.processed_rows = start_row + batch_start + idx + 1
							job.save()
							return {'status': 'paused', 'reason': 'consecutive_errors'}

					job.processed_rows = start_row + batch_start + idx + 1

				# Flush results buffer if large enough
				if len(results_to_create) >= RESULT_FLUSH_SIZE:
					service._bulk_upsert_results(results_to_create)
					results_to_create = []

				# Save progress after each batch
				job.save(update_fields=[
					'processed_rows', 'imported_count', 'updated_count',
					'skipped_count', 'error_count', 'consecutive_errors',
					'patients_created', 'variables_created', 'errors', 'updated_at',
				])

				batch_start = batch_end

			# Flush remaining results
			if results_to_create:
				service._bulk_upsert_results(results_to_create)

			# Mark as completed
			job.status = 'COMPLETED'
			job.completed_at = timezone.now()
			job.save(update_fields=['status', 'completed_at', 'updated_at'])

			Logger.info(
				f'[IMPORT] Job #{job_id} completed: {job.imported_count} imported, '
				f'{job.updated_count} updated',
			)

			return {
				'status': 'completed',
				'imported': job.imported_count,
				'updated': job.updated_count,
				'skipped': job.skipped_count,
				'errors': job.error_count,
			}

		except Exception as e:
			Logger.error(f'[IMPORT] Job #{job_id} failed: {e}')
			traceback.print_exc()
			service._fail_job(job, str(e))
			return {'error': str(e)}

	def _fail_job(self, job: DataImportJob, error: str) -> None:
		"""Mark job as failed with error message."""
		job.status = 'FAILED'
		job.completed_at = timezone.now()
		job.errors = job.errors + [{'row': 0, 'error': error}]
		job.save(update_fields=['status', 'completed_at', 'errors', 'updated_at'])

	def _bulk_upsert_results(self, results: list) -> None:
		"""Bulk insert/update StudyResult records."""
		if not results:
			return

		# Use bulk_create with update_or_create fallback
		# Group by (userStudy_id, studyVariable_id) to handle duplicates
		result_map = {}
		for r in results:
			key = (r['user_study_id'], r['variable_id'])
			result_map[key] = r['value']  # Last value wins

		# Check existing
		existing = {}
		for sr in StudyResult.objects.filter(
			userStudy_id__in=[k[0] for k in result_map],
			studyVariable_id__in=[k[1] for k in result_map],
		):
			existing[(sr.userStudy_id, sr.studyVariable_id)] = sr

		to_create = []
		to_update = []

		for (us_id, var_id), value in result_map.items():
			if (us_id, var_id) in existing:
				sr = existing[(us_id, var_id)]
				if sr.value != value:
					sr.value = value
					to_update.append(sr)
			else:
				to_create.append(StudyResult(
					userStudy_id=us_id,
					studyVariable_id=var_id,
					value=value,
				))

		if to_create:
			StudyResult.objects.bulk_create(to_create, ignore_conflicts=True)
		if to_update:
			StudyResult.objects.bulk_update(to_update, ['value'])

		Logger.info(f'[IMPORT] Flushed {len(to_create)} new + {len(to_update)} updated results')

	def _process_row_optimized(  # noqa: PLR0915, PLR0912, C901, PLR0913
		self,
		row: dict,
		study: Study,
		job: DataImportJob,
		patient_mapping: dict,
		variable_mapping: dict,
		existing_user_studies_by_ref: dict,
		existing_user_studies_by_patient: dict,
		existing_variables: dict,
		variables_by_id: dict,
		data_columns: list,
		mapped_columns: set,
		patient_columns: set,
		seen_signatures: set,
		all_patients: dict,
		results_buffer: list,
	) -> str:
		"""
		Process a single row - OPTIMIZED version.
		Uses pre-cached data and buffers results for bulk insert.
		"""
		# Extract patient fields
		patient_col = patient_mapping.get('reference', '')
		first_name_col = patient_mapping.get('firstName', '')
		last_name_col = patient_mapping.get('lastName', '')
		dob_col = patient_mapping.get('dateOfBirth', '')
		age_col = patient_mapping.get('age', '')
		gender_col = patient_mapping.get('gender', '')
		lat_col = patient_mapping.get('latitude', '')
		lng_col = patient_mapping.get('longitude', '')

		reference = str(row.get(patient_col, '')).strip() if patient_col else ''
		first_name = str(row.get(first_name_col, '')).strip() if first_name_col else ''
		last_name = str(row.get(last_name_col, '')).strip() if last_name_col else ''
		dob = str(row.get(dob_col, '')).strip() if dob_col else ''
		age = str(row.get(age_col, '')).strip() if age_col else ''
		gender = str(row.get(gender_col, '')).strip() if gender_col else ''
		latitude = str(row.get(lat_col, '')).strip() if lat_col else ''
		longitude = str(row.get(lng_col, '')).strip() if lng_col else ''

		# Convert age to DOB if needed
		effective_dob = dob
		if age and not dob:
			try:
				age_int = int(float(age))
				birth_year = timezone.now().year - age_int
				effective_dob = f'{birth_year}-01-01'
			except (ValueError, TypeError):
				pass

		# Check valid identifiers
		has_reference = bool(reference)
		has_name = bool(first_name or last_name)

		if not has_reference and not has_name:
			return 'skipped'

		# Create signature for duplicate detection within file
		signature = f'{reference}|{first_name.lower()}|{last_name.lower()}|{effective_dob}'
		if signature in seen_signatures:
			return 'skipped'
		seen_signatures.add(signature)

		# Find patient and user_study
		patient = None
		user_study = None
		created_patient = False

		# 1. Try reference lookup (fastest)
		if has_reference and reference in existing_user_studies_by_ref:
			user_study = existing_user_studies_by_ref[reference]
			patient = user_study.patient

		# 2. Try name+dob lookup from cache
		if not patient and has_name:
			patient_key = f'{first_name.lower()}|{last_name.lower()}|{effective_dob}'
			patient = all_patients.get(patient_key)
			if patient and patient.id in existing_user_studies_by_patient:
				user_study = existing_user_studies_by_patient[patient.id]

		# 3. Create patient if not found
		if not patient:
			parsed_dob = None
			if effective_dob:
				for fmt in ['%Y-%m-%d', '%d/%m/%Y', '%m/%d/%Y']:
					try:
						parsed_dob = datetime.strptime(effective_dob, fmt).date()  # noqa: DTZ007
						break
					except ValueError:
						continue

			parsed_lat = None
			parsed_lng = None
			if latitude and longitude:
				try:
					parsed_lat = float(latitude)
					parsed_lng = float(longitude)
				except (ValueError, TypeError):
					pass

			normalized_gender = 'PREFER_NOT_TO_SAY'
			if gender:
				gender_upper = gender.upper().strip()
				if gender_upper in ('M', 'MALE'):
					normalized_gender = 'MALE'
				elif gender_upper in ('F', 'FEMALE'):
					normalized_gender = 'FEMALE'

			patient = Patient.objects.create(
				firstName=first_name or None,
				lastName=last_name or None,
				dateOfBirth=parsed_dob,
				gender=normalized_gender,
				latitude=parsed_lat,
				longitude=parsed_lng,
				createdBy=job.created_by,
			)
			created_patient = True

			# Add to cache
			patient_key = f'{first_name.lower()}|{last_name.lower()}|{effective_dob}'
			all_patients[patient_key] = patient

		# 4. Create UserStudy if needed
		result_type = 'imported' if created_patient else 'updated'
		if not user_study:
			user_study, us_created = UserStudy.objects.get_or_create(
				study=study,
				patient=patient,
				defaults={
					'reference': reference or f'AUTO-{patient.id}',
					'createdBy': job.created_by,
				},
			)
			if us_created:
				result_type = 'imported'
				existing_user_studies_by_patient[patient.id] = user_study
				if reference:
					existing_user_studies_by_ref[reference] = user_study

		# 5. Buffer variable values for bulk insert
		# Mapped variables
		for var_id_str, column_name in variable_mapping.items():
			variable = variables_by_id.get(var_id_str)
			if variable and column_name in row:
				value = str(row.get(column_name, '')).strip()
				if value:
					results_buffer.append({
						'user_study_id': user_study.id,
						'variable_id': variable.id,
						'value': value,
					})

		# Unmapped columns (auto-created variables)
		for col in data_columns:
			if col not in mapped_columns and col not in patient_columns:
				variable = existing_variables.get(col.lower())
				if variable:
					value = str(row.get(col, '')).strip()
					if value:
						results_buffer.append({
							'user_study_id': user_study.id,
							'variable_id': variable.id,
							'value': value,
						})

		if created_patient:
			return 'patient_created'

		return result_type


# ========================================================================
# Module-level function for Django-Q task discovery
# ========================================================================

def execute_import_task_sync(job_id: int) -> dict:
	"""
	Module-level wrapper for Django-Q to discover.
	Django-Q requires module-level functions, not class methods.
	"""
	service = DataImportService()
	return service.execute_import_task(job_id)
