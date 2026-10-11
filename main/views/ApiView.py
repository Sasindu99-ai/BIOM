from authentication.models import ApiKey
from res import R
from vvecon.zorion.views import GetMapping, Mapping, View

__all__ = ['ApiView']


@Mapping('api')
class ApiView(View):
    R: R = R()

    def homeConfig(self):
        self.R.data.navigator.enabled = True
        self.R.data.footer.enabled = True

    @GetMapping('/')
    def api(self, request):
        self.homeConfig()
        active_key = None
        if request.user.is_authenticated:
            active_key = ApiKey.objects.filter(user=request.user, is_active=True).first()

        context = {
            'active_key': active_key,
        }
        return self.render(request, context, 'api')
