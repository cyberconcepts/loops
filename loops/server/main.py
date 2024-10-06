# loops.server.main

# call main() for starting a loops server process

import sys

# module aliases - should be moved to loops.server.aliases
from zope.securitypolicy import securitymap
sys.modules['zope.app.securitypolicy.securitymap'] = securitymap

import waitress
from zope.app.wsgi import config, getWSGIApplication

def run(app, config):
    port = int(config.server_port)
    #print(f'Serving on port {port}.')
    waitress.serve(app, port=port)

def main():
    import config
    zope_conf = getattr(config, 'zope_conf', 'zope.conf')
    print(f'starting loops server... - conf: {zope_conf}')
    app = getWSGIApplication(zope_conf)
    run(app, config)

if __name__ == '__main__':
    main()
