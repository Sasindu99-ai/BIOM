from vvecon.zorion import serializers

from ...models import StudyVariable

__all__ = ['StudyVariableRequest']


class StudyVariableRequest(serializers.ModelRequest):
	class Meta:
		model = StudyVariable
		fields = ('name', 'notes', 'status', 'type', 'field', 'isRange', 'isSearchable', 'isUnique', 'order')
		extra_kwargs = dict(
			name=dict(required=True),
			notes=dict(required=False),
			status=dict(required=False),
			type=dict(required=False),
			field=dict(required=False),
			isRange=dict(required=False),
			isSearchable=dict(required=False),
			isUnique=dict(required=False),
			order=dict(required=False),
		)
