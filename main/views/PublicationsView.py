from res import R
from settings.services import PublicationService
from vvecon.zorion.views import GetMapping, Mapping, View

__all__ = ['PublicationsView']


@Mapping('publications')
class PublicationsView(View):
    R: R = R()
    publicationService: PublicationService = PublicationService()

    def homeConfig(self):
        self.R.data.navigator.enabled = True
        self.R.data.footer.enabled = True

    @GetMapping('/')
    def publications(self, request):
        self.homeConfig()
        publications = self.publicationService.getActive()
        years = sorted({p.year for p in publications}, reverse=True)
        return self.render(
            request,
            {
                'publications': publications,
                'years': years,
                'totalCount': publications.count(),
            },
            'publications',
        )
