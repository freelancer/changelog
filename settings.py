import os
from configparser import RawConfigParser

# Any valid SQLAlchemy connection string
ALCHEMY_URL = 'sqlite:///changelog.db'
LISTEN_HOST = '127.0.0.1'
LISTEN_PORT = 5000

# Use these to enable sending problems to Sentry
USE_SENTRY = False
SENTRY_DSN = None

# Loading site-specific override settings
env_config_path = os.getenv('CHANGELOG_SETTINGS_PATH')
config_path = (env_config_path if env_config_path
               else os.path.expanduser('~/changelog.cfg'))
print 'Loading user-specified settings from {}'.format(config_path)
config = RawConfigParser()
config.read(config_path)

if config.has_section('db'):
    ALCHEMY_URL = config.get('db', 'sqlalchemy_uri')
if config.has_section('sentry'):
    USE_SENTRY = config.getboolean('sentry', 'enable')
    SENTRY_DSN = config.get('sentry', 'dsn')

print 'Starting with settings:'
print {key: value for key, value in globals().items() if key.isupper()}
