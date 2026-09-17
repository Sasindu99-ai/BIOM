from vvecon.zorion.core import Service

from ..models import BioMarker

__all__ = ['BioMarkerService']


class BioMarkerService(Service):
	model = BioMarker
	searchableFields = ('name', 'commonName', 'shortName', 'uniProtKB', 'ncib', 'pdb')
	filterableFields = ('status', 'type', 'biomType', 'uploadedBy')
