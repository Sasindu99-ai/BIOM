from vvecon.zorion import serializers

from ...enums import BioMarkerStatus

__all__ = ['BioMarkerReviewRequest']


class BioMarkerReviewRequest(serializers.Request):
	status = serializers.ChoiceField(choices=BioMarkerStatus.choices)
