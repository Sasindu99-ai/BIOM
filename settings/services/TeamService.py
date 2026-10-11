from vvecon.zorion.core import Service

from ..models import TeamMember

__all__ = ['TeamService']

DEFAULT_TEAM = [
    {
        'name': 'Dr. E.Y Fernando',
        'role': 'Principal Investigator & Nephrologist',
        'affiliation': 'Faculty of Medicine, University of Peradeniya',
        'bio': (
            'Specialist in clinical nephrology and leading epidemiology cohorts studying renal '
            'progression markers in CKDu hotspots.'
        ),
        'avatar': 'img/avatar.jpg',
        'email': 'eyfernando@biom.lk',
        'linkedin_url': 'https://linkedin.com',
        'orcid_url': 'https://orcid.org',
        'order': 1,
        'is_active': True,
    },
    {
        'name': 'Dr. P.K Premachandra',
        'role': 'Co-Investigator & Molecular Biologist',
        'affiliation': 'Department of Molecular Biology & Biotechnology',
        'bio': (
            'Expert in genomic profiling and targeted metabolomics investigating heavy-metal exposure '
            'and oxidative stress markers.'
        ),
        'avatar': 'img/avatar.jpg',
        'email': 'pkpremachandra@biom.lk',
        'linkedin_url': 'https://linkedin.com',
        'orcid_url': 'https://orcid.org',
        'order': 2,
        'is_active': True,
    },
    {
        'name': 'Dr. A. Rajapaksha',
        'role': 'Senior Research Scientist',
        'affiliation': 'National Hospital of Sri Lanka / Research Unit',
        'bio': (
            'Clinical pathologist focusing on urine-derived proteomic signatures and non-invasive '
            'early stage diagnostics.'
        ),
        'avatar': 'img/avatar.jpg',
        'email': 'arajapaksha@biom.lk',
        'linkedin_url': 'https://linkedin.com',
        'orcid_url': 'https://orcid.org',
        'order': 3,
        'is_active': True,
    },
    {
        'name': 'Dr. N. Nanayakkara',
        'role': 'Consultant Nephrologist & Senior Advisor',
        'affiliation': 'Centre for Research in CKDu, Kandy',
        'bio': (
            'Pioneer researcher in CKDu clinical screening with decades of cohort data contributions '
            'across rural agricultural areas.'
        ),
        'avatar': 'img/avatar.jpg',
        'email': 'nnanayakkara@biom.lk',
        'linkedin_url': 'https://linkedin.com',
        'orcid_url': 'https://orcid.org',
        'order': 4,
        'is_active': True,
    },
    {
        'name': 'Mr. D.M.R.B.N Dissanayake',
        'role': 'Bioinformatics Lead',
        'affiliation': 'Computational Omics Lab',
        'bio': (
            'Focuses on pipeline engineering, multi-omics batch correction, and integrating '
            'transcriptomic data with environmental variables.'
        ),
        'avatar': 'img/avatar.jpg',
        'email': 'rbndissanayake@biom.lk',
        'linkedin_url': 'https://linkedin.com',
        'orcid_url': 'https://orcid.org',
        'order': 5,
        'is_active': True,
    },
    {
        'name': 'Ms. R.H.T.D Ranasinghe',
        'role': 'Data Scientist & Biostatistician',
        'affiliation': 'BIOM Research Group',
        'bio': (
            'Designs cohort deduplication logic, longitudinal survival analysis models, and '
            'standardized phenotype schemas.'
        ),
        'avatar': 'img/avatar.jpg',
        'email': 'rhtdranasinghe@biom.lk',
        'linkedin_url': 'https://linkedin.com',
        'orcid_url': 'https://orcid.org',
        'order': 6,
        'is_active': True,
    },
    {
        'name': 'Mr. N.A.I Supasan',
        'role': 'Software Engineer & Kit Maintainer',
        'affiliation': 'Core Engineering Team',
        'bio': (
            'Maintains the biom-kit Python distribution, REST endpoints, and reproducible '
            'notebook interfaces for researchers.'
        ),
        'avatar': 'img/avatar.jpg',
        'email': 'naisupasan@biom.lk',
        'linkedin_url': 'https://linkedin.com',
        'orcid_url': 'https://orcid.org',
        'order': 7,
        'is_active': True,
    },
]


class TeamService(Service):
    model = TeamMember

    def getActive(self):
        self.seedDefaultsIfEmpty()
        return self.model.objects.filter(is_active=True).order_by('order', 'name')

    def getAll(self):
        self.seedDefaultsIfEmpty()
        return self.model.objects.all().order_by('order', 'name')

    def getById(self, pk: int) -> TeamMember | None:
        try:
            return self.model.objects.get(pk=pk)
        except self.model.DoesNotExist:
            return None

    def seedDefaultsIfEmpty(self):
        if not self.model.objects.exists():
            for item in DEFAULT_TEAM:
                self.model.objects.create(**item)
