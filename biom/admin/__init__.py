from django.contrib import admin

from ..models import BioMarker, Counters, Study, StudyResult, StudyVariable, User
from .BioMarkerAdmin import BioMarkerAdmin
from .CountersAdmin import CountersAdmin
from .StudyAdmin import StudyAdmin
from .StudyResultAdmin import StudyResultAdmin
from .StudyVariableAdmin import StudyVariableAdmin
from .UserAdmin import UserAdmin

admin.site.register(BioMarker, BioMarkerAdmin)
admin.site.register(Counters, CountersAdmin)
admin.site.register(Study, StudyAdmin)
admin.site.register(StudyResult, StudyResultAdmin)
admin.site.register(StudyVariable, StudyVariableAdmin)
admin.site.register(User, UserAdmin)
