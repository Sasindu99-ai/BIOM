from res import R
from vvecon.zorion.views import GetMapping, Mapping, View

__all__ = ['HomeView']


@Mapping()
class HomeView(View):
    R: R = R()

    @GetMapping()
    def home(self, request):
        return self.render(request, dict(), 'home')
