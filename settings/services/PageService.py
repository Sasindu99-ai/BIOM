from django.core.exceptions import ObjectDoesNotExist
from rest_framework.exceptions import NotFound

from vvecon.zorion.core import Service

from ..models import Page

__all__ = ['PageService']

DEFAULT_PAGES = [
    {
        'slug': 'privacy-policy',
        'title': 'Privacy Policy',
        'content': (
            '<h2>BIOM Privacy Policy</h2><p>This privacy policy outlines how BIOM collects, protects, '
            'and utilizes information when you access our knowledgebase and associated tools.</p>'
            '<h3>Data Collection & Anonymization</h3><p>All clinical and patient data stored in BIOM '
            'is strictly de-identified in full adherence to international biomedical research ethics '
            'and HIPAA/GDPR data protection standards.</p>'
        ),
        'nav': False,
        'footer': True,
        'aside': False,
    },
    {
        'slug': 'terms-and-conditions',
        'title': 'Terms & Conditions',
        'content': (
            '<h2>Terms of Service</h2><p>By using the BIOM open biomedical platform, you agree to cite '
            'appropriate publications and comply with data use agreements for published cohorts.</p>'
            '<h3>Permitted Research Use</h3><p>BIOM datasets are provided for academic research, '
            'biomedical discovery, and non-commercial analytical workflows.</p>'
        ),
        'nav': False,
        'footer': True,
        'aside': False,
    },
]


class PageService(Service):
    model = Page

    def getAll(self):
        self.seedDefaultsIfEmpty()
        return self.model.objects.all().order_by('title')

    def getBySlug(self, slug: str) -> Page | None:
        self.seedDefaultsIfEmpty()
        try:
            return self.model.objects.get(slug=slug)
        except (NotFound, ObjectDoesNotExist, self.model.DoesNotExist):
            return None

    def getById(self, pk: int) -> Page | None:
        try:
            return self.model.objects.get(pk=pk)
        except (NotFound, ObjectDoesNotExist, self.model.DoesNotExist):
            return None

    def seedDefaultsIfEmpty(self):
        if not self.model.objects.exists():
            for p in DEFAULT_PAGES:
                self.model.objects.create(**p)
