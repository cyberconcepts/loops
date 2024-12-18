# loops/inst/loops/config.py

from dotenv import load_dotenv
from os import getenv

load_dotenv()

server_id = getenv('SERVER_ID')
zope_conf = getenv('ZOPE_CONF', 'zope.conf')
server_port = getenv('SERVER_PORT',
        server_id and getenv(f'SERVER_PORT_{server_id}')) or '8080'

shell_pw = (getenv('SHELL_PW', 'dummy'))
loops_path = (getenv('LOOPS_PATH', None))

# storage settings
from scopes.storage.db.postgres import StorageFactory
dbengine = 'postgresql+psycopg'
dbname = getenv('DBNAME', 'demo')
dbuser = getenv('DBUSER', 'demo')
dbpassword = getenv('DBPASSWORD', 'secret')
dbschema = getenv('DBSCHEMA', 'demo')
