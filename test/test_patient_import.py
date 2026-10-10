import datetime
import io
from pathlib import Path
import pandas as pd
from django.conf import settings
from django.test import TestCase
from rest_framework.test import APIClient

from authentication.models import User
from authentication.enums import Gender
from main.models import Patient
from main.services import PatientService


class PatientImportComprehensiveTest(TestCase):

	def setUp(self):
		self.user = User.objects.create_user(
			username='admin_test',
			firstName='Admin',
			lastName='User',
		)
		self.user.is_staff = True
		self.user.is_superuser = True
		self.user.save()

		self.service = PatientService()
		self.client = APIClient()
		self.client.force_authenticate(user=self.user)

	def test_import_from_template_csv(self):
		uploads_dir = Path(settings.MEDIA_ROOT) / 'uploads' / 'bulk'
		uploads_dir.mkdir(parents=True, exist_ok=True)
		csv_file = uploads_dir / 'template_sample.csv'

		headers = [
			'Reference', 'FirstName', 'LastName', 'DateOfBirth', 'Age', 'Gender',
			'Email', 'Phone', 'Address', 'City', 'State', 'PostalCode', 'Country', 'Notes',
		]
		sample_data = [
			['P-001', 'John', 'Doe', '1985-06-15', '', 'Male', 'john.doe@example.com', '+1234567890', '123 Main St', 'New York', 'NY', '10001', 'USA', ''],
			['P-002', 'Jane', 'Smith', '', '32', 'Female', 'jane.smith@example.com', '+0987654321', '456 Oak Ave', 'Los Angeles', 'CA', '90001', 'USA', ''],
			['P-003', 'Robert', 'Johnson', '1990-03-22', '', 'Male', '', '', '', '', '', '', '', ''],
		]
		df = pd.DataFrame(sample_data, columns=headers)
		df.to_csv(csv_file, index=False)

		file_url = f'/media/uploads/bulk/{csv_file.name}'

		# Step 1: Preview without mapping (auto-detect)
		preview = self.service.previewImport(file_url)
		self.assertEqual(preview['stats']['total'], 3)
		self.assertEqual(len(preview['validation_errors']), 0)

		# Step 2: Execute import
		result = self.service.executeImport(
			file_url=file_url,
			column_mapping=preview['final_mapping'],
			created_by=self.user,
		)
		if csv_file.exists():
			csv_file.unlink()

		self.assertEqual(result['imported'], 3)
		self.assertEqual(result['failed'], 0)

	def test_import_excel_xlsx(self):
		uploads_dir = Path(settings.MEDIA_ROOT) / 'uploads' / 'bulk'
		uploads_dir.mkdir(parents=True, exist_ok=True)
		xlsx_file = uploads_dir / 'test_patients.xlsx'

		data = [
			{'First Name': 'Alice', 'Last Name': 'Wonderland', 'DOB': '1992-04-10', 'Gender': 'Female'},
			{'First Name': 'Bob', 'Last Name': 'Builder', 'Age': 45, 'Gender': 'Male'},
		]
		df = pd.DataFrame(data)
		df.to_excel(xlsx_file, index=False)

		file_url = f'/media/uploads/bulk/{xlsx_file.name}'

		preview = self.service.previewImport(file_url)
		self.assertEqual(preview['stats']['total'], 2)

		result = self.service.executeImport(
			file_url=file_url,
			column_mapping=preview['final_mapping'],
			created_by=self.user,
		)
		if xlsx_file.exists():
			xlsx_file.unlink()

		self.assertEqual(result['imported'], 2)
		self.assertEqual(result['failed'], 0)

	def test_import_with_full_name_mapping(self):
		uploads_dir = Path(settings.MEDIA_ROOT) / 'uploads' / 'bulk'
		uploads_dir.mkdir(parents=True, exist_ok=True)
		csv_file = uploads_dir / 'test_fullname.csv'

		data = [
			{'Full Name': 'Clark Kent', 'Gender': 'Male'},
			{'Full Name': 'Diana Prince', 'Gender': 'Female'},
			{'Full Name': 'Cher', 'Gender': 'Female'},
		]
		df = pd.DataFrame(data)
		df.to_csv(csv_file, index=False)
		file_url = f'/media/uploads/bulk/{csv_file.name}'

		mapping = {
			'fullName': 'Full Name',
			'gender': 'Gender',
		}

		result = self.service.executeImport(
			file_url=file_url,
			column_mapping=mapping,
			created_by=self.user,
		)
		if csv_file.exists():
			csv_file.unlink()

		self.assertEqual(result['imported'], 3)
		p1 = Patient.objects.get(firstName='Clark')
		self.assertEqual(p1.lastName, 'Kent')
		p2 = Patient.objects.get(firstName='Diana')
		self.assertEqual(p2.lastName, 'Prince')
		p3 = Patient.objects.get(firstName='Cher')
		self.assertFalse(p3.lastName)

	def test_gender_normalization(self):
		uploads_dir = Path(settings.MEDIA_ROOT) / 'uploads' / 'bulk'
		uploads_dir.mkdir(parents=True, exist_ok=True)
		csv_file = uploads_dir / 'test_gender.csv'

		data = [
			{'firstName': 'G1', 'gender': 'M'},
			{'firstName': 'G2', 'gender': 'female'},
			{'firstName': 'G3', 'gender': 'Prefer Not to Say'},
			{'firstName': 'G4', 'gender': 'Unknown / Other'},
			{'firstName': 'G5', 'gender': ''},
		]
		df = pd.DataFrame(data)
		df.to_csv(csv_file, index=False)
		file_url = f'/media/uploads/bulk/{csv_file.name}'

		mapping = {'firstName': 'firstName', 'gender': 'gender'}
		result = self.service.executeImport(
			file_url=file_url,
			column_mapping=mapping,
			created_by=self.user,
		)
		if csv_file.exists():
			csv_file.unlink()

		self.assertEqual(result['imported'], 5)
		self.assertEqual(Patient.objects.get(firstName='G1').gender, Gender.MALE.value)
		self.assertEqual(Patient.objects.get(firstName='G2').gender, Gender.FEMALE.value)
		self.assertEqual(Patient.objects.get(firstName='G3').gender, Gender.PREFER_NOT_TO_SAY.value)
		self.assertEqual(Patient.objects.get(firstName='G4').gender, Gender.PREFER_NOT_TO_SAY.value)
		self.assertEqual(Patient.objects.get(firstName='G5').gender, Gender.PREFER_NOT_TO_SAY.value)

	def test_duplicate_detection_distinguishes_different_last_names(self):
		# Pre-existing patient
		existing = Patient.objects.create(
			firstName='John',
			lastName='Doe',
			dateOfBirth=datetime.date(1990, 1, 1),
			gender=Gender.MALE.value,
			latitude=40.7128,
			longitude=-74.0060,
			createdBy=self.user,
		)

		uploads_dir = Path(settings.MEDIA_ROOT) / 'uploads' / 'bulk'
		uploads_dir.mkdir(parents=True, exist_ok=True)
		csv_file = uploads_dir / 'test_duplicates.csv'

		data = [
			# Row 0: Exact match with existing (location + demographics) -> Duplicate
			{'First Name': 'John', 'Last Name': 'Doe', 'DOB': '1990-01-01', 'Gender': 'Male', 'Lat': '40.7128', 'Lng': '-74.0060'},
			# Row 1: Same location and first name, different last name -> NOT duplicate!
			{'First Name': 'John', 'Last Name': 'Smith', 'DOB': '1995-05-05', 'Gender': 'Male', 'Lat': '40.7128', 'Lng': '-74.0060'},
			# Row 2: Completely new patient -> New
			{'First Name': 'Jane', 'Last Name': 'Watson', 'DOB': '1992-02-02', 'Gender': 'Female', 'Lat': '34.0522', 'Lng': '-118.2437'},
		]
		df = pd.DataFrame(data)
		df.to_csv(csv_file, index=False)
		file_url = f'/media/uploads/bulk/{csv_file.name}'

		mapping = {
			'firstName': 'First Name',
			'lastName': 'Last Name',
			'dateOfBirth': 'DOB',
			'gender': 'Gender',
			'latitude': 'Lat',
			'longitude': 'Lng',
		}

		preview = self.service.previewImport(file_url, column_mapping=mapping)
		self.assertEqual(preview['stats']['duplicates'], 1)
		dup_row_indices = [d['row_index'] for d in preview['duplicates']]
		self.assertIn(0, dup_row_indices)
		self.assertNotIn(1, dup_row_indices)

		# Execute with action 'skip' for row 0
		result = self.service.executeImport(
			file_url=file_url,
			column_mapping=mapping,
			duplicate_actions={'0': 'skip'},
			created_by=self.user,
		)
		if csv_file.exists():
			csv_file.unlink()

		self.assertEqual(result['imported'], 2)
		self.assertEqual(result['skipped'], 1)
		self.assertEqual(result['updated'], 0)
		self.assertEqual(result['failed'], 0)

		# Verify John Smith and Jane Watson were created, John Doe still exists
		self.assertTrue(Patient.objects.filter(firstName='John', lastName='Smith').exists())
		self.assertTrue(Patient.objects.filter(firstName='Jane', lastName='Watson').exists())

	def test_failed_rows_posix_path_and_generation(self):
		uploads_dir = Path(settings.MEDIA_ROOT) / 'uploads' / 'bulk'
		uploads_dir.mkdir(parents=True, exist_ok=True)
		csv_file = uploads_dir / 'test_failed.csv'

		data = [
			# Row 0: Valid
			{'First Name': 'Bruce', 'Last Name': 'Banner'},
			# Row 1: Invalid (no name and no coordinates)
			{'First Name': '', 'Last Name': ''},
		]
		df = pd.DataFrame(data)
		df.to_csv(csv_file, index=False)
		file_url = f'/media/uploads/bulk/{csv_file.name}'

		mapping = {'firstName': 'First Name', 'lastName': 'Last Name'}
		result = self.service.executeImport(
			file_url=file_url,
			column_mapping=mapping,
			created_by=self.user,
		)
		if csv_file.exists():
			csv_file.unlink()

		self.assertEqual(result['imported'], 1)
		self.assertEqual(result['failed'], 1)
		self.assertIsNotNone(result['failed_rows_file'])
		# Must use forward slash, not Windows backslash
		self.assertNotIn('\\', result['failed_rows_file'])

		failed_disk_path = Path(settings.MEDIA_ROOT) / result['failed_rows_file']
		self.assertTrue(failed_disk_path.exists())
		failed_disk_path.unlink()

	def test_template_download_endpoints(self):
		# CSV template
		csv_res = self.client.get('/api/v1/patient/template?file_type=csv')
		self.assertEqual(csv_res.status_code, 200)
		self.assertIn('text/csv', csv_res['Content-Type'])

		# Excel template
		xlsx_res = self.client.get('/api/v1/patient/template?file_type=xlsx')
		self.assertEqual(xlsx_res.status_code, 200)
		self.assertIn('spreadsheetml.sheet', xlsx_res['Content-Type'])

	def test_api_endpoints(self):
		uploads_dir = Path(settings.MEDIA_ROOT) / 'uploads' / 'bulk'
		uploads_dir.mkdir(parents=True, exist_ok=True)
		csv_file = uploads_dir / 'api_test.csv'

		df = pd.DataFrame([
			{'firstName': 'Charlie', 'lastName': 'Brown', 'dateOfBirth': '2000-01-01', 'gender': 'Male'}
		])
		df.to_csv(csv_file, index=False)
		file_url = f'/media/uploads/bulk/{csv_file.name}'

		# Test preview endpoint
		preview_res = self.client.post('/api/v1/patient/import/preview', {'file_url': file_url}, format='json')
		self.assertEqual(preview_res.status_code, 200)
		self.assertEqual(preview_res.data['stats']['total'], 1)

		# Test execute endpoint
		exec_res = self.client.post('/api/v1/patient/import/execute', {
			'file_url': file_url,
			'column_mapping': preview_res.data['final_mapping']
		}, format='json')
		self.assertEqual(exec_res.status_code, 200)
		self.assertEqual(exec_res.data['imported'], 1)

		if csv_file.exists():
			csv_file.unlink()

	def test_duplicate_action_update(self):
		existing = Patient.objects.create(
			firstName='Clark',
			lastName='Kent',
			dateOfBirth=datetime.date(1980, 5, 5),
			gender=Gender.MALE.value,
			latitude=40.7128,
			longitude=-74.0060,
			notes='Original notes',
			createdBy=self.user,
		)

		uploads_dir = Path(settings.MEDIA_ROOT) / 'uploads' / 'bulk'
		uploads_dir.mkdir(parents=True, exist_ok=True)
		csv_file = uploads_dir / 'test_dup_update.csv'

		data = [
			{'First Name': 'Clark', 'Last Name': 'Kent', 'DOB': '1980-05-05', 'Gender': 'Male', 'Notes': 'Updated notes', 'Lat': '40.7128', 'Lng': '-74.0060'},
		]
		df = pd.DataFrame(data)
		df.to_csv(csv_file, index=False)
		file_url = f'/media/uploads/bulk/{csv_file.name}'

		mapping = {
			'firstName': 'First Name',
			'lastName': 'Last Name',
			'dateOfBirth': 'DOB',
			'gender': 'Gender',
			'notes': 'Notes',
			'latitude': 'Lat',
			'longitude': 'Lng',
		}

		result = self.service.executeImport(
			file_url=file_url,
			column_mapping=mapping,
			duplicate_actions={'0': 'update'},
			created_by=self.user,
		)
		if csv_file.exists():
			csv_file.unlink()

		self.assertEqual(result['updated'], 1)
		self.assertEqual(result['imported'], 0)
		existing.refresh_from_db()
		self.assertEqual(existing.notes, 'Updated notes')

	def test_excel_timestamp_and_float_age(self):
		uploads_dir = Path(settings.MEDIA_ROOT) / 'uploads' / 'bulk'
		uploads_dir.mkdir(parents=True, exist_ok=True)
		xlsx_file = uploads_dir / 'test_timestamp.xlsx'

		# Data with pandas Timestamp and float age
		data = [
			{'Name': 'Barry Allen', 'DOB': pd.Timestamp('1990-09-20 00:00:00'), 'Age': None, 'Gender': 'Male'},
			{'Name': 'Hal Jordan', 'DOB': None, 'Age': 35.0, 'Gender': 'Male'},
		]
		df = pd.DataFrame(data)
		df.to_excel(xlsx_file, index=False)
		file_url = f'/media/uploads/bulk/{xlsx_file.name}'

		mapping = {
			'fullName': 'Name',
			'dateOfBirth': 'DOB',
			'age': 'Age',
			'gender': 'Gender',
		}

		result = self.service.executeImport(
			file_url=file_url,
			column_mapping=mapping,
			created_by=self.user,
		)
		if xlsx_file.exists():
			xlsx_file.unlink()

		self.assertEqual(result['imported'], 2)
		p1 = Patient.objects.get(firstName='Barry')
		self.assertEqual(p1.dateOfBirth, datetime.date(1990, 9, 20))

		p2 = Patient.objects.get(firstName='Hal')
		current_year = datetime.date.today().year
		self.assertEqual(p2.dateOfBirth, datetime.date(current_year - 35, 1, 1))

