import os
from pathlib import Path

BASE_DIR = Path(os.environ.get('DJANGO_SETTINGS_BASE_PATH', '.')).resolve()
DEBUG = os.environ.get('DEBUG', 'true').lower() == 'true'
SECRET_KEY = os.environ.get('SECRET_KEY', 'secret_key')
ENV = os.environ.get('ENVIRONMENT', 'development')
TIME_ZONE = os.environ.get('TIME_ZONE', 'UTC')
USE_TZ = True

if 'INSTALLED_APPS' not in globals():
	INSTALLED_APPS: list[str] = []

INSTALLED_APPS = [
	'authentication.apps.AuthenticationConfig',
	'settings.apps.SettingsConfig',
	'main.apps.MainConfig',
	'admins.apps.AdminConfig',
	# 'biom.apps.BiomConfig',
] + INSTALLED_APPS + [
	'allauth',
	'allauth.account',
	'allauth.socialaccount',
	'allauth.socialaccount.providers.google',
	'allauth.socialaccount.providers.apple',
	'django_vite',
	'django_cotton',
	'drf_spectacular',
	'drf_spectacular_sidecar',
	'django_q',
	# 'core.apps.MongoAdminConfig',
	# 'core.apps.MongoAuthConfig',
	# 'core.apps.MongoContentTypesConfig',
]

# Django-Q Configuration (Background Task Processing)
Q_CLUSTER = {
	'name': 'biom',
	'workers': 2,
	'recycle': 500,
	'timeout': 3600,  # 1 hour max per task
	'retry': 3700,
	'queue_limit': 50,
	'bulk': 10,
	'orm': 'default',  # Use ORM broker (SQLite compatible)
	'catch_up': True,  # Handle tasks after restart
}

if 'REST_FRAMEWORK' not in globals():
	REST_FRAMEWORK: dict = {}
REST_FRAMEWORK['DEFAULT_SCHEMA_CLASS'] = 'drf_spectacular.openapi.AutoSchema'
SPECTACULAR_SETTINGS = {
	# Spectacular settings
    'TITLE': 'BIOM API',
    'DESCRIPTION': 'API for BIOM',
    'VERSION': '1.0.0',
    'SERVE_INCLUDE_SCHEMA': False,
	# Sidecar settings
	'SWAGGER_UI_DIST': 'SIDECAR',
    'SWAGGER_UI_FAVICON_HREF': 'SIDECAR',
    'REDOC_DIST': 'SIDECAR',
}

DATABASES = {
	'default': {
		'ENGINE': 'django.db.backends.sqlite3',
		'NAME': BASE_DIR / 'db.sqlite3',
	},
} if DEBUG else {
	'default': {
		'ENGINE': 'django.db.backends.postgresql',
		'NAME': os.environ.get('DB_NAME', 'biom_db'),
		'USER': os.environ.get('DB_USER', 'biom_user'),
		'PASSWORD': os.environ.get('DB_PASSWORD', '58ZFp7j6SK5PrWGG'),
		'HOST': os.environ.get('DB_HOST', 'localhost'),
		'PORT': os.environ.get('DB_PORT', '5432'),
		'ATOMIC_REQUESTS': True,
		'CONN_MAX_AGE': 600,
	},
}

# DATABASE_ROUTERS = ['django_mongodb_backend.routers.MongoRouter']

if 'TEMPLATES' not in globals():
	TEMPLATES: list = [{'DIRS': [], 'OPTIONS': {'context_processors': [], 'loaders': [], 'builtins': []}}]

TEMPLATES[0]['DIRS'] += [BASE_DIR / 'static/components']
TEMPLATES[0]['OPTIONS']['context_processors'] += ['django.template.context_processors.request']
TEMPLATES[0]['OPTIONS']['loaders'] = [(
	'django.template.loaders.cached.Loader',
	[
		'django_cotton.cotton_loader.Loader',
		'django.template.loaders.filesystem.Loader',
		'django.template.loaders.app_directories.Loader',
	],
)]
TEMPLATES[0]['OPTIONS']['builtins'] = [
	'django_cotton.templatetags.cotton',
]

if 'MIDDLEWARE' not in globals():
	MIDDLEWARE: list = []
MIDDLEWARE += [
	'allauth.account.middleware.AccountMiddleware',
]

AUTH_USER_MODEL = 'authentication.User'

SITE_ID = 2

STATIC_URL = 'static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
if 'STATICFILES_DIRS' not in globals():
	STATICFILES_DIRS = []
