from main.models import BioMarker, Patient, Study
from res import R
from settings.models import Setting
from settings.services import TeamService
from vvecon.zorion.views import GetMapping, Mapping, View

__all__ = ['AboutView']


@Mapping('about')
class AboutView(View):
    R: R = R()
    teamService: TeamService = TeamService()

    def homeConfig(self):
        self.R.data.navigator.enabled = True
        self.R.data.footer.enabled = True

    @GetMapping('/')
    def about(self, request):
        self.homeConfig()
        cms_settings = {s.key: s.value for s in Setting.objects.filter(tag='cms')}
        context = {
            'stats': {
                'studies': Study.objects.count(),
                'biomarkers': BioMarker.objects.count(),
                'patients': Patient.objects.count(),
            },
            'leadTeam': self.teamService.getActive()[:4],
            'cmsSettings': cms_settings,
        }
        return self.render(request, context, 'about')
