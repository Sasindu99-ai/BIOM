"""Re-derive each StudyVariable's data type from its actual stored values.

Existing variables were assigned a type at creation time from a small
sample of rows (or defaulted to TEXT). This command re-runs detection
against every value the variable actually has in StudyResult and corrects
the stored type (and the dependent `field` widget) where they disagree.
"""
from django.core.management.base import BaseCommand
from django.db.models import Count

from main.models import StudyResult, StudyVariable
from main.utils import detect_variable_type, field_for_type

__all__ = ['Command']


class Command(BaseCommand):
    help = 'Recompute StudyVariable.type from its stored StudyResult values and correct mismatches.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run', action='store_true',
            help='Report what would change without writing to the database.',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        variables = StudyVariable.objects.annotate(result_count=Count('results')).order_by('name')

        checked = changed = skipped_no_data = 0
        changes = []

        for var in variables:
            checked += 1
            if var.result_count == 0:
                skipped_no_data += 1
                continue

            values = StudyResult.objects.filter(studyVariable=var).values_list('value', flat=True)
            detected_type = detect_variable_type(values)

            if detected_type == var.type:
                continue

            changes.append((var, var.type, detected_type, var.result_count))
            changed += 1

            if not dry_run:
                var.type = detected_type
                var.field = field_for_type(detected_type)
                var.save(update_fields=['type', 'field'])

        for var, old_type, new_type, result_count in changes:
            self.stdout.write(
                f'{"[DRY RUN] " if dry_run else ""}'
                f'{var.name!r}: {old_type} -> {new_type} ({result_count} values)',
            )

        self.stdout.write(self.style.SUCCESS(
            f'Checked {checked} variables, {skipped_no_data} had no data, '
            f'{changed} {"would change" if dry_run else "updated"}.',
        ))
