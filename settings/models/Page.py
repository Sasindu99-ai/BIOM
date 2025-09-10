from vvecon.zorion.db import models

__all__ = ['Page']


class Page(models.Model):
    slug = models.SlugField(max_length=255, unique=True)
    title = models.CharField(max_length=255)
    content = models.TextField()
    aside = models.BooleanField(default=False)
    nav = models.BooleanField(default=False)
    footer = models.BooleanField(default=False)

    def get_url(self):
        return f'/page/{self.slug}'
