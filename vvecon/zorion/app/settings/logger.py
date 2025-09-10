from dotenv import load_dotenv

load_dotenv()

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'standard': {
            'format': '%(asctime)s %(levelname)s %(name)s %(message)s',
        },
    },
    'handlers': {
        'console': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'standard',
            'filters': [],
        },
    },
    'loggers': {
        logger_name: {
            'level': 'WARNING',
            'propagate': True,
        } for logger_name in (
            'django', 'django.request', 'django.server', 'django.db.backends', 'django.security', 'py.warnings',
            'core', 'vvecon',
        )
    },
    'root': {
        'level': 'DEBUG',
        'handlers': ['console'],
    },
}
