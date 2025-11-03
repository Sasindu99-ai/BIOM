from django.db.models import Count
from vvecon.zorion.core import Service
from ..models import Patient

__all__ = ['PatientService']


class PatientService(Service):
	model = Patient
	searchableFields = ('fullName', 'notes')
	filterableFields = ('dateOfBirth', 'gender', 'createdBy')
	annotations = dict(userStudiesCount=Count('userStudies'))
