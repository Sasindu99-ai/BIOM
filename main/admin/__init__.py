from django.contrib import admin

from ..models import BioMarker, Patient, Study, StudyVariable, UserStudy
from .BioMarkerAdmin import BioMarkerAdmin
from .PatientAdmin import PatientAdmin
from .StudyAdmin import StudyAdmin
from .StudyVariableAdmin import StudyVariableAdmin
from .UserStudyAdmin import UserStudyAdmin

admin.site.register(BioMarker, BioMarkerAdmin)
admin.site.register(Study, StudyAdmin)
admin.site.register(StudyVariable, StudyVariableAdmin)
admin.site.register(UserStudy, UserStudyAdmin)
admin.site.register(Patient, PatientAdmin)