STATICFILES_DIRS += [
    BASE_DIR / 'assets',
	BASE_DIR / 'static',
]

# Media files (Images)
MEDIA_URL = 'media/'
MEDIA_ROOT = BASE_DIR / 'media'

APPEND_SLASH = True

# AUTHENTICATION_BACKENDS = [
# 	'django.contrib.auth.backends.ModelBackend',
# 	'allauth.account.auth_backends.AuthenticationBackend',
# ]

SOCIALACCOUNT_PROVIDERS = {
	'google': {
		'SCOPE': [
			'email',
			'profile',
		],
		'AUTH_PARAMS': {
			'access_type': 'online',
		},
	},
}

SOCIALACCOUNT_LOGIN_ON_GET = True
SOCIALACCOUNT_ADAPTER = 'authentication.adapters.SocialAccountAdapter'
LOGIN_REDIRECT_URL = 'http://127.0.0.1:8000/auth/social/login/redirect/'

if 'JAZZMIN_SETTINGS' not in globals():
	JAZZMIN_SETTINGS = {}

JAZZMIN_SETTINGS['site_title'] = 'BIOM Admin'
JAZZMIN_SETTINGS['site_header'] = 'BIOM'
JAZZMIN_SETTINGS['site_brand'] = 'BIOM'
JAZZMIN_SETTINGS['welcome_sign'] = 'Welcome to the BIOM Admin'
JAZZMIN_SETTINGS['site_logo'] = 'img/logo.png'
JAZZMIN_SETTINGS['site_icon'] = 'img/biom.png'

JAZZMIN_SETTINGS['icons'] = {
}

DJANGO_VITE = {
  'default': {
    'dev_mode': DEBUG,
  },
}
DJANGO_VITE_ASSETS_PATH = BASE_DIR / 'staticfiles'

ACCOUNT_LOGIN_METHODS = {'username'}
ACCOUNT_SIGNUP_FIELDS =  ['firstName*', 'lastName*', 'username*', 'password1*', 'password2*']
ACCOUNT_EMAIL_VERIFICATION = 'none'

# AWS S3 Bucket Configurations
AWS_ACCESS_KEY_ID = os.environ.get('AWS_ACCESS_KEY_ID', '')
AWS_SECRET_ACCESS_KEY = os.environ.get('AWS_SECRET_ACCESS_KEY', '')
AWS_STORAGE_BUCKET_NAME = os.environ.get('AWS_STORAGE_BUCKET_NAME', '')
AWS_S3_REGION_NAME = os.environ.get('AWS_S3_REGION_NAME', '')

# Icecast Server Configurations
ICECAST_SERVER_HOST = os.environ.get('ICECAST_SERVER_HOST', 'localhost')
ICECAST_SERVER_PORT = int(os.environ.get('ICECAST_SERVER_PORT', '8000'))
ICECAST_ADMIN_USER = os.environ.get('ICECAST_ADMIN_USER', 'admin')
ICECAST_ADMIN_PASSWORD = os.environ.get('ICECAST_ADMIN_PASSWORD', 'hackme')
ICECAST_SOURCE_PASSWORD = os.environ.get('ICECAST_SOURCE_PASSWORD', 'hackme')
ICECAST_RELAY_PASSWORD = os.environ.get('ICECAST_RELAY_PASSWORD', 'hackme')
ICECAST_ADMIN_EMAIL = os.environ.get('ICECAST_ADMIN_EMAIL', 'admin@example.com')
ICECAST_LOCATION = os.environ.get('ICECAST_LOCATION', 'Earth')
ICECAST_MAX_SOURCES = int(os.environ.get('ICECAST_MAX_SOURCES', '10'))
ICECAST_MAX_LISTENERS = int(os.environ.get('ICECAST_MAX_LISTENERS', '100'))

# MIGRATION_MODULES = {
#     'admin': 'mongo_migrations.admin',
#     'auth': 'mongo_migrations.auth',
#     'contenttypes': 'mongo_migrations.contenttypes',
# }
# DATABASE_ROUTERS = [
#     'biom.db_router.BiomRouter',
# ]

if not DEBUG:
	ALLOWED_HOSTS = [
		'biom.arceion.com',
		'www.biom.arceion.com',
	]

	SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
	USE_X_FORWARDED_HOST = True

	CSRF_TRUSTED_ORIGINS = [
		'https://biom.arceion.com',
		'https://www.biom.arceion.com',
	]
	SESSION_COOKIE_SECURE = True
	CSRF_COOKIE_SECURE = True
