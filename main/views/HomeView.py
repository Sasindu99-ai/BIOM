from django.http import Http404, JsonResponse
from django.shortcuts import redirect

from main.models import BioMarker, Patient, Study, StudyVariable
from res import R
from settings.models import Setting
from settings.services import (
    ContactService,
    PageService,
    PublicationService,
    TeamService,
    ToolService,
)
from vvecon.zorion.views import GetMapping, Mapping, PostMapping, View

__all__ = ['HomeView']


@Mapping()
class HomeView(View):
    R: R = R()

    pageService: PageService = PageService()
    teamService: TeamService = TeamService()
    publicationService: PublicationService = PublicationService()
    toolService: ToolService = ToolService()
    contactService: ContactService = ContactService()

    def homeConfig(self):
        self.R.data.navigator.enabled = True
        self.R.data.footer.enabled = True

    def _getCmsSettings(self):
        settings_qs = Setting.objects.filter(tag='cms')
        res = {s.key: s.value for s in settings_qs}
        defaults = {
            'site_title': 'BIOM: Biomedical Omics Knowledgebase',
            'hero_subtitle': (
                'A curated knowledgebase of biomarkers, studies, and structured variables for CKDu research. '
                'Explore reproducible datasets, contribute findings, and accelerate discovery through open, '
                'well-documented data.'
            ),
            'contact_email': 'sasindusulochana99@gmail.com',
            'contact_phone': '+94 81 239 2000',
            'contact_address': 'University of Peradeniya, Sri Lanka',
            'ckdu_description': (
                'Chronic kidney disease of unknown etiology (CKDu) is the gradual loss of kidney function '
                'over periods of months or years with symptoms appearing in the late stages of the disease. '
                'Emergence of CKDu is a global health concern affecting agricultural communities worldwide.'
            ),
            'twitter_url': 'https://twitter.com',
            'github_url': 'https://github.com/Sasindu99-ai/BIOM',
            'linkedin_url': 'https://linkedin.com',
        }
        for k, v in defaults.items():
            if k not in res:
                res[k] = v
        return res

    @GetMapping()
    def home(self, request):
        self.homeConfig()
        context = {
            'stats': {
                'totalStudies': Study.objects.count(),
                'totalBiomarkers': BioMarker.objects.count(),
                'totalPatients': Patient.objects.count(),
                'totalVariables': StudyVariable.objects.count(),
            },
            'featuredPublications': self.publicationService.getFeatured()[:3],
            'tools': self.toolService.getActive()[:4],
            'teamSpotlight': self.teamService.getActive()[:3],
            'cmsSettings': self._getCmsSettings(),
            'contactSuccess': request.GET.get('contact_success') == '1',
        }
        return self.render(request, context, 'home')

    @PostMapping('contact-submit')
    def submitContact(self, request):
        name = request.POST.get('name', '').strip()
        email = request.POST.get('email', '').strip()
        subject = request.POST.get('subject', '').strip()
        message = request.POST.get('message', '').strip()

        if not name or not email or not message:
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({'status': 'error', 'message': 'Please fill all required fields.'}, status=400)
            return redirect('/#contact')

        self.contactService.createMessage(
            name=name, email=email, subject=subject or 'General Inquiry', message=message,
        )

        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({'status': 'success', 'message': 'Thank you! Your message has been sent.'})
        return redirect('/?contact_success=1#contact')

    @GetMapping('page/<slug>')
    def dynamicPage(self, request, slug: str):
        self.homeConfig()
        page = self.pageService.getBySlug(slug)
        if not page:
            raise Http404('Page not found')
        return self.render(request, {'page': page}, 'page')

    @GetMapping('privacy-policy')
    def privacyPolicy(self, request):
        self.homeConfig()
        page = self.pageService.getBySlug('privacy-policy')
        return self.render(request, {'page': page}, 'privacy-policy')

    @GetMapping('terms-and-conditions')
    def termsAndConditions(self, request):
        self.homeConfig()
        page = self.pageService.getBySlug('terms-and-conditions')
        return self.render(request, {'page': page}, 'terms-and-conditions')
