# loops.server.main

# call main() for starting a loops server process

import sys

# module aliases - should be moved to loops.server.aliases
# or removed after migration with zodbupdate
from zope.securitypolicy import securitymap
sys.modules['zope.app.securitypolicy.securitymap'] = securitymap

from loops.server import auth
from scopes.web.auth import oidc
import waitress
from zope.app.wsgi import config, getWSGIApplication

def run(app, config):
    if config.oidc_provider:
        oidc.startup()
    port = int(config.server_port)
    print(f'Serving on port {port}.')
    waitress.serve(app, port=port)

def main():
    import config
    zope_conf = getattr(config, 'zope_conf', 'zope.conf')
    print(f'starting loops server... - conf: {zope_conf}')
    app = getWSGIApplication(zope_conf)
    auth.registerAuthUtility(config)
    run(app, config)

if __name__ == '__main__':
    main()
