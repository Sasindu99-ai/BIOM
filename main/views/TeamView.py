from res import R
from settings.services import TeamService
from vvecon.zorion.views import GetMapping, Mapping, View

__all__ = ['TeamView']


@Mapping('team')
class TeamView(View):
    R: R = R()
    teamService: TeamService = TeamService()

    def homeConfig(self):
        self.R.data.navigator.enabled = True
        self.R.data.footer.enabled = True

    @GetMapping('/')
    def team(self, request):
        self.homeConfig()
        team_members = self.teamService.getActive()
        return self.render(request, {'team_members': team_members}, 'team')
