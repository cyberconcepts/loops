# loops/tests/config.py

from dotenv import load_dotenv
from os import getenv
from scopes.web.app import zope_app_factory

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

base_url = 'test://'

# special testing stuff
from scopes.tests import data_auth # add oidc URIs and keys to dummy_requests data
from scopes.tests import dummy_requests
import sys
sys.modules['requests'] = dummy_requests

# authentication settings
oidc_provider = 'test://oidc'
oidc_client_id = getenv('OIDC_CLIENT_ID', '12345')
oidc_params = dict(
    op_config_url=oidc_provider + '/.well-known/openid-configuration',
    op_uris=None,
    op_keys=None,
    callback_url=getenv('OIDC_CALLBACK_URL', base_url + '/auth/callback'),
    client_id=oidc_client_id,
    principal_prefix=getenv('OIDC_PRINCIPAL_PREFIX', 'loops.'),
    cookie_name=getenv('OIDC_COOKIE_NAME', 'oidc_' + oidc_client_id),
    cookie_domain=getenv('OIDC_COOKIE_DOMAIN', None),
    cookie_lifetime=getenv('OIDC_COOKIE_LIFETIME', '86400'),
    cookie_crypt=getenv('OIDC_COOKIE_CRYPT', None)
)

