from dataclasses import dataclass
from enum import Enum
from typing import Any

from .Files import FileMaker
from .Theme import ThemeFolder

__all__ = ['Image', 'Images']


@dataclass
class Image:
	path: str
	url: str
	alt: str = ''
	classList: str = ''
	style: str = ''
	width: str = ''
	height: str = ''
	elementId: str = ''

	def __str__(self):
		return self.alt


class Images:
	__theme__: type[Enum] | Enum
	images: FileMaker = NotImplemented

	def __init__(self, theme: type[Enum] | Enum):
		self.__theme__ = theme

		self.createImages()

	def createImages(self):
		if self.images is not NotImplemented and isinstance(self.images, FileMaker):
			for file_name in self.images.__dict__:
				file = self.images.__getattribute__(file_name)
				if isinstance(file, str):
					file = (file, 1)
				self.createImage(file, file_name)

	FILE_PATH_INDEX = 0
	FILE_VERSION_INDEX = 1
	FILE_FOLDER_INDEX = 2
	FILE_DATA_INDEX = 3

	def createImage(self, file: tuple, file_name: str):
		file_path = file[self.FILE_PATH_INDEX]
		version = file[self.FILE_VERSION_INDEX] if len(file) > self.FILE_VERSION_INDEX else 1
		folder = file[self.FILE_FOLDER_INDEX] if len(file) > self.FILE_FOLDER_INDEX else ThemeFolder.none
		data = file[self.FILE_DATA_INDEX] if len(file) > self.FILE_DATA_INDEX else False

		if not getattr(self, file_name, False):
			setattr(
				self, file_name,
				Image(*self.imageFile(file_path, version, folder, data=True), **(data if data else {})),
			)

	def imageFile(
		self, file: str, version: int, folder: Any, *, urlOnly: bool = False, data: bool = False,
	) -> str | tuple:
		if folder == ThemeFolder.theme:
			folder = self.__theme__
		file = f"img/{ f'{folder.value}/' if folder != ThemeFolder.none else ''}{file}"
		if data:
			return file, file + f'?v={version}', file.split('/')[-1].split('.')[0].replace('-', ' ').title()
		if urlOnly:
			return file, (file + f'?v={version}',)
		return file, '<img src="{}" alt="{}">'.format(
			'{% static ' + file + f'?v={version}' + ' %}',
			file.split('/')[-1].split('.')[0].replace('-', ' ').title(),
		)
