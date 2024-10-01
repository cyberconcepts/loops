# loops/inst/loops/main.py

import sys
from zope.securitypolicy import securitymap
sys.modules['zope.app.securitypolicy.securitymap'] = securitymap

import waitress
from zope.app.wsgi import config, getWSGIApplication

def run(app, config):
    port = int(config.server_port)
    #print(f'Serving on port {port}.')
    waitress.serve(app, port=port)


if __name__ == '__main__':
    import config
    app = getWSGIApplication('zope.conf')
    run(app, config)
