import os
import json

from vvecon.zorion import scripts

scripts.config('\\'.join(os.path.dirname(__file__).split('\\')[:-1]))

from biom.models.StudyResult import StudyResult as BiomStudyResult
from main.models.UserStudy import UserStudy as MainUserStudy
from main.models.StudyResult import StudyResult as MainStudyResult
from authentication.models import User
from main.models.Study import Study as MainStudy
from main.models.StudyVariable import StudyVariable as MainStudyVariable
from main.enums import UserStudyStatus

# Load mapping files
with open(os.path.join(os.path.dirname(__file__), 'biom_to_auth_id_map.json'), 'r') as f:
    biom_to_auth_id_map = json.load(f)
with open(os.path.join(os.path.dirname(__file__), 'study_id_map.json'), 'r') as f:
    study_id_map = json.load(f)
with open(os.path.join(os.path.dirname(__file__), 'study_variable_id_map.json'), 'r') as f:
    variable_id_map = json.load(f)

userstudy_id_map = {}

def map_enum(value, enum_cls, default=None):
    if not value:
        return default
    for choice, _ in enum_cls.choices:
        if value == choice:
            return choice
    return default

for biom_sr in BiomStudyResult.objects.all():
    # Map user (createdBy)
    user = None
    if biom_sr.createdBy:
        user_id = biom_to_auth_id_map.get(str(biom_sr.createdBy))
        if user_id:
            try:
                user = User.objects.get(id=user_id)
            except User.DoesNotExist:
                user = None

    # Map study
    study = None
    if biom_sr.study:
        for main_id, biom_id in study_id_map.items():
            if str(biom_sr.study) == biom_id:
                try:
                    study = MainStudy.objects.get(id=main_id)
                except MainStudy.DoesNotExist:
                    study = None
                break

    # Map status
    status = map_enum(biom_sr.status, UserStudyStatus, UserStudyStatus.PENDING)

    # Create UserStudy
    main_userstudy = MainUserStudy(
        user=user,
        study=study,
        status=status,
        reference=biom_sr.reference or "",
        createdBy=user,
        version=biom_sr.version or 1,
    )
    main_userstudy.save()
    userstudy_id_map[str(main_userstudy.id)] = str(biom_sr.id)
    print(f"Transferred StudyResult: {biom_sr.id} -> UserStudy {main_userstudy.id}")

    # Transfer results if present
    if hasattr(biom_sr, 'results') and biom_sr.results:
        for biom_result in biom_sr.results:
            # Try to resolve variable by id mapping, then by name
            study_variable = None
            # First, try id mapping
            if biom_result.variable:
                for main_var_id, biom_var_id in variable_id_map.items():
                    if str(biom_result.variable) == biom_var_id:
                        try:
                            study_variable = MainStudyVariable.objects.get(id=main_var_id)
                        except MainStudyVariable.DoesNotExist:
                            study_variable = None
                        break
            # If not found, try by name
            if not study_variable:
                # Try to get variable name from biom
                try:
                    from biom.models.StudyVariable import StudyVariable as BiomStudyVariable
                    biom_var_obj = BiomStudyVariable.objects.using("biom").get(pk=biom_result.variable)
                    biom_var_name = biom_var_obj.name
                except Exception:
                    biom_var_name = None
                if biom_var_name:
                    try:
                        study_variable = MainStudyVariable.objects.get(name=biom_var_name)
                        print(f"  Matched variable by name: {biom_var_name} -> {study_variable.id}")
                    except MainStudyVariable.DoesNotExist:
                        study_variable = None
            if not study_variable:
                print(f"  Skipped result for StudyResult {biom_sr.id}: variable {biom_result.variable} not found in mapping or by name.")
                continue
            # Create StudyResult
            main_result = MainStudyResult(
                userStudy=main_userstudy,
                studyVariable=study_variable,
                value=biom_result.value,
            )
            main_result.save()
            print(f"  Transferred result variable={biom_result.variable} value={biom_result.value} -> {main_result.id}")

# Save mapping to JSON
with open(os.path.join(os.path.dirname(__file__), 'userstudy_id_map.json'), 'w') as f:
    json.dump(userstudy_id_map, f, indent=2)
print("StudyResults transfer complete. Mapping saved to userstudy_id_map.json.")
