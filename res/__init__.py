from vvecon.zorion import utils

from .Data import Data
from .Files import Files
from .Images import Images
from .Theme import Theme

__all__ = ['R']


class R(utils.R):

    def __init__(self, theme: type[Theme] | Theme = Theme.light):
        super(R, self).__init__(theme=theme)

        self.data = Data()
        self.files = Files(self.__theme__)
        self.images = Images(self.__theme__)
