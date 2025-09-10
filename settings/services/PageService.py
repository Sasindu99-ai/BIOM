
from django.core.exceptions import ObjectDoesNotExist
from rest_framework.exceptions import NotFound

from vvecon.zorion.core import Service

from ..models import Page

__all__ = ['PageService']


class PageService(Service):
    model = Page

    def getBySlug(self, slug: str) -> Page | None:
        try:
            return self.model.objects.get(slug=slug)
        except (NotFound, ObjectDoesNotExist):
            return None
