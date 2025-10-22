from vvecon.zorion.db import models

__all__ = ['BioMarkerType']


class BioMarkerType(models.TextChoices):
	PROTEIN = 'PROTEIN', 'Protein'
	RNA = 'RNA', 'RNA'
	DNA = 'DNA', 'DNA'
