from enum import Enum
from typing import Any

from .Theme import ThemeFolder

__all__ = ['File', 'FileMaker', 'FileType', 'Files']


class FileType(Enum):
	common = 'common'
	css = 'css'
	js = 'js'
	font = 'font'
	icon = 'icon'


class FileMaker:

	def __init__(self, **kwargs):
		for key, value in kwargs.items():
			setattr(self, key, value)

	def __repr__(self):
		return f'{self.__dict__}'


class File:
	css: str = NotImplemented
	js: str = NotImplemented
	font: str = NotImplemented
	icon: str = NotImplemented

	def __repr__(self):
		return f'css: \n{self.css}\njs: \n{self.js}'


class Files:
	__theme__: type[Enum] | Enum

	common: FileMaker = NotImplemented
	css: FileMaker = NotImplemented
	js: FileMaker = NotImplemented
	font: FileMaker = NotImplemented
	icon: FileMaker = NotImplemented

	def __init__(self, theme: type[Enum] | Enum):
		self.__theme__ = theme

		self.createFiles()

	def createFiles(self):
		for fileType in FileType:
			files = getattr(self, fileType.value, NotImplemented)
			if files is not NotImplemented and isinstance(files, FileMaker):
				for file_name in files.__dict__:
					file = files.__getattribute__(file_name)
					if not isinstance(file, str):
						file = (file, 1)
					self.createFile(file, fileType, file_name)

	FILE_PATH_INDEX = 0
	FILE_VERSION_INDEX = 1
	FILE_FOLDER_INDEX = 2

	def createFile(self, file: tuple, file_type: FileType, file_name: str):
		file_path = file[self.FILE_PATH_INDEX]
		version = file[self.FILE_VERSION_INDEX] if len(file) > self.FILE_VERSION_INDEX else 1
		folder = file[self.FILE_FOLDER_INDEX] if len(file) > self.FILE_FOLDER_INDEX else ThemeFolder.common

		if not getattr(self, file_name, False):
			setattr(self, file_name, File())

		if file_type in (FileType.common, FileType.css):
			attr = getattr(self, file_name, NotImplemented)
			if hasattr(attr, 'css'):
				attr.css = self.cssFile(file_path, version, folder, urlOnly=True)
		if file_type in (FileType.common, FileType.js):
			attr = getattr(self, file_name, NotImplemented)
			if hasattr(attr, 'js'):
				attr.js = self.jsFile(file_path, version, folder, urlOnly=True)
		if file_type in (FileType.common, FileType.font):
			attr = getattr(self, file_name, NotImplemented)
			if hasattr(attr, 'font'):
				attr.font = self.fontFile(file_path, version, folder, urlOnly=True)
		if file_type in (FileType.common, FileType.icon):
			attr = getattr(self, file_name, NotImplemented)
			if hasattr(attr, 'icon'):
				attr.icon = self.iconFile(file_path, version, folder, urlOnly=True)

	def cssFile(self, file: str, version: int = 2, folder: Any = ThemeFolder.common, *, urlOnly: bool = False):
		if folder == ThemeFolder.theme:
			folder = self.__theme__
		if not isinstance(folder, str):
			folder = folder.value
		file = f'css/{folder}/{file}'
		if urlOnly:
			return file + '.css?v=' + str(version)
		return '<link rel="stylesheet" type="text/css" href="{}">'.format(
			'{% static ' + file + '.css?v=' + str(version) + ' %}',
		)

	def jsFile(self, file: str, version: int = 1, folder: Any = ThemeFolder.common, *, urlOnly: bool = False):
		if folder == ThemeFolder.theme:
			folder = self.__theme__
		if not isinstance(folder, str):
			folder = folder.value
		file = f'js/{folder}/{file}'
		if urlOnly:
			return file + '.js?v=' + str(version)
		return '<script src="{}"></script>'.format('{% static ' + file + '.js?v=' + str(version) + ' %}')

	def fontFile(self, file: str, version: int = 1, folder: Any = ThemeFolder.common, *, urlOnly: bool = False):
		if folder == ThemeFolder.theme:
			folder = self.__theme__
		file = f'fonts/{folder}/{file}'
		if urlOnly:
			return file + '.css?v=' + str(version)
		return '<link rel="stylesheet" type="text/css" href="{}">'.format(
			'{% static ' + file + '.css?v=' + str(version) + ' %}',
		)

	def iconFile(self, file: str, version: int = 1, folder: Any = ThemeFolder.common, *, urlOnly: bool = False):
		if folder == ThemeFolder.theme:
			folder = self.__theme__
		file = f'icons/{folder}/{file}'
		if urlOnly:
			return file + '.css?v=' + str(version)
		return '<link rel="stylesheet" type="text/css" href="{}">'.format(
			'{% static ' + file + '.css?v=' + str(version) + ' %}',
		)
