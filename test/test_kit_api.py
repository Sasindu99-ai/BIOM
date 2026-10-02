import json
from datetime import date, timedelta

from django.test import Client, TestCase
from django.utils import timezone

from authentication.enums import Gender
from authentication.models import ApiKey, User
from main.enums import StudyStatus, StudyVariableType, UserStudyStatus
from main.models import Patient, Study, StudyResult, StudyVariable, UserStudy


class KitApiTest(TestCase):

	def setUp(self):
		self.client = Client()

		# Create staff user and API key
		self.user = User.objects.create_user(
			username='staff_kit_user',
			firstName='Staff',
			lastName='Scientist',
		)
		self.user.is_staff = True
		self.user.is_superuser = True
		self.user.save()

		self.api_key, self.raw_key = ApiKey.create_key_for_user(self.user)
		self.headers = {'HTTP_X_API_KEY': self.raw_key}

		# Create sample study and variables
		self.study = Study.objects.create(
			name='Cardiovascular Cohort',
			reference='CV-TEST-01',
			status=StudyStatus.ACTIVE,
			category='CLINICAL',
		)

		self.var_glucose = StudyVariable.objects.create(
			name='Glucose',
			type=StudyVariableType.NUMBER,
			isSearchable=True,
		)
		self.var_smoker = StudyVariable.objects.create(
			name='Smoker',
			type=StudyVariableType.BOOLEAN,
			isSearchable=True,
		)
		self.study.variables.add(self.var_glucose, self.var_smoker)

		# Create Patient 1: 35yo Female, Glucose=115, Smoker=True
		today = timezone.now().date()
		p1_dob = date(today.year - 35, today.month, today.day)
		self.p1 = Patient.objects.create(
			firstName='Alice',
			lastName='Baker',
			gender=Gender.FEMALE,
			dateOfBirth=p1_dob,
		)
		self.us1 = UserStudy.objects.create(
			study=self.study,
			patient=self.p1,
			reference='REF-001',
			status=UserStudyStatus.APPROVED,
		)
		StudyResult.objects.create(userStudy=self.us1, studyVariable=self.var_glucose, value='115')
		StudyResult.objects.create(userStudy=self.us1, studyVariable=self.var_smoker, value='True')

		# Create Patient 2: 55yo Male, Glucose=90, Smoker=False
		p2_dob = date(today.year - 55, today.month, today.day)
		self.p2 = Patient.objects.create(
			firstName='Bob',
			lastName='Carter',
			gender=Gender.MALE,
			dateOfBirth=p2_dob,
		)
		self.us2 = UserStudy.objects.create(
			study=self.study,
			patient=self.p2,
			reference='REF-002',
			status=UserStudyStatus.APPROVED,
		)
		StudyResult.objects.create(userStudy=self.us2, studyVariable=self.var_glucose, value='90')
		StudyResult.objects.create(userStudy=self.us2, studyVariable=self.var_smoker, value='False')

	def test_verify_auth_endpoint(self):
		# Anonymous request
		res = self.client.get('/api/v1/kit/auth/verify')
		self.assertEqual(res.status_code, 401)

		# Authenticated with X-API-Key
		res = self.client.get('/api/v1/kit/auth/verify', **self.headers)
		self.assertEqual(res.status_code, 200)
		data = res.json()
		self.assertEqual(data.get('status'), 'success')
		self.assertEqual(data.get('user', {}).get('username'), 'staff_kit_user')
		self.assertTrue(data.get('user', {}).get('isStaff'))

	def test_get_fields_endpoint(self):
		res = self.client.get('/api/v1/kit/fields', **self.headers)
		self.assertEqual(res.status_code, 200)
		data = res.json()
		self.assertIn('fields', data)
		self.assertIn('typeOperators', data)
		field_keys = [f['key'] for f in data['fields']]
		self.assertIn('age', field_keys)
		self.assertIn('gender', field_keys)
		self.assertIn('patientId', field_keys)

	def test_get_datasets_endpoint(self):
		res = self.client.get('/api/v1/kit/datasets', **self.headers)
		self.assertEqual(res.status_code, 200)
		data = res.json()
		self.assertIn('datasets', data)
		datasets = data['datasets']
		self.assertTrue(len(datasets) >= 1)
		matched = next((d for d in datasets if d['id'] == self.study.id), None)
		self.assertIsNotNone(matched)
		self.assertEqual(matched['name'], 'Cardiovascular Cohort')
		self.assertEqual(matched['recordCount'], 2)
		self.assertEqual(matched['variableCount'], 2)

	def test_get_dataset_variables_endpoint(self):
		res = self.client.get(f'/api/v1/kit/datasets/{self.study.id}/variables', **self.headers)
		self.assertEqual(res.status_code, 200)
		data = res.json()
		self.assertIn('variables', data)
		var_names = [v['name'] for v in data['variables']]
		self.assertIn('Glucose', var_names)
		self.assertIn('Smoker', var_names)

	def test_search_variables_endpoint(self):
		res = self.client.get('/api/v1/kit/variables/search?q=gluc', **self.headers)
		self.assertEqual(res.status_code, 200)
		data = res.json()
		self.assertIn('variables', data)
		names = [v['name'] for v in data['variables']]
		self.assertIn('Glucose', names)

	def test_query_filtering_known_field(self):
		# Filter for age >= 50 (should only match Bob, age 55)
		payload = {
			'dataset': self.study.id,
			'filters': [
				{'field': 'age', 'operator': 'gte', 'value': 50, 'scope': 'known'},
			],
		}
		res = self.client.post(
			'/api/v1/kit/query',
			data=json.dumps(payload),
			content_type='application/json',
			**self.headers,
		)
		self.assertEqual(res.status_code, 200)
		data = res.json()
		self.assertEqual(data.get('meta', {}).get('totalRecords'), 1)
		records = data.get('records', [])
		self.assertEqual(len(records), 1)
		self.assertEqual(records[0]['firstName'], 'Bob')
		self.assertEqual(records[0]['Glucose'], '90')

	def test_query_filtering_study_variable(self):
		# Filter for Glucose > 100 (should only match Alice, Glucose 115)
		payload = {
			'dataset': self.study.id,
			'filters': [
				{'field': 'Glucose', 'operator': 'gt', 'value': 100, 'scope': 'variable'},
			],
		}
		res = self.client.post(
			'/api/v1/kit/query',
			data=json.dumps(payload),
			content_type='application/json',
			**self.headers,
		)
		self.assertEqual(res.status_code, 200)
		data = res.json()
		self.assertEqual(data.get('meta', {}).get('totalRecords'), 1)
		records = data.get('records', [])
		self.assertEqual(len(records), 1)
		self.assertEqual(records[0]['firstName'], 'Alice')
		self.assertEqual(records[0]['Glucose'], '115')

	def test_query_combined_and_or_logic(self):
		# Filter (gender == 'Female' AND Glucose > 100) -> Alice
		payload_and = {
			'dataset': self.study.id,
			'filterLogic': 'AND',
			'filters': [
				{'field': 'gender', 'operator': 'equals', 'value': 'Female', 'scope': 'known'},
				{'field': 'Glucose', 'operator': 'gt', 'value': 100, 'scope': 'variable'},
			],
		}
		res = self.client.post(
			'/api/v1/kit/query',
			data=json.dumps(payload_and),
			content_type='application/json',
			**self.headers,
		)
		data = res.json()
		self.assertEqual(data['meta']['totalRecords'], 1)

		# Filter (age < 30 OR age > 50) -> Bob (55)
		payload_or = {
			'dataset': self.study.id,
			'filterLogic': 'OR',
			'filters': [
				{'field': 'age', 'operator': 'lt', 'value': 30, 'scope': 'known'},
				{'field': 'age', 'operator': 'gt', 'value': 50, 'scope': 'known'},
			],
		}
		res_or = self.client.post(
			'/api/v1/kit/query',
			data=json.dumps(payload_or),
			content_type='application/json',
			**self.headers,
		)
		data_or = res_or.json()
		self.assertEqual(data_or['meta']['totalRecords'], 1)
		self.assertEqual(data_or['records'][0]['firstName'], 'Bob')

	def test_query_field_projection(self):
		payload = {
			'dataset': self.study.id,
			'fields': ['firstName', 'Glucose'],
		}
		res = self.client.post(
			'/api/v1/kit/query',
			data=json.dumps(payload),
			content_type='application/json',
			**self.headers,
		)
		self.assertEqual(res.status_code, 200)
		data = res.json()
		records = data.get('records', [])
		self.assertEqual(len(records), 2)
		record = records[0]
		self.assertIn('firstName', record)
		self.assertIn('Glucose', record)
		self.assertNotIn('lastName', record)
		self.assertNotIn('Smoker', record)

	def test_query_pagination(self):
		payload = {
			'dataset': self.study.id,
			'limit': 1,
			'page': 1,
		}
		res = self.client.post(
			'/api/v1/kit/query',
			data=json.dumps(payload),
			content_type='application/json',
			**self.headers,
		)
		self.assertEqual(res.status_code, 200)
		data = res.json()
		self.assertEqual(data['meta']['page'], 1)
		self.assertEqual(data['meta']['limit'], 1)
		self.assertEqual(len(data['records']), 1)
		self.assertEqual(data['meta']['totalRecords'], 2)

	def test_query_unauthorized_user(self):
		# Non-staff user without permissions
		non_staff = User.objects.create_user(
			username='regular_kit_user',
			firstName='Regular',
			lastName='User',
		)
		non_staff.is_staff = False
		non_staff.save()
		_, raw_non_staff_key = ApiKey.create_key_for_user(non_staff)

		res = self.client.post(
			'/api/v1/kit/query',
			data=json.dumps({'dataset': self.study.id}),
			content_type='application/json',
			HTTP_X_API_KEY=raw_non_staff_key,
		)
		# Should be 401 or 403 Forbidden
		self.assertIn(res.status_code, [401, 403])

