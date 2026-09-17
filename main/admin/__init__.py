from django.contrib import admin

from ..models import (
	BioMarker, DataImportJob, Patient, PatientPlace, Study, StudyVariable, UserStudy,
)
from .BioMarkerAdmin import BioMarkerAdmin
from .DataImportJobAdmin import DataImportJobAdmin
from .PatientAdmin import PatientAdmin
from .PatientPlaceAdmin import PatientPlaceAdmin
from .StudyAdmin import StudyAdmin
from .StudyVariableAdmin import StudyVariableAdmin
from .UserStudyAdmin import UserStudyAdmin

admin.site.register(BioMarker, BioMarkerAdmin)
admin.site.register(Study, StudyAdmin)
admin.site.register(StudyVariable, StudyVariableAdmin)
admin.site.register(UserStudy, UserStudyAdmin)
admin.site.register(Patient, PatientAdmin)
admin.site.register(PatientPlace, PatientPlaceAdmin)
admin.site.register(DataImportJob, DataImportJobAdmin)
