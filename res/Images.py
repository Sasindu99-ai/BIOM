from vvecon.zorion import utils

__all__ = ['Images']


class Images(utils.Images):
    images = utils.FileMaker(
        register='register.png',
		logo='biom-long.png',
		avatar='avatar.jpg',
		hero='biom-long-rbg.png',
		lab='register.png',
		dna='biom.png',
    )
