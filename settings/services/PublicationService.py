from vvecon.zorion.core import Service

from ..models import Publication

__all__ = ['PublicationService']

DEFAULT_PUBLICATIONS = [
    {
        'title': (
            'Multi-omics profiling reveals tubular mitochondrial dysfunction in Chronic Kidney Disease '
            'of unknown etiology'
        ),
        'authors': 'Fernando, E.Y., Premachandra, P.K., Rajapaksha, A., et al.',
        'journal': 'Kidney International Reports',
        'year': 2025,
        'doi': '10.1016/j.ekir.2025.01.014',
        'url': 'https://doi.org/10.1016/j.ekir.2025.01.014',
        'abstract': (
            'A comprehensive transcriptomic and metabolomic investigation of renal tissue biopsies from endemic '
            'agricultural communities demonstrating distinctive mitochondrial respiratory complex downregulation '
            'in preclinical stages.'
        ),
        'citation_count': 34,
        'is_featured': True,
        'is_active': True,
        'order': 1,
    },
    {
        'title': (
            'Urinary KIM-1 and NGAL as longitudinal biomarkers of renal function decline in rural '
            'Sri Lankan farming cohorts'
        ),
        'authors': 'Premachandra, P.K., Nanayakkara, N., Dissanayake, R.B.N., et al.',
        'journal': 'BMC Nephrology',
        'year': 2024,
        'doi': '10.1186/s12882-024-03521-7',
        'url': 'https://doi.org/10.1186/s12882-024-03521-7',
        'abstract': (
            'Evaluation of urinary biomarker panels over a 36-month prospective cohort study to assess '
            'predictive accuracy for rapid eGFR trajectory decline compared to traditional albuminuria.'
        ),
        'citation_count': 22,
        'is_featured': True,
        'is_active': True,
        'order': 2,
    },
    {
        'title': (
            'Standardized environmental variable curation and phenotypic harmonization in the BIOM '
            'open knowledgebase'
        ),
        'authors': 'Ranasinghe, R.H.T.D., Supasan, N.A.I., Fernando, E.Y.',
        'journal': 'Scientific Data (Nature)',
        'year': 2024,
        'doi': '10.1038/s41597-024-03198-2',
        'url': 'https://doi.org/10.1038/s41597-024-03198-2',
        'abstract': (
            'Presents the computational framework, ontology mapping, and dataset reconciliation pipelines '
            'implemented in BIOM for reproducible multi-center nephropathy studies.'
        ),
        'citation_count': 18,
        'is_featured': True,
        'is_active': True,
        'order': 3,
    },
    {
        'title': 'Heavy metal co-exposure and groundwater silica: A geospatial omics study in North Central Province',
        'authors': 'Rajapaksha, A., Fernando, E.Y., Premachandra, P.K.',
        'journal': 'Environmental Research',
        'year': 2023,
        'doi': '10.1016/j.envres.2023.116890',
        'url': 'https://doi.org/10.1016/j.envres.2023.116890',
        'abstract': (
            'Correlation of drinking water hydrogeochemical signatures with patient serum metabolomic profiles, '
            'pinpointing localized oxidative damage pathways.'
        ),
        'citation_count': 41,
        'is_featured': False,
        'is_active': True,
        'order': 4,
    },
]


class PublicationService(Service):
    model = Publication

    def getActive(self):
        self.seedDefaultsIfEmpty()
        return self.model.objects.filter(is_active=True).order_by('order', '-year', 'title')

    def getFeatured(self):
        self.seedDefaultsIfEmpty()
        return self.model.objects.filter(is_active=True, is_featured=True).order_by('order', '-year')

    def getAll(self):
        self.seedDefaultsIfEmpty()
        return self.model.objects.all().order_by('order', '-year', 'title')

    def getById(self, pk: int) -> Publication | None:
        try:
            return self.model.objects.get(pk=pk)
        except self.model.DoesNotExist:
            return None

    def seedDefaultsIfEmpty(self):
        if not self.model.objects.exists():
            for item in DEFAULT_PUBLICATIONS:
                self.model.objects.create(**item)
