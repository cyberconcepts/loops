# loops/config.py
# (used for testing only)

from dotenv import load_dotenv
from os import getenv

load_dotenv()

server_port = getenv('SERVER_PORT', '8099')

app_factory = zope_app_factory

# storage settings
dbengine = 'postgresql+psycopg'
dbname = getenv('DBNAME', 'demo')
dbuser = getenv('DBUSER', 'demo')
dbpassword = getenv('DBPASSWORD', 'secret')
dbschema = getenv('DBSCHEMA', 'demo')

