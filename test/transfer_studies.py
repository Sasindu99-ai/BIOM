import json
import os

from vvecon.zorion import scripts

scripts.config('\\'.join(os.path.dirname(__file__).split('\\')[:-1]))

from authentication.models import User
from biom.models.Study import Study as BiomStudy
from main.enums import StudyCategory, StudyStatus
from main.models.Study import Study as MainStudy

# Load biom_to_auth_id_map.json
with open(os.path.join(os.path.dirname(__file__), 'biom_to_auth_id_map.json')) as f:
    biom_to_auth_id_map = json.load(f)

study_id_map = {}

for biom_study in BiomStudy.objects.all():
    uploaded_by = None
    if biom_study.createdBy:
        uploaded_by_id = biom_to_auth_id_map.get(str(biom_study.createdBy))
        if uploaded_by_id:
            try:
                uploaded_by = User.objects.get(id=uploaded_by_id)
            except User.DoesNotExist:
                uploaded_by = None

    # Map enums from biom to main
    category = None
    if biom_study.category:
        for choice, _ in StudyCategory.choices:
            if biom_study.category == choice:
                category = choice
                break

    status = None
    if biom_study.status:
        for choice, _ in StudyStatus.choices:
            if biom_study.status == choice:
                status = choice
                break
        if not status:
            status = StudyStatus.ACTIVE  # fallback

    main_study = MainStudy(
        name=biom_study.name,
        description=biom_study.description,
        category=category,
        status=status,
        createdBy=uploaded_by,
        reference=biom_study.reference or '',
        version=biom_study.version or 1,
    )
    main_study.save()
    study_id_map[str(main_study.id)] = str(biom_study.id)
    print(f'Transferred Study: {biom_study.name} ({biom_study.id}) -> {main_study.id}')

# Save mapping to JSON
with open(os.path.join(os.path.dirname(__file__), 'study_id_map.json'), 'w') as f:
    json.dump(study_id_map, f, indent=2)
print('Study transfer complete. Mapping saved to study_id_map.json.')
