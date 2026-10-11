import datetime
from django.db import IntegrityError
from django.test import TestCase, Client
from rest_framework.test import APIClient

from authentication.models import User
from authentication.enums import Gender
from main.models import DataImportJob, Patient, Study, UserStudy
from main.services import DataImportService, PatientService, StudyService


class PatientReferenceTest(TestCase):

	def setUp(self):
		self.user = User.objects.create_user(
			username='admin_ref_test',
			firstName='Admin',
			lastName='Tester',
		)
		self.user.is_staff = True
		self.user.is_superuser = True
		self.user.save()

		self.patient_service = PatientService()

		# REST API client
		self.api_client = APIClient()
		self.api_client.force_authenticate(user=self.user)

		# Admin UI client
		self.web_client = Client()
		self.web_client.force_login(self.user)

	def test_patient_reference_creation_and_normalization(self):
		"""Test that reference is saved, whitespace stripped, and empty string normalized to None."""
		p1 = Patient.objects.create(
			reference='  REF-001  ',
			firstName='Alice',
			lastName='Smith',
			createdBy=self.user,
		)
		self.assertEqual(p1.reference, 'REF-001')
		self.assertIn('[REF-001]', str(p1))

		# Empty string should normalize to None
		p2 = Patient.objects.create(
			reference='',
			firstName='Bob',
			lastName='Jones',
			createdBy=self.user,
		)
		self.assertIsNone(p2.reference)
		self.assertNotIn('[', str(p2))

		# Multiple patients with None/empty reference should not violate unique constraint
		p3 = Patient.objects.create(
			reference=None,
			firstName='Charlie',
			lastName='Brown',
			createdBy=self.user,
		)
		self.assertIsNone(p3.reference)

	def test_patient_reference_uniqueness_enforced(self):
		"""Test that non-null duplicate references raise an IntegrityError."""
		Patient.objects.create(
			reference='REF-UNIQUE-01',
			firstName='Diana',
			lastName='Prince',
			createdBy=self.user,
		)

		with self.assertRaises(IntegrityError):
			Patient.objects.create(
				reference='REF-UNIQUE-01',
				firstName='Another',
				lastName='Person',
				createdBy=self.user,
			)

	def test_service_reference_deterministic_matching(self):
		"""Test that _findBestMatchingPatient gives 100% confidence on matching reference."""
		p = Patient.objects.create(
			reference='PAT-MATCH-99',
			firstName='Original',
			lastName='Name',
			dateOfBirth=datetime.date(1990, 5, 10),
			createdBy=self.user,
		)

		# When reference matches, even if names differ slightly, it should return exact match
		match = self.patient_service._findBestMatchingPatient(
			firstname='DifferentName',
			lastname='DifferentLast',
			reference='PAT-MATCH-99',
		)
		self.assertIsNotNone(match)
		self.assertEqual(match['id'], p.id)
		self.assertEqual(match['reference'], 'PAT-MATCH-99')

	def test_api_create_and_search_by_reference(self):
		"""Test creating a patient with reference via REST API and searching for it."""
		# Create patient via API
		response = self.api_client.post('/api/v1/patient/create', {
			'reference': 'API-REF-777',
			'firstName': 'Gregory',
			'lastName': 'House',
			'gender': Gender.MALE.name,
		}, format='json')
		self.assertEqual(response.status_code, 201)
		data = response.json()
		patient_id = data['id'] if isinstance(data, dict) else data[0]['id']
		self.assertTrue(Patient.objects.filter(id=patient_id, reference='API-REF-777').exists())

		# Search by reference via POST /api/v1/patient/
		search_res = self.api_client.post(
			'/api/v1/patient/',
			{'search': 'API-REF-777', 'pagination': {'page': 1, 'limit': 20}},
			format='json',
		)
		self.assertEqual(search_res.status_code, 200)
		results = search_res.json()['results']
		self.assertEqual(len(results), 1)
		self.assertEqual(results[0]['reference'], 'API-REF-777')

		# Sort by reference
		Patient.objects.create(
			reference='AAA-FIRST',
			firstName='Aaron',
			lastName='Aardvark',
			createdBy=self.user,
		)
		sort_res = self.api_client.post(
			'/api/v1/patient/',
			{'sortField': 'reference', 'sortDirection': 'asc', 'pagination': {'page': 1, 'limit': 20}},
			format='json',
		)
		self.assertEqual(sort_res.status_code, 200)
		sorted_results = [r for r in sort_res.json()['results'] if r.get('reference')]
		self.assertGreaterEqual(len(sorted_results), 2)
		self.assertEqual(sorted_results[0]['reference'], 'AAA-FIRST')

	def test_single_view_page_and_modal(self):
		"""Test the single patient view page and quick view modal endpoints."""
		p = Patient.objects.create(
			reference='REF-PAGE-TEST',
			firstName='Sherlock',
			lastName='Holmes',
			dateOfBirth=datetime.date(1975, 1, 6),
			gender=Gender.MALE.name,
			notes='Consulting detective from Baker Street',
			createdBy=self.user,
		)

		# 1. Full single view page (GET /dashboard/patients/view/<pid>)
		view_response = self.web_client.get(f'/dashboard/patients/view/{p.id}')
		self.assertEqual(view_response.status_code, 200)
		content = view_response.content.decode('utf-8')
		self.assertIn('REF-PAGE-TEST', content)
		self.assertIn('Sherlock', content)
		self.assertIn('Holmes', content)
		self.assertIn('Consulting detective', content)

		# 2. Modal Quick View (POST /dashboard/patients/view/<pid>)
		modal_response = self.web_client.post(f'/dashboard/patients/view/{p.id}')
		self.assertEqual(modal_response.status_code, 200)
		modal_content = modal_response.content.decode('utf-8')
		self.assertIn('REF-PAGE-TEST', modal_content)
		self.assertIn('Sherlock', modal_content)

		# 3. Non-existent patient returns 404
		not_found_response = self.web_client.get('/dashboard/patients/view/999999')
		self.assertEqual(not_found_response.status_code, 404)

	def test_tier1_patient_id_matching(self):
		"""Tier 1: Direct patient_id match yields 100% confidence even if name differs."""
		p = Patient.objects.create(
			reference='REF-T1',
			firstName='Original',
			lastName='Patient',
			createdBy=self.user,
		)
		match = self.patient_service._findBestMatchingPatient(
			firstname='Unrelated',
			lastname='Person',
			patient_id=str(p.id),
		)
		self.assertIsNotNone(match)
		self.assertEqual(match['id'], p.id)

	def test_tier2_reference_matching(self):
		"""Tier 2: Reference match alone yields 100% confidence match."""
		p = Patient.objects.create(
			reference='REF-DOCTOR-55',
			firstName='Test',
			lastName='Case',
			createdBy=self.user,
		)
		match = self.patient_service._findBestMatchingPatient(
			firstname='Other',
			lastname='Name',
			reference='REF-DOCTOR-55',
		)
		self.assertIsNotNone(match)
		self.assertEqual(match['id'], p.id)
		self.assertEqual(match['reference'], 'REF-DOCTOR-55')

	def test_tier3_location_and_confirmed_demographics(self):
		"""Tier 3: Coordinates within 0.01 deg + confirmed demographics matches."""
		p = Patient.objects.create(
			reference=None,
			firstName='Emma',
			lastName='Watson',
			dateOfBirth=datetime.date(1990, 4, 15),
			gender=Gender.FEMALE.name,
			latitude=51.5074,
			longitude=-0.1278,
			createdBy=self.user,
		)
		# Close location (within 0.005 deg) with confirmed name & DOB
		match = self.patient_service._findBestMatchingPatient(
			firstname='Emma',
			lastname='Watson',
			dateofbirth='1990-04-15',
			gender='FEMALE',
			latitude='51.5080',
			longitude='-0.1280',
		)
		self.assertIsNotNone(match)
		self.assertEqual(match['id'], p.id)

	def test_tier3_rejection_without_location(self):
		"""Tier 3 rejection: Names and birthdays together without location NEVER match."""
		Patient.objects.create(
			reference=None,
			firstName='David',
			lastName='Miller',
			dateOfBirth=datetime.date(1985, 8, 20),
			createdBy=self.user,
		)
		# Even with exact first name, last name, and date of birth, without location it MUST NOT match
		match = self.patient_service._findBestMatchingPatient(
			firstname='David',
			lastname='Miller',
			dateofbirth='1985-08-20',
			latitude='',
			longitude='',
		)
		self.assertIsNone(match, 'Name and DOB alone without location must not match (anti-false-identification)')

	def test_dob_calculation_from_age_and_tested_date(self):
		"""DOB calculation anchors to tested_date.year - age, or current_year - age."""
		from django.conf import settings
		from django.utils import timezone
		from pathlib import Path

		upload_dir = Path(settings.MEDIA_ROOT) / 'uploads' / 'bulk'
		upload_dir.mkdir(parents=True, exist_ok=True)
		test_file = upload_dir / 'test_dob_calc.csv'
		test_file.write_text(
			"firstName,lastName,age,tested_date\n"
			"Alice,Wonderland,30,2015-06-10\n"
			"Bob,Builder,25,\n"
		)
		file_url = f'/media/uploads/bulk/{test_file.name}'

		mapping = {
			'firstName': 'firstName',
			'lastName': 'lastName',
			'age': 'age',
			'testedDate': 'tested_date',
		}
		result = self.patient_service.executeImport(file_url, mapping, created_by=self.user)
		self.assertEqual(result['imported'], 2)

		# Alice: 2015 - 30 = 1985 -> 1985-01-01
		alice = Patient.objects.get(firstName='Alice')
		self.assertEqual(str(alice.dateOfBirth), '1985-01-01')

		# Bob: current_year - 25 -> Jan 1
		expected_birth_year = timezone.now().year - 25
		bob = Patient.objects.get(firstName='Bob')
		self.assertEqual(str(bob.dateOfBirth), f'{expected_birth_year}-01-01')

		# Clean up test file
		if test_file.exists():
			test_file.unlink()

	def test_patient_template_download_contains_patient_id_and_reference(self):
		"""Test that patient template download includes PatientId and Reference."""
		res = self.api_client.get('/api/v1/patient/template?file_type=csv')
		self.assertEqual(res.status_code, 200)
		content = b''.join(res.streaming_content).decode('utf-8')
		first_line = content.splitlines()[0]
		self.assertIn('PatientId', first_line)
		self.assertIn('Reference', first_line)

	def test_dataset_template_download_contains_patient_id_and_reference(self):
		"""Test that dataset import template download includes PatientId and PatientReference."""
		study = Study.objects.create(
			name='Template Test Study',
			createdBy=self.user,
		)
		res = self.api_client.get(f'/api/v1/dataset/{study.id}/template?file_type=csv')
		self.assertEqual(res.status_code, 200)
		content = b''.join(res.streaming_content).decode('utf-8')
		first_line = content.splitlines()[0]
		self.assertIn('PatientId', first_line)
		self.assertIn('PatientReference', first_line)

	def test_bulk_dataset_multi_row_same_patient_without_tested_date(self):
		"""
		When a CSV contains multiple rows for the same patient and NO testedDate column is mapped/specified,
		each row must create a separate UserStudy record with unique offset past dates (today, today-1d, today-2d).
		None of the rows should be dropped or collapsed.
		"""
		from pathlib import Path
		from django.conf import settings
		from django.utils import timezone

		study = Study.objects.create(name='Multi Row Study', createdBy=self.user)
		upload_dir = Path(settings.MEDIA_ROOT) / 'uploads' / 'bulk'
		upload_dir.mkdir(parents=True, exist_ok=True)
		csv_file = upload_dir / 'test_multi_row_no_date.csv'
		csv_file.write_text(
			"Reference,FirstName,LastName\n"
			"PAT-MULTI-1,John,Doe\n"
			"PAT-MULTI-1,John,Doe\n"
			"PAT-MULTI-1,John,Doe\n"
		)
		file_url = f'/media/uploads/bulk/{csv_file.name}'

		import_service = DataImportService()
		mapping = {
			'patient': {
				'reference': 'Reference',
				'firstName': 'FirstName',
				'lastName': 'LastName',
			},
			'variables': {},
		}
		job = import_service.create_job(
			study_id=study.id,
			file_url=file_url,
			file_name=csv_file.name,
			mapping=mapping,
			column_types={'Reference': 'TEXT', 'FirstName': 'TEXT', 'LastName': 'TEXT'},
			total_rows=3,
			user=self.user,
		)
		DataImportService.execute_import_task(job.id)
		if csv_file.exists():
			csv_file.unlink()

		# Exactly 1 patient should exist
		patients = Patient.objects.filter(reference='PAT-MULTI-1')
		self.assertEqual(patients.count(), 1)
		patient = patients.first()

		# Exactly 3 UserStudy records should exist for this patient in this study
		user_studies = list(UserStudy.objects.filter(study=study, patient=patient).order_by('-testedDate'))
		self.assertEqual(len(user_studies), 3)

		today = timezone.now().date()
		tested_dates = [us.testedDate.date() for us in user_studies]
		self.assertEqual(len(set(tested_dates)), 3, "All testedDates must be unique")
		self.assertEqual(tested_dates, [today, today - datetime.timedelta(days=1), today - datetime.timedelta(days=2)])

	def test_sequential_import_jobs_without_tested_date_do_not_overwrite(self):
		"""
		Two sequential dataset imports on the same day for the same patient without tested_date
		must NOT overwrite earlier records. The second job must allocate offset past dates.
		"""
		from pathlib import Path
		from django.conf import settings
		from django.utils import timezone

		study = Study.objects.create(name='Sequential Import Study', createdBy=self.user)
		upload_dir = Path(settings.MEDIA_ROOT) / 'uploads' / 'bulk'
		upload_dir.mkdir(parents=True, exist_ok=True)

		import_service = DataImportService()
		mapping = {
			'patient': {'reference': 'Reference', 'firstName': 'FirstName'},
			'variables': {},
		}

		# Job 1: 1 row
		csv1 = upload_dir / 'test_seq_job1.csv'
		csv1.write_text("Reference,FirstName\nSEQ-PAT-1,Alice\n")
		job1 = import_service.create_job(
			study_id=study.id, file_url=f'/media/uploads/bulk/{csv1.name}',
			file_name=csv1.name, mapping=mapping, column_types={'Reference': 'TEXT'}, total_rows=1, user=self.user,
		)
		DataImportService.execute_import_task(job1.id)
		if csv1.exists():
			csv1.unlink()

		# Job 2: 1 row for same patient
		csv2 = upload_dir / 'test_seq_job2.csv'
		csv2.write_text("Reference,FirstName\nSEQ-PAT-1,Alice\n")
		job2 = import_service.create_job(
			study_id=study.id, file_url=f'/media/uploads/bulk/{csv2.name}',
			file_name=csv2.name, mapping=mapping, column_types={'Reference': 'TEXT'}, total_rows=1, user=self.user,
		)
		DataImportService.execute_import_task(job2.id)
		if csv2.exists():
			csv2.unlink()

		patient = Patient.objects.get(reference='SEQ-PAT-1')
		user_studies = list(UserStudy.objects.filter(study=study, patient=patient).order_by('-testedDate'))
		self.assertEqual(len(user_studies), 2, "Second job must create a new record, not overwrite")
		today = timezone.now().date()
		self.assertEqual([us.testedDate.date() for us in user_studies], [today, today - datetime.timedelta(days=1)])

	def test_bulk_dataset_multi_row_with_identical_explicit_date(self):
		"""
		When rows have explicit testedDate and a record already exists with that date:
		The first row updates the existing record, while subsequent rows allocate offset past dates.
		"""
		from pathlib import Path
		from django.conf import settings

		study = Study.objects.create(name='Explicit Date Collision Study', createdBy=self.user)
		patient = Patient.objects.create(reference='EXP-PAT-1', firstName='Bob', createdBy=self.user)
		existing_us = UserStudy.objects.create(
			study=study, patient=patient, reference='OLD-REF',
			testedDate=datetime.date(2026, 4, 15), createdBy=self.user,
		)

		upload_dir = Path(settings.MEDIA_ROOT) / 'uploads' / 'bulk'
		upload_dir.mkdir(parents=True, exist_ok=True)
		csv_file = upload_dir / 'test_explicit_collision.csv'
		# Two rows with identical date 2026-04-15
		csv_file.write_text(
			"Reference,TestedDate\n"
			"EXP-PAT-1,2026-04-15\n"
			"EXP-PAT-1,2026-04-15\n"
		)
		file_url = f'/media/uploads/bulk/{csv_file.name}'

		import_service = DataImportService()
		mapping = {
			'patient': {'reference': 'Reference', 'testedDate': 'TestedDate'},
			'variables': {},
		}
		job = import_service.create_job(
			study_id=study.id, file_url=file_url, file_name=csv_file.name,
			mapping=mapping, column_types={'Reference': 'TEXT', 'TestedDate': 'DATE'}, total_rows=2, user=self.user,
		)
		DataImportService.execute_import_task(job.id)
		if csv_file.exists():
			csv_file.unlink()

		user_studies = list(UserStudy.objects.filter(study=study, patient=patient).order_by('-testedDate'))
		self.assertEqual(len(user_studies), 2)
		# First row updated the existing 2026-04-15 record; second row created offset date (2026-04-14)
		self.assertIn(existing_us.id, [us.id for us in user_studies])
		self.assertEqual(
			[us.testedDate.date() for us in user_studies],
			[datetime.date(2026, 4, 15), datetime.date(2026, 4, 14)]
		)

	def test_preview_data_import_grouping_and_conditional_update(self):
		"""
		Test StudyService.previewDataImport:
		1. Groups multi-record rows under the same file_group (G1).
		2. Marks 'new' when testedDate is not mapped.
		3. When testedDate is mapped and exists: marks first row as 'update' and second row as 'new'.
		"""
		from pathlib import Path
		from django.conf import settings

		study = Study.objects.create(name='Preview Test Study', createdBy=self.user)
		patient = Patient.objects.create(reference='PREV-PAT-1', firstName='Clara', createdBy=self.user)
		UserStudy.objects.create(
			study=study, patient=patient, reference='PREV-US-1',
			testedDate=datetime.date(2026, 5, 20), createdBy=self.user,
		)

		upload_dir = Path(settings.MEDIA_ROOT) / 'uploads' / 'bulk'
		upload_dir.mkdir(parents=True, exist_ok=True)
		csv_file = upload_dir / 'test_preview_data.csv'
		csv_file.write_text(
			"Reference,TestedDate\n"
			"PREV-PAT-1,2026-05-20\n"
			"PREV-PAT-1,2026-05-20\n"
		)
		file_url = f'/media/uploads/bulk/{csv_file.name}'
		study_service = StudyService()

		# Case A: Mapping without testedDate -> both rows must be 'new'
		no_date_mapping = {
			'patient': {'reference': 'Reference'},
			'variables': {},
		}
		preview_a = study_service.previewDataImport(study.id, file_url, no_date_mapping)
		self.assertEqual(preview_a['stats']['update'], 0)
		self.assertEqual(preview_a['stats']['new'], 2)
		self.assertEqual(preview_a['stats']['fileDuplicates'], 1)
		rows_a = preview_a['previewData']
		self.assertEqual(rows_a[0]['_status'], 'new')
		self.assertEqual(rows_a[0]['_file_group'], 'G1')
		self.assertEqual(rows_a[1]['_status'], 'new')
		self.assertEqual(rows_a[1]['_file_group'], 'G1')
		self.assertEqual(rows_a[1]['_file_duplicate_of'], '2')

		# Case B: Mapping with testedDate -> row 1 is 'update', row 2 is 'new'
		with_date_mapping = {
			'patient': {'reference': 'Reference', 'testedDate': 'TestedDate'},
			'variables': {},
		}
		preview_b = study_service.previewDataImport(study.id, file_url, with_date_mapping)
		self.assertEqual(preview_b['stats']['update'], 1)
		self.assertEqual(preview_b['stats']['new'], 1)
		self.assertEqual(preview_b['stats']['fileDuplicates'], 1)
		rows_b = preview_b['previewData']
		self.assertEqual(rows_b[0]['_status'], 'update')
		self.assertEqual(rows_b[1]['_status'], 'new')

		if csv_file.exists():
			csv_file.unlink()


