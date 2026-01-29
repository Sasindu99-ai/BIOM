from authentication.models import User
from vvecon.zorion.db import models

from ..enums import BioMarkerStatus, BioMarkerType, BiomType

__all__ = ['BioMarker']


class BioMarker(models.Model):
	aaSequence = models.CharField(max_length=2048, blank=True, null=True, verbose_name='Amino Acid Sequence')
	biomType = models.CharField(
		max_length=50, choices=BiomType.choices, default=BiomType.EXISTING, verbose_name='Biomarker Type',
	)
	commonName = models.CharField(max_length=255, blank=True, null=True, verbose_name='Common Name')
	image = models.ImageField(upload_to='biomarkers/', blank=True, null=True, verbose_name='Image')
	molecularLength = models.IntegerField(verbose_name='Molecular Length', default=0)
	name = models.CharField(max_length=255, verbose_name='Name')
	ncib = models.CharField(max_length=255, blank=True, null=True, verbose_name='NCIB ID')
	pdb = models.CharField(max_length=255, blank=True, null=True, verbose_name='PDB ID')
	shortName = models.CharField(max_length=100, blank=True, null=True, verbose_name='Short Name')
	status = models.CharField(
		max_length=50, verbose_name='Status', choices=BioMarkerStatus.choices, default=BioMarkerStatus.PENDING,
	)
	type = models.CharField(
		max_length=50, verbose_name='Type', choices=BioMarkerType.choices, default=BioMarkerType.PROTEIN,
	)
	uniProtKB = models.CharField(max_length=255, blank=True, null=True, verbose_name='UniProtKB ID')
	molecularWeight = models.FloatField(verbose_name='Molecular Weight', default=0)
	uploadedBy = models.ForeignKey(
		User, on_delete=models.SET_NULL, blank=True, null=True, verbose_name='Uploaded By',
		related_name='uploadedBioMarkers',
	)
	administeredBy = models.ForeignKey(
		User, on_delete=models.SET_NULL, blank=True, null=True, verbose_name='Administered By',
		related_name='administeredBioMarkers',
	)
	version = models.IntegerField(default=1, verbose_name='Version')

	def __str__(self):
		return self.name
