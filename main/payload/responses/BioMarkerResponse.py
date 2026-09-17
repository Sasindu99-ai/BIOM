from authentication.payload.responses import UserResponse
from vvecon.zorion import serializers

from ...models import BioMarker

__all__ = ['BioMarkerResponse']


class BioMarkerResponse(serializers.ModelResponse):
	uploadedBy = UserResponse(allow_null=True).response()
	administeredBy = UserResponse(allow_null=True).response()

	model = BioMarker
	fields = (
		'id', 'name', 'shortName', 'commonName', 'type', 'biomType', 'status',
		'aaSequence', 'molecularLength', 'molecularWeight', 'uniProtKB', 'ncib', 'pdb',
		'uploadedBy', 'administeredBy', 'version', 'created_at', 'updated_at',
	)
