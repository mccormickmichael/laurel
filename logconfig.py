import logging.config

CONFIG = {
    'version': 1,
    'disable_existing_loggers': True,
    'formatters': {
        'relative': {
            'format': '%(relativeCreated)6d:%(levelname)5s:%(name)s:%(message)s'
        },
        'simple': {
            'format': '%(levelname)5s %(message)s'
        }
    },
    'handlers': {
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'relative',
            'stream': 'ext://sys.stdout'
        }
    },
    'loggers': {
        'laurel': {
            'handlers': ['console'],
            'propagate': True,
            'level': 'DEBUG'
        },
        'boto3': {
            'handlers': ['console'],
            'propagate': False,
            'level': 'WARNING'
        },
        'botocore': {
            'handlers': ['console'],
            'propagate': False,
            'level': 'WARNING'
        }
    }
}


def config():
    logging.config.dictConfig(CONFIG)
