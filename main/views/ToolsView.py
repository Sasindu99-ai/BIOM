from res import R
from settings.services import ToolService
from vvecon.zorion.views import GetMapping, Mapping, View

__all__ = ['ToolsView']


@Mapping('tools')
class ToolsView(View):
    R: R = R()
    toolService: ToolService = ToolService()

    def homeConfig(self):
        self.R.data.navigator.enabled = True
        self.R.data.footer.enabled = True

    @GetMapping('/')
    def tools(self, request):
        self.homeConfig()
        tools = self.toolService.getActive()
        categories = sorted({t.category for t in tools})
        return self.render(
            request,
            {
                'tools': tools,
                'categories': categories,
            },
            'tools',
        )
