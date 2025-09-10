from dotenv import load_dotenv

from vvecon.zorion.utils import Utils

load_dotenv()

if 'ENV_PREFIX' not in globals():
    ENV_PREFIX = 'DJANGO_CORE_SETTINGS_'

Utils.deepUpdate(globals(), Utils.groupEnv(ENV_PREFIX))
