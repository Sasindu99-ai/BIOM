import logging
import os

__all__ = ['Logger']

Logger = logging.getLogger('Logger')
logging.basicConfig(format='%(asctime)s [%(filename)s:%(lineno)d] %(levelname)s: %(message)s', level=logging.DEBUG)
Logger.__setattr__('basicConfig', logging.basicConfig)

file_handler = logging.FileHandler(
    os.environ.get('LOGGER', default=os.environ.get('DJANGO_SETTINGS_BASE_PATH', '.') + '/server.log'),
)
file_handler.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s [%(filename)s:%(lineno)d] %(levelname)s: %(message)s')
file_handler.setFormatter(formatter)
Logger.addHandler(file_handler)
