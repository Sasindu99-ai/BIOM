import json
import os

from vvecon.zorion import scripts

scripts.config('\\'.join(os.path.dirname(__file__).split('\\')[:-1]))

from authentication.models import User
from biom.models.BioMarker import BioMarker as BiomBioMarker
from main.models.BioMarker import BioMarker as MainBioMarker

# Load biom_to_auth_id_map.json
with open(os.path.join(os.path.dirname(__file__), 'biom_to_auth_id_map.json')) as f:
    biom_to_auth_id_map = json.load(f)

for biom_bm in BiomBioMarker.objects.all():
    uploaded_by_id = None
    if biom_bm.uploadedBy:
        uploaded_by_id = biom_to_auth_id_map.get(str(biom_bm.uploadedBy))
        if uploaded_by_id:
            try:
                uploaded_by = User.objects.get(id=uploaded_by_id)
            except User.DoesNotExist:
                uploaded_by = None
        else:
            uploaded_by = None
    else:
        uploaded_by = None

    main_bm = MainBioMarker(
        name=biom_bm.name,
        shortName=biom_bm.shortName,
        commonName=biom_bm.commonName,
        uniProtKB=biom_bm.uniProtKB,
        pdb=biom_bm.pdb,
        molecularWeight=biom_bm.molecularWeight or 0,
        molecularLength=biom_bm.molecularLength or 0,
        aaSequence=biom_bm.aaSequence,
        status=biom_bm.status,
        type=biom_bm.type,
        biomType=biom_bm.biomType,
        uploadedBy=uploaded_by,
        # administeredBy left as None
        version=biom_bm.version or 1,
        # image and ncib fields left as None
    )
    main_bm.save()
