from vvecon.zorion import utils

__all__ = ['Files']


class Files(utils.Files):
    common = utils.FileMaker(
    )

    css = utils.FileMaker(
    )

    js = utils.FileMaker(
    )

    font = utils.FileMaker(
        poppins='poppins/poppins',
    )

    icon = utils.FileMaker(
        bootstrap='bootstrap/bootstrap-icons.min',
    )
