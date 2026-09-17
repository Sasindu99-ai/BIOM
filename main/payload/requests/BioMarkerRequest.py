from vvecon.zorion import serializers

from ...models import BioMarker

__all__ = ['BioMarkerRequest']


class BioMarkerRequest(serializers.ModelRequest):
	class Meta:
		model = BioMarker
		fields = (
			'name', 'shortName', 'commonName', 'type', 'biomType', 'status',
			'aaSequence', 'molecularLength', 'molecularWeight', 'uniProtKB', 'ncib', 'pdb',
		)
		extra_kwargs = dict(
			name=dict(required=True),
			shortName=dict(required=False),
			commonName=dict(required=False),
			type=dict(required=False),
			biomType=dict(required=False),
			status=dict(required=False),
			aaSequence=dict(required=False),
			molecularLength=dict(required=False),
			molecularWeight=dict(required=False),
			uniProtKB=dict(required=False),
			ncib=dict(required=False),
			pdb=dict(required=False),
		)
