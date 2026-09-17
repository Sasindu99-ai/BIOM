from django.db import migrations, models


def dedupe_study_results(apps, schema_editor):
	"""
	Collapse duplicate (userStudy, studyVariable) StudyResult rows created before
	the unique constraint existed (e.g. from re-running an import without an
	upsert-safe DB constraint). For each duplicate group, keep the row with a
	non-empty value (highest id wins on ties) and delete the rest.
	"""
	StudyResult = apps.get_model('main', 'StudyResult')

	duplicate_keys = (
		StudyResult.objects.values('userStudy_id', 'studyVariable_id')
		.annotate(row_count=models.Count('id'))
		.filter(row_count__gt=1)
	)

	for key in duplicate_keys:
		rows = list(
			StudyResult.objects.filter(
				userStudy_id=key['userStudy_id'],
				studyVariable_id=key['studyVariable_id'],
			).order_by('id'),
		)

		keeper = None
		for row in rows:
			if row.value:
				keeper = row  # last non-empty row wins (rows are id-ordered)
		if keeper is None:
			keeper = rows[-1]

		StudyResult.objects.filter(
			userStudy_id=key['userStudy_id'],
			studyVariable_id=key['studyVariable_id'],
		).exclude(id=keeper.id).delete()


class Migration(migrations.Migration):

	dependencies = [
		('main', '0003_userstudy_testeddate'),
	]

	operations = [
		migrations.RunPython(dedupe_study_results, migrations.RunPython.noop),
		migrations.AddConstraint(
			model_name='studyresult',
			constraint=models.UniqueConstraint(
				fields=['userStudy', 'studyVariable'],
				name='unique_studyresult_per_userstudy_variable',
			),
		),
	]
