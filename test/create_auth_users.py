import json
import os

from icecream import ic

from vvecon.zorion import scripts

scripts.config('\\'.join(ic(os.path.dirname(__file__)).split('\\')[:-1]))

from authentication.models import User as AuthUser
from biom.models import User as BiomUser


def main():
	# Load all biom users (adjust as needed for your ORM or data access)
	biom_users = BiomUser.objects.all()
	id_map = {}

	for biom_user in biom_users:
		# Create a corresponding authentication user
		auth_user = AuthUser(
			username=''.join(biom_user.email.split('@')[0].split('.')),
			email=biom_user.email,
			firstName=biom_user.name.split(' ')[0] if biom_user.name else '',
			lastName=' '.join(biom_user.name.split(' ')[1:]) if biom_user.name and len(biom_user.name.split(' ')) > 1 else '',
		)
		auth_user.save()
		id_map[str(biom_user.id)] = str(auth_user.id)

	# Save mapping to JSON
	with open('biom_to_auth_id_map.json', 'w') as f:
		json.dump(id_map, f, indent=2)


if __name__ == '__main__':
	main()
