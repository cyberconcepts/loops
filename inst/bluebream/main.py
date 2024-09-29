# loops/inst/bluebream/main.py

import waitress
from zope.app.wsgi import config, getWSGIApplication

def run(app, config):
    port = int(config.server_port)
    waitress.serve(app, port=port)
    print(f'Serving on port {port}.')


if __name__ == '__main__':
    import config
    app = getWSGIApplication('zope.conf')
    run(app, config)
