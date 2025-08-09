# loops/inst/loops/config.py

from dotenv import load_dotenv
from os import getenv

load_dotenv()

server_id = getenv('SERVER_ID')
zope_conf = getenv('ZOPE_CONF', 'zope.conf')
server_port = getenv('SERVER_PORT',
        server_id and getenv(f'SERVER_PORT_{server_id}')) or '8080'
base_url = getenv('BASE_URL', 
        server_id and getenv(f'BASE_URL_{server_id}')) or 'https://test.example.com'

shell_pw = (getenv('SHELL_PW', 'dummy'))
loops_path = (getenv('LOOPS_PATH', 'loops/demo'))

# storage settings
from scopes.storage.db.postgres import StorageFactory
dbengine = getenv('DBENGINE', 'postgresql+psycopg')
dbname = getenv('DBNAME', 'demo')
dbuser = getenv('DBUSER', 'demo')
dbpassword = getenv('DBPASSWORD', 'secret')
dbschema = getenv('DBSCHEMA', 'demo')

# OpenID Connect (OIDC, e.g. via zitadel) authentication settings
oidc_provider = getenv('OIDC_PROVIDER', '') #'https://instance1-abcdef.zitadel.cloud')
oidc_client_id = getenv('OIDC_CLIENT_ID', '12345')
oidc_params = dict(
    op_config_url=oidc_provider + '/.well-known/openid-configuration',
    op_uris=None,
    op_keys=None,
    callback_url=getenv('OIDC_CALLBACK_URL', base_url + '/auth_callback'),
    client_id=oidc_client_id,
    principal_prefix=getenv('OIDC_PRINCIPAL_PREFIX', 'loops.'),
    cookie_name=getenv('OIDC_COOKIE_NAME', 'oidc_' + oidc_client_id),
    cookie_domain=getenv('OIDC_COOKIE_DOMAIN', None),
    cookie_lifetime=getenv('OIDC_COOKIE_LIFETIME', '86400'),
    cookie_crypt=getenv('OIDC_COOKIE_CRYPT', None),
    private_key_file=getenv('OIDC_SERVICE_USER_PRIVATE_KEY_FILE', '.private-key.json'),
    organization_id=getenv('OIDC_ORGANIZATION_ID', '12346'),
    project_id=getenv('OIDC_PROJECT_ID', '12347'),
)

