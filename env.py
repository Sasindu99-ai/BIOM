from vvecon.zorion.enums import EnvMode
from vvecon.zorion.env import Env, EnvManager

__all__ = ['env']

env = EnvManager({
	EnvMode.DEBUG: Env(
		EnvMode.DEBUG,
		ENVIRONMENT='development',
		SECRET_KEY='dev_secret_key',
		TIME_ZONE='UTC',
		# AWS S3 configurations
		AWS_ACCESS_KEY_ID='',
		AWS_SECRET_ACCESS_KEY='',
		AWS_STORAGE_BUCKET_NAME='',
		AWS_S3_REGION_NAME='',
		# Icecast development configurations
		ICECAST_SERVER_HOST='',
		ICECAST_SERVER_PORT='8000',
		ICECAST_ADMIN_USER='',
		ICECAST_ADMIN_PASSWORD='',
		ICECAST_SOURCE_PASSWORD='',
		ICECAST_RELAY_PASSWORD='',
		ICECAST_ADMIN_EMAIL='',
		ICECAST_LOCATION='',
		ICECAST_MAX_SOURCES='10',
		ICECAST_MAX_LISTENERS='100',
		ADMIN_PATH='dashboard',
	),
	EnvMode.RELEASE: Env(
		EnvMode.RELEASE,
		ENVIRONMENT='production',
		SECRET_KEY='prod_secret_key',
		TIME_ZONE='Asia/Colombo',
		# AWS S3 configurations
		AWS_ACCESS_KEY_ID='',
		AWS_SECRET_ACCESS_KEY='',
		AWS_STORAGE_BUCKET_NAME='',
		AWS_S3_REGION_NAME='',
		# Icecast development configurations
		ICECAST_SERVER_HOST='',
		ICECAST_SERVER_PORT='8000',
		ICECAST_ADMIN_USER='',
		ICECAST_ADMIN_PASSWORD='',
		ICECAST_SOURCE_PASSWORD='',
		ICECAST_RELAY_PASSWORD='',
		ICECAST_ADMIN_EMAIL='',
		ICECAST_LOCATION='',
		ICECAST_MAX_SOURCES='10',
		ICECAST_MAX_LISTENERS='100',
		ADMIN_PATH='dashboard',
	),
}, default=EnvMode.DEBUG)
