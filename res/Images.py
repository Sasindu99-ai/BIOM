from vvecon.zorion import utils

__all__ = ['Images']


class Images(utils.Images):
    images = utils.FileMaker(
        register='register.png',
    )
