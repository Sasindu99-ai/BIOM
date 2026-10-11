from django.http import HttpResponseRedirect, JsonResponse
from django.urls import reverse

from res import R
from settings.models import ContactMessage, Page, Publication, ResearchTool, Setting, TeamMember
from settings.services import (
    ContactService,
    PageService,
    PublicationService,
    SettingService,
    TeamService,
    ToolService,
)
from vvecon.zorion.auth import Authenticated
from vvecon.zorion.views import GetMapping, Mapping, PostMapping, View

__all__ = ['CMSView']


@Mapping('dashboard/cms')
class CMSView(View):
    R: R = R()

    pageService: PageService = PageService()
    teamService: TeamService = TeamService()
    publicationService: PublicationService = PublicationService()
    toolService: ToolService = ToolService()
    contactService: ContactService = ContactService()
    settingService: SettingService = SettingService()

    def adminConfig(self, activeSlug='dashboard/cms'):
        self.R.data.navigator.enabled = True
        self.R.data.aside['admin'].enabled = True
        self.R.data.aside['admin'].activeSlug = activeSlug

    # -------------------------------------------------------------------------
    # 1. Overview
    # -------------------------------------------------------------------------
    @GetMapping('/')
    @Authenticated(admin=True)
    def overview(self, request):
        self.adminConfig('dashboard/cms')
        context = {
            'stats': {
                'pagesCount': self.pageService.getAll().count(),
                'teamCount': self.teamService.getAll().count(),
                'publicationsCount': self.publicationService.getAll().count(),
                'toolsCount': self.toolService.getAll().count(),
                'messagesCount': self.contactService.getAll().count(),
                'unreadMessagesCount': self.contactService.getUnread().count(),
            },
            'recentMessages': self.contactService.getAll()[:5],
            'recentPublications': self.publicationService.getAll()[:4],
            'recentTeam': self.teamService.getAll()[:4],
        }
        return self.render(request, context=context, template_name='dashboard/cms/overview')

    # -------------------------------------------------------------------------
    # 2. Pages
    # -------------------------------------------------------------------------
    @GetMapping('/pages')
    @Authenticated(admin=True)
    def pagesList(self, request):
        self.adminConfig('dashboard/cms')
        pages = self.pageService.getAll()
        return self.render(request, context={'pages': pages}, template_name='dashboard/cms/pages')

    @PostMapping('/pages/save')
    @Authenticated(admin=True)
    def savePage(self, request):
        page_id = request.POST.get('id')
        title = request.POST.get('title', '').strip()
        slug = request.POST.get('slug', '').strip().lower()
        content = request.POST.get('content', '')
        nav = request.POST.get('nav') == 'on' or request.POST.get('nav') == 'true'
        footer = request.POST.get('footer') == 'on' or request.POST.get('footer') == 'true'
        aside = request.POST.get('aside') == 'on' or request.POST.get('aside') == 'true'

        if not title or not slug:
            return JsonResponse({'status': 'error', 'message': 'Title and slug are required'}, status=400)

        if page_id:
            page = self.pageService.getById(int(page_id))
            if not page:
                return JsonResponse({'status': 'error', 'message': 'Page not found'}, status=404)
            page.title = title
            page.slug = slug
            page.content = content
            page.nav = nav
            page.footer = footer
            page.aside = aside
            page.save()
        else:
            if Page.objects.filter(slug=slug).exists():
                return JsonResponse(
                    {'status': 'error', 'message': f"Page with slug '{slug}' already exists"}, status=400,
                )
            Page.objects.create(
                title=title,
                slug=slug,
                content=content,
                nav=nav,
                footer=footer,
                aside=aside,
            )

        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({'status': 'success', 'message': 'Page saved successfully'})
        return HttpResponseRedirect(reverse('dashboard/cms/pages'))

    @PostMapping('/pages/delete')
    @Authenticated(admin=True)
    def deletePage(self, request):
        page_id = request.POST.get('id')
        if not page_id:
            return JsonResponse({'status': 'error', 'message': 'Page ID required'}, status=400)
        Page.objects.filter(id=int(page_id)).delete()
        return JsonResponse({'status': 'success', 'message': 'Page deleted successfully'})

    # -------------------------------------------------------------------------
    # 3. Team Members
    # -------------------------------------------------------------------------
    @GetMapping('/team')
    @Authenticated(admin=True)
    def teamList(self, request):
        self.adminConfig('dashboard/cms')
        team = self.teamService.getAll()
        return self.render(request, context={'team': team}, template_name='dashboard/cms/team')

    @PostMapping('/team/save')
    @Authenticated(admin=True)
    def saveTeam(self, request):
        member_id = request.POST.get('id')
        name = request.POST.get('name', '').strip()
        role = request.POST.get('role', '').strip()
        affiliation = request.POST.get('affiliation', '').strip()
        bio = request.POST.get('bio', '').strip()
        avatar = request.POST.get('avatar', '').strip() or 'img/avatar.jpg'
        email = request.POST.get('email', '').strip()
        linkedin_url = request.POST.get('linkedin_url', '').strip()
        orcid_url = request.POST.get('orcid_url', '').strip()
        order = int(request.POST.get('order') or 0)
        is_active = request.POST.get('is_active') == 'on' or request.POST.get('is_active') == 'true'

        if not name or not role:
            return JsonResponse({'status': 'error', 'message': 'Name and role are required'}, status=400)

        if member_id:
            member = self.teamService.getById(int(member_id))
            if not member:
                return JsonResponse({'status': 'error', 'message': 'Member not found'}, status=404)
            member.name = name
            member.role = role
            member.affiliation = affiliation
            member.bio = bio
            member.avatar = avatar
            member.email = email
            member.linkedin_url = linkedin_url
            member.orcid_url = orcid_url
            member.order = order
            member.is_active = is_active
            member.save()
        else:
            TeamMember.objects.create(
                name=name,
                role=role,
                affiliation=affiliation,
                bio=bio,
                avatar=avatar,
                email=email,
                linkedin_url=linkedin_url,
                orcid_url=orcid_url,
                order=order,
                is_active=is_active,
            )

        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({'status': 'success', 'message': 'Team member saved'})
        return HttpResponseRedirect(reverse('dashboard/cms/team'))

    @PostMapping('/team/delete')
    @Authenticated(admin=True)
    def deleteTeam(self, request):
        member_id = request.POST.get('id')
        if not member_id:
            return JsonResponse({'status': 'error', 'message': 'ID required'}, status=400)
        TeamMember.objects.filter(id=int(member_id)).delete()
        return JsonResponse({'status': 'success', 'message': 'Team member deleted'})

    # -------------------------------------------------------------------------
    # 4. Publications
    # -------------------------------------------------------------------------
    @GetMapping('/publications')
    @Authenticated(admin=True)
    def publicationsList(self, request):
        self.adminConfig('dashboard/cms')
        publications = self.publicationService.getAll()
        return self.render(request, context={'publications': publications}, template_name='dashboard/cms/publications')

    @PostMapping('/publications/save')
    @Authenticated(admin=True)
    def savePublication(self, request):
        pub_id = request.POST.get('id')
        title = request.POST.get('title', '').strip()
        authors = request.POST.get('authors', '').strip()
        journal = request.POST.get('journal', '').strip()
        year = int(request.POST.get('year') or 2026)
        doi = request.POST.get('doi', '').strip()
        url = request.POST.get('url', '').strip()
        abstract = request.POST.get('abstract', '').strip()
        citation_count = int(request.POST.get('citation_count') or 0)
        is_featured = request.POST.get('is_featured') == 'on' or request.POST.get('is_featured') == 'true'
        is_active = request.POST.get('is_active') == 'on' or request.POST.get('is_active') == 'true'
        order = int(request.POST.get('order') or 0)

        if not title or not authors:
            return JsonResponse({'status': 'error', 'message': 'Title and authors are required'}, status=400)

        if pub_id:
            pub = self.publicationService.getById(int(pub_id))
            if not pub:
                return JsonResponse({'status': 'error', 'message': 'Publication not found'}, status=404)
            pub.title = title
            pub.authors = authors
            pub.journal = journal
            pub.year = year
            pub.doi = doi
            pub.url = url
            pub.abstract = abstract
            pub.citation_count = citation_count
            pub.is_featured = is_featured
            pub.is_active = is_active
            pub.order = order
            pub.save()
        else:
            Publication.objects.create(
                title=title,
                authors=authors,
                journal=journal,
                year=year,
                doi=doi,
                url=url,
                abstract=abstract,
                citation_count=citation_count,
                is_featured=is_featured,
                is_active=is_active,
                order=order,
            )

        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({'status': 'success', 'message': 'Publication saved'})
        return HttpResponseRedirect(reverse('dashboard/cms/publications'))

    @PostMapping('/publications/delete')
    @Authenticated(admin=True)
    def deletePublication(self, request):
        pub_id = request.POST.get('id')
        if not pub_id:
            return JsonResponse({'status': 'error', 'message': 'ID required'}, status=400)
        Publication.objects.filter(id=int(pub_id)).delete()
        return JsonResponse({'status': 'success', 'message': 'Publication deleted'})

    # -------------------------------------------------------------------------
    # 5. Research Tools
    # -------------------------------------------------------------------------
    @GetMapping('/tools')
    @Authenticated(admin=True)
    def toolsList(self, request):
        self.adminConfig('dashboard/cms')
        tools = self.toolService.getAll()
        return self.render(request, context={'tools': tools}, template_name='dashboard/cms/tools')

    @PostMapping('/tools/save')
    @Authenticated(admin=True)
    def saveTool(self, request):
        tool_id = request.POST.get('id')
        name = request.POST.get('name', '').strip()
        category = request.POST.get('category', 'General').strip()
        summary = request.POST.get('summary', '').strip()
        description = request.POST.get('description', '').strip()
        url = request.POST.get('url', '').strip()
        badge = request.POST.get('badge', '').strip()
        icon = request.POST.get('icon', 'ph-gear').strip()
        order = int(request.POST.get('order') or 0)
        is_active = request.POST.get('is_active') == 'on' or request.POST.get('is_active') == 'true'

        if not name or not url:
            return JsonResponse({'status': 'error', 'message': 'Name and URL are required'}, status=400)

        if tool_id:
            tool = self.toolService.getById(int(tool_id))
            if not tool:
                return JsonResponse({'status': 'error', 'message': 'Tool not found'}, status=404)
            tool.name = name
            tool.category = category
            tool.summary = summary
            tool.description = description
            tool.url = url
            tool.badge = badge
            tool.icon = icon
            tool.order = order
            tool.is_active = is_active
            tool.save()
        else:
            ResearchTool.objects.create(
                name=name,
                category=category,
                summary=summary,
                description=description,
                url=url,
                badge=badge,
                icon=icon,
                order=order,
                is_active=is_active,
            )

        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({'status': 'success', 'message': 'Tool saved'})
        return HttpResponseRedirect(reverse('dashboard/cms/tools'))

    @PostMapping('/tools/delete')
    @Authenticated(admin=True)
    def deleteTool(self, request):
        tool_id = request.POST.get('id')
        if not tool_id:
            return JsonResponse({'status': 'error', 'message': 'ID required'}, status=400)
        ResearchTool.objects.filter(id=int(tool_id)).delete()
        return JsonResponse({'status': 'success', 'message': 'Tool deleted'})

    # -------------------------------------------------------------------------
    # 6. Contact Inquiries Inbox
    # -------------------------------------------------------------------------
    @GetMapping('/messages')
    @Authenticated(admin=True)
    def messagesList(self, request):
        self.adminConfig('dashboard/cms')
        filter_type = request.GET.get('filter', 'all')
        messages = self.contactService.getUnread() if filter_type == 'unread' else self.contactService.getAll()
        return self.render(
            request,
            context={
                'messages': messages,
                'filter': filter_type,
                'unreadCount': self.contactService.getUnread().count(),
                'totalCount': self.contactService.getAll().count(),
            },
            template_name='dashboard/cms/messages',
        )

    @PostMapping('/messages/toggle')
    @Authenticated(admin=True)
    def toggleMessage(self, request):
        msg_id = request.POST.get('id')
        if not msg_id:
            return JsonResponse({'status': 'error', 'message': 'Message ID required'}, status=400)
        msg = self.contactService.getById(int(msg_id))
        if not msg:
            return JsonResponse({'status': 'error', 'message': 'Message not found'}, status=404)
        msg.is_read = not msg.is_read
        msg.save()
        return JsonResponse({'status': 'success', 'is_read': msg.is_read})

    @PostMapping('/messages/delete')
    @Authenticated(admin=True)
    def deleteMessage(self, request):
        msg_id = request.POST.get('id')
        if not msg_id:
            return JsonResponse({'status': 'error', 'message': 'Message ID required'}, status=400)
        ContactMessage.objects.filter(id=int(msg_id)).delete()
        return JsonResponse({'status': 'success', 'message': 'Message deleted'})

    # -------------------------------------------------------------------------
    # 7. General Branding & CMS Settings
    # -------------------------------------------------------------------------
    @GetMapping('/settings')
    @Authenticated(admin=True)
    def cmsSettings(self, request):
        self.adminConfig('dashboard/cms')
        settings_qs = Setting.objects.filter(tag='cms')
        settings_dict = {s.key: s.value for s in settings_qs}
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
            if k not in settings_dict:
                settings_dict[k] = v

        return self.render(
            request,
            context={'cms_settings': settings_dict},
            template_name='dashboard/cms/settings',
        )

    @PostMapping('/settings/save')
    @Authenticated(admin=True)
    def saveCmsSettings(self, request):
        fields = [
            'site_title',
            'hero_subtitle',
            'contact_email',
            'contact_phone',
            'contact_address',
            'ckdu_description',
            'twitter_url',
            'github_url',
            'linkedin_url',
        ]
        for f in fields:
            if f in request.POST:
                val = request.POST.get(f, '').strip()
                setting, _ = Setting.objects.get_or_create(key=f, tag='cms')
                setting.value = val
                setting.save()

        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({'status': 'success', 'message': 'Settings updated'})
        return HttpResponseRedirect(reverse('dashboard/cms/settings'))
