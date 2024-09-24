# py-scopes/demo/config.py

from dotenv import load_dotenv
from os import getenv
from scopes.server.app import zope_app_factory

load_dotenv()

server_port = getenv('SERVER_PORT', '8099')

app_factory = zope_app_factory

# storage settings
from scopes.storage.db.postgres import StorageFactory
dbengine = 'postgresql+psycopg'
dbname = getenv('DBNAME', 'demo')
dbuser = getenv('DBUSER', 'demo')
dbpassword = getenv('DBPASSWORD', 'secret')
dbschema = getenv('DBSCHEMA', 'demo')

