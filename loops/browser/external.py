# loops.browser.external

""" view class(es) for import/export.
"""

from zope.app import zapi
from zope.app.pagetemplate.viewpagetemplatefile import ViewPageTemplateFile
from zope.cachedescriptors.property import Lazy
from zope.security.proxy import removeSecurityProxy
from cStringIO import StringIO

from loops.external.external import IExternalContentSource
from loops.external.external import ILoader, IExporter


class NodesExportImport(object):
    """ View providing export and import functionality.
    """

    def __init__(self, context, request):
        #self.context = removeSecurityProxy(context)
        self.context = context
        self.request = request
        self.message = u''

    def submit(self):
        action = self.request.get('loops.action', None)
        if action:
            method = getattr(self, action, None)
            if method:
                return method()
        return False

    def export(self):
        f = StringIO()
        exporter = IExporter(self.context)
        exporter.dumpData(f, noclose=True)
        text = f.getvalue()
        f.close()
        self.setDownloadHeader(self.request, text)
        return text

    def upload(self):
        data = self.request.get('field.data', None)
        if not data:
            return False
        importer = IExternalContentSource(self.context)
        text = importer.getData(data)
        loader = ILoader(self.context)
        loader.load(text)
        self.message = u'Content uploaded and imported.'
        return False

    def setDownloadHeader(self, request, text):
        response = request.response
        response.setHeader('Content-Disposition',
                           'attachment; filename=loopscontent.dmp')
        response.setHeader('Content-Type', 'text/plain')
        response.setHeader('Content-Length', len(text))

