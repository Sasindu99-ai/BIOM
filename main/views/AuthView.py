from res import R
from vvecon.zorion.views import GetMapping, Mapping, View

__all__ = ['AuthView']


@Mapping('auth')
class AuthView(View):
    R: R = R()

    @GetMapping('/register')
    def register(self, request):
        self.R.data.settings['head'] = 'Register'
        return self.render(request, dict(), 'auth/register')
