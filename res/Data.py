from typing import ClassVar

from vvecon.zorion import utils

__all__ = ['Data']


class Data(utils.Data):

	settings: ClassVar = dict(
		site1=utils.Settings(
			head='Welcome',
			app_name=' | Nevada Broadcast',
			app_icon='img/common/logo.png',
			site_name='https://nevada-broadcast.com',
			logo='img/common/logo.png',
		),
		admin=utils.Settings(
			head='Welcome',
			app_name=' | Nevada Broadcast',
			app_icon='img/common/logo.png',
			site_name='https://nevada-broadcast.com',
			logo='img/common/logo.png',
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

	aside = utils.Aside()

	footer = utils.Footer()
