# loops/inst/loops/config.py

from dotenv import load_dotenv
from os import getenv

load_dotenv()

server_port = getenv('SERVER_PORT', '8099')

# storage settings
from scopes.storage.db.postgres import StorageFactory
dbengine = 'postgresql+psycopg'
dbname = getenv('DBNAME', 'demo')
dbuser = getenv('DBUSER', 'demo')
dbpassword = getenv('DBPASSWORD', 'secret')
dbschema = getenv('DBSCHEMA', 'demo')
