from typing import ClassVar

from vvecon.zorion import utils

__all__ = ['Data']


class Data(utils.Data):

	settings: ClassVar = dict(
		site1=utils.Settings(
			head='Welcome',
			app_name=' | BIOM',
			app_icon='img/biom-icon.png',
			site_name='https://biom.pythonanywhere.com',
			logo='img/biom-long.png',
		),
		admin=utils.Settings(
			head='Welcome',
			app_name=' | BIOM',
			app_icon='img/biom-icon.png',
			site_name='https://biom.pythonanywhere.com',
			logo='img/biom-long.png',
		),
	)

	meta: ClassVar = dict(
		site1=utils.Meta(
			description='',
			keywords=[],
		),
	)

	tracking = utils.Tracking(
		enabled=False,
		google='UA-XXXXX-X',
	)

	navigator = utils.Navigator()

	aside: ClassVar = dict(
		admin=utils.Aside(
			enabled=True,
			activeSlug='dashboard',
			asideType=1,
			content=dict(
				search=[
					dict(
						url='dashboard/datasets',
						# icon='bi bi-database text-green-500',
						label='Datasets',
						image=dict(
							src='img/dataset.svg'
						)
					),
				],
				biom=[
					dict(
						url='dashboard/patients',
						label='Patients',
						image=dict(
							src='img/patients.svg'
						)
					)
				]
			),
		)
	)

	footer = utils.Footer()
