from vvecon.zorion.core import Service

from ..models import ResearchTool

__all__ = ['ToolService']

DEFAULT_TOOLS = [
    {
        'name': 'Study & Cohort Browser',
        'category': 'Data Exploration',
        'summary': (
            'Interactive cohort exploration interface with clinical phenotypes, biomarker distributions, '
            'and longitudinal sampling data.'
        ),
        'description': (
            'Search and filter studies by location, etiology status, cohort size, and variable availability. '
            'Export harmonized cohort subsets for external analysis.'
        ),
        'url': '/explore/',
        'badge': 'Core Tool',
        'icon': 'ph-chart-pie-slice',
        'is_active': True,
        'order': 1,
    },
    {
        'name': 'Biomarker Knowledge Atlas',
        'category': 'Omics Discovery',
        'summary': 'Curated reference atlas of urine, serum, and tissue biomarkers reported across CKDu studies.',
        'description': (
            'Look up molecular markers, gene symbols, assay platforms, statistical significance levels, '
            'and corresponding publication references.'
        ),
        'url': '/explore/#biomarkers',
        'badge': 'Curated',
        'icon': 'ph-dna',
        'is_active': True,
        'order': 2,
    },
    {
        'name': 'REST API & OpenAPI Explorer',
        'category': 'Developer Integration',
        'summary': (
            'Programmatic endpoints with complete Swagger / Redoc interactive API documentation '
            'and JSON schemas.'
        ),
        'description': (
            'Query studies, clinical variables, patient demographics, and biomarker measurements '
            'directly via standard REST requests using API keys.'
        ),
        'url': '/api/',
        'badge': 'v1.0 REST',
        'icon': 'ph-code',
        'is_active': True,
        'order': 3,
    },
    {
        'name': 'biom-kit Python Package',
        'category': 'Data Science & Notebooks',
        'summary': (
            'Client library for Jupyter Notebooks, Google Colab, and Python scripts with '
            'Pandas DataFrame export.'
        ),
        'description': (
            'Installable via pip. Provides high-level abstractions to pull cleaned cohorts '
            'directly into analysis workflows without raw CSV handling.'
        ),
        'url': '/dashboard/settings/',
        'badge': 'Python SDK',
        'icon': 'ph-terminal-window',
        'is_active': True,
        'order': 4,
    },
    {
        'name': 'Advanced Phenotype Filter',
        'category': 'Data Exploration',
        'summary': (
            'Multi-parameter faceted query builder to cross-reference patient lab results, '
            'eGFR stages, and geographic coordinates.'
        ),
        'description': (
            'Combine demographic bounds with biomarker thresholds to discover candidate patient cohorts '
            'across distinct clinical study sites.'
        ),
        'url': '/dashboard/advanced-filter/',
        'badge': 'Dashboard',
        'icon': 'ph-funnel',
        'is_active': True,
        'order': 5,
    },
]


class ToolService(Service):
    model = ResearchTool

    def getActive(self):
        self.seedDefaultsIfEmpty()
        return self.model.objects.filter(is_active=True).order_by('order', 'name')

    def getAll(self):
        self.seedDefaultsIfEmpty()
        return self.model.objects.all().order_by('order', 'name')

    def getById(self, pk: int) -> ResearchTool | None:
        try:
            return self.model.objects.get(pk=pk)
        except self.model.DoesNotExist:
            return None

    def seedDefaultsIfEmpty(self):
        if not self.model.objects.exists():
            for item in DEFAULT_TOOLS:
                self.model.objects.create(**item)
