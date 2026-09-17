import heapq

from django.db.models import Count
from django.db.models.functions import TruncMonth
from django.utils import timezone

from authentication.enums import Gender
from main.enums import BioMarkerStatus, StudyStatus, UserStudyStatus
from main.models import BioMarker, DataImportJob, Patient, Study, StudyResult, UserStudy
from main.models.DataImportJob import DataImportJobStatus
from res import R
from vvecon.zorion.auth import Authenticated
from vvecon.zorion.views import GetMapping, Mapping, View

__all__ = ['HomeView']

RECENT_ACTIVITY_LIMIT = 8
ENROLLMENT_TREND_MONTHS = 6
AGE_BUCKETS = (18, 30, 45, 60, 75)


@Mapping('dashboard')
class HomeView(View):
	R: R = R()

	def adminConfig(self):
		self.R.data.navigator.enabled = True
		self.R.data.aside['admin'].enabled = True

	def _stats(self):
		return {
			'totalStudies': Study.objects.count(),
			'totalPatients': Patient.objects.count(),
			'totalResults': StudyResult.objects.count(),
			'pendingBiomarkers': BioMarker.objects.filter(status=BioMarkerStatus.PENDING).count(),
			'activeImports': DataImportJob.objects.filter(
				status__in=[DataImportJobStatus.PENDING, DataImportJobStatus.RUNNING],
			).count(),
			'pendingEnrollments': UserStudy.objects.filter(status=UserStudyStatus.PENDING).count(),
		}

	def _recentActivity(self):
		events = []

		for study in Study.objects.select_related('createdBy').order_by('-created_at')[:RECENT_ACTIVITY_LIMIT]:
			events.append({
				'type': 'study',
				'icon': 'bi-database-fill',
				'timestamp': study.created_at,
				'description': f'Dataset "{study.name}" was created',
				'user': study.createdBy.fullName if study.createdBy else None,
				'url': f'/dashboard/datasets/view/{study.pk}',
			})

		for patient in Patient.objects.select_related('createdBy').order_by('-created_at')[:RECENT_ACTIVITY_LIMIT]:
			events.append({
				'type': 'patient',
				'icon': 'bi-person-fill',
				'timestamp': patient.created_at,
				'description': f'Patient "{patient.fullName}" was added',
				'user': patient.createdBy.fullName if patient.createdBy else None,
				'url': None,
			})

		for job in DataImportJob.objects.select_related('study', 'created_by').order_by('-created_at')[:RECENT_ACTIVITY_LIMIT]:
			events.append({
				'type': 'import',
				'icon': 'bi-cloud-arrow-up-fill',
				'timestamp': job.created_at,
				'description': f'Import "{job.file_name}" into "{job.study.name}" is {job.status.lower()}',
				'user': job.created_by.fullName if job.created_by else None,
				'url': f'/dashboard/datasets/view/{job.study_id}',
			})

		for biomarker in BioMarker.objects.select_related('uploadedBy').order_by('-created_at')[:RECENT_ACTIVITY_LIMIT]:
			events.append({
				'type': 'biomarker',
				'icon': 'bi-clipboard2-pulse-fill',
				'timestamp': biomarker.created_at,
				'description': f'Biomarker "{biomarker.name}" was submitted ({biomarker.status.lower()})',
				'user': biomarker.uploadedBy.fullName if biomarker.uploadedBy else None,
				'url': None,
			})

		return heapq.nlargest(RECENT_ACTIVITY_LIMIT, events, key=lambda event: event['timestamp'])

	@staticmethod
	def _labelFor(choicesEnum, value):
		try:
			return choicesEnum(value).label
		except ValueError:
			return value or 'Unknown'

	def _studyStatusChart(self):
		counts = dict(
			Study.objects.values_list('status').annotate(count=Count('id')).order_by(),
		)
		return {
			'labels': [self._labelFor(StudyStatus, status) for status in counts],
			'values': list(counts.values()),
		}

	def _genderChart(self):
		counts = dict(
			Patient.objects.values_list('gender').annotate(count=Count('id')).order_by(),
		)
		return {
			'labels': [self._labelFor(Gender, gender) for gender in counts],
			'values': list(counts.values()),
		}

	def _ageDistributionChart(self):
		bucketLabels = [f'<{AGE_BUCKETS[0]}'] + [
			f'{lo}-{hi - 1}' for lo, hi in zip(AGE_BUCKETS, AGE_BUCKETS[1:])
		] + [f'{AGE_BUCKETS[-1]}+']
		bucketCounts = [0] * len(bucketLabels)

		for age in Patient.objects.exclude(dateOfBirth=None).values_list('dateOfBirth', flat=True):
			years = (timezone.now().date() - age).days // 365
			index = next((i for i, threshold in enumerate(AGE_BUCKETS) if years < threshold), len(AGE_BUCKETS))
			bucketCounts[index] += 1

		return {'labels': bucketLabels, 'values': bucketCounts}

	def _enrollmentTrendChart(self):
		since = timezone.now() - timezone.timedelta(days=30 * ENROLLMENT_TREND_MONTHS)
		rows = (
			UserStudy.objects
			.filter(created_at__gte=since)
			.annotate(month=TruncMonth('created_at'))
			.values('month')
			.annotate(count=Count('id'))
			.order_by('month')
		)
		return {
			'labels': [row['month'].strftime('%b %Y') for row in rows],
			'values': [row['count'] for row in rows],
		}

	@GetMapping('/')
	@Authenticated(staff=True)
	def home(self, request):
		self.adminConfig()

		self.R.data.aside['admin'].activeSlug = 'dashboard'

		context = {
			'stats': self._stats(),
			'activity': self._recentActivity(),
			'now': timezone.now(),
			'charts': {
				'studyStatus': self._studyStatusChart(),
				'gender': self._genderChart(),
				'ageDistribution': self._ageDistributionChart(),
				'enrollmentTrend': self._enrollmentTrendChart(),
			},
		}

		return self.render(request, context, 'dashboard/home')
