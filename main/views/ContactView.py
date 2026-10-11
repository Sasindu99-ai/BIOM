from django.http import JsonResponse
from django.shortcuts import redirect

from res import R
from settings.models import Setting
from settings.services import ContactService
from vvecon.zorion.views import GetMapping, Mapping, PostMapping, View

__all__ = ['ContactView']


@Mapping('contact')
class ContactView(View):
    R: R = R()
    contactService: ContactService = ContactService()

    def homeConfig(self):
        self.R.data.navigator.enabled = True
        self.R.data.footer.enabled = True

    def _getCmsSettings(self):
        settings_qs = Setting.objects.filter(tag='cms')
        res = {s.key: s.value for s in settings_qs}
        defaults = {
            'contact_email': 'sasindusulochana99@gmail.com',
            'contact_phone': '+94 81 239 2000',
            'contact_address': 'University of Peradeniya, Sri Lanka',
            'twitter_url': 'https://twitter.com',
            'github_url': 'https://github.com/Sasindu99-ai/BIOM',
            'linkedin_url': 'https://linkedin.com',
        }
        for k, v in defaults.items():
            if k not in res:
                res[k] = v
        return res

    @GetMapping('/')
    def contact(self, request):
        self.homeConfig()
        context = {
            'cmsSettings': self._getCmsSettings(),
            'success': request.GET.get('success') == '1',
        }
        return self.render(request, context, 'contact')

    @PostMapping('/')
    def submitMessage(self, request):
        name = request.POST.get('name', '').strip()
        email = request.POST.get('email', '').strip()
        subject = request.POST.get('subject', '').strip()
        message = request.POST.get('message', '').strip()

        if not name or not email or not message:
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({'status': 'error', 'message': 'All fields are required.'}, status=400)
            return redirect('/contact/')

        self.contactService.createMessage(
            name=name,
            email=email,
            subject=subject or 'Contact Inquiry',
            message=message,
        )

        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({'status': 'success', 'message': 'Your message has been sent successfully!'})
        return redirect('/contact/?success=1')
