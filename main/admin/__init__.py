from django.contrib import admin

from .BioMarkerAdmin import BioMarkerAdmin
from .StudyAdmin import StudyAdmin
from .StudyVariableAdmin import StudyVariableAdmin
from .UserStudyAdmin import UserStudyAdmin
from .PatientAdmin import PatientAdmin

from ..models import BioMarker, Study, StudyVariable, UserStudy, Patient

admin.site.register(BioMarker, BioMarkerAdmin)
admin.site.register(Study, StudyAdmin)
admin.site.register(StudyVariable, StudyVariableAdmin)
admin.site.register(UserStudy, UserStudyAdmin)
admin.site.register(Patient, PatientAdmin)