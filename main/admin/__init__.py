from django.contrib import admin

from .BioMarkerAdmin import *
from .StudyAdmin import *
from .StudyVariableAdmin import *
from .UserStudyAdmin import *

from ..models import *

admin.site.register(BioMarker, BioMarkerAdmin)
admin.site.register(Study, StudyAdmin)
admin.site.register(StudyVariable, StudyVariableAdmin)
admin.site.register(UserStudy, UserStudyAdmin)