import os
import json

from vvecon.zorion import scripts

scripts.config('\\'.join(os.path.dirname(__file__).split('\\')[:-1]))

from biom.models.StudyVariable import StudyVariable as BiomStudyVariable
from main.models.StudyVariable import StudyVariable as MainStudyVariable
from main.models.Study import Study as MainStudy
from main.enums import StudyVariableStatus, StudyVariableType, StudyVariableField

# Load study id map
with open(os.path.join(os.path.dirname(__file__), 'study_id_map.json'), 'r') as f:
    study_id_map = json.load(f)

variable_id_map = {}

def map_enum(value, enum_cls, default=None):
    if not value:
        return default
    for choice, _ in enum_cls.choices:
        if value == choice:
            return choice
    # fallback to default if not found
    return default

for biom_var in BiomStudyVariable.objects.all():
    # Map study
    main_study = None
    if biom_var.study:
        for main_id, biom_id in study_id_map.items():
            if str(biom_var.study) == biom_id:
                try:
                    main_study = MainStudy.objects.get(id=main_id)
                except MainStudy.DoesNotExist:
                    main_study = None
                break

    # Map enums
    status = map_enum(biom_var.status, StudyVariableStatus, StudyVariableStatus.ACTIVE)
    var_type = map_enum(biom_var.type, StudyVariableType, StudyVariableType.TEXT)
    field = map_enum(biom_var.type, StudyVariableField, StudyVariableField.TEXT)

    # Check for existing variable by name
    try:
        main_var = MainStudyVariable.objects.get(name=biom_var.name)
        print(f"Reused existing StudyVariable: {biom_var.name} -> {main_var.id}")
    except MainStudyVariable.DoesNotExist:
        main_var = MainStudyVariable(
            isRange=biom_var.isRange or False,
            name=biom_var.name,
            notes=biom_var.notes,
            status=status,
            type=var_type,
            field=field,
            isSearchable=biom_var.isSearchable or False,
            order=biom_var.order,
            isUnique=biom_var.isUnique or False,
        )
        main_var.save()
        print(f"Transferred StudyVariable: {biom_var.name} ({biom_var.id}) -> {main_var.id}")

    variable_id_map[str(main_var.id)] = str(biom_var.id)

    # Add to study.variables if study exists and has 'variables' m2m or related field
    if main_study:
        if hasattr(main_study, 'variables'):
            main_study.variables.add(main_var)
            main_study.save()
            print(f"Added variable {main_var.id} to study {main_study.id}")

# Save mapping to JSON
with open(os.path.join(os.path.dirname(__file__), 'study_variable_id_map.json'), 'w') as f:
    json.dump(variable_id_map, f, indent=2)
print("StudyVariable transfer complete. Mapping saved to study_variable_id_map.json.")
