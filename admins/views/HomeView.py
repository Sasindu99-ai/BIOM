from res import R
from vvecon.zorion.auth import Authenticated
from vvecon.zorion.views import GetMapping, Mapping, View

__all__ = ['HomeView']


@Mapping('admin')
class HomeView(View):
    R: R = R()

    @GetMapping()
    @Authenticated(staff=True, admin=True)
    def home(self, request):
        self.R.data.settings['head'] = 'Dashboard'

        return self.render(request, dict(), 'admin/home')
