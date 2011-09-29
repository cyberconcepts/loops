#
#  Copyright (c) 2010 Helmut Merz helmutm@cy55.de
#
#  This program is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 2 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software
#  Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
#

"""
view class(es) for import/export.

$Id$
"""

from cStringIO import StringIO
import os
import time
from zope import component
from zope.interface import Interface, implements
from zope.app.pagetemplate.viewpagetemplatefile import ViewPageTemplateFile
from zope.cachedescriptors.property import Lazy
from zope.security.proxy import removeSecurityProxy
from zope.traversing.api import getName, getPath, traverse

from cybertools.util.date import str2timeStamp
from loops.external.base import Loader, Extractor
from loops.external.interfaces import IReader, IWriter
from loops import util


class ExportImport(object):
    """ View providing export and import functionality.
    """

    def __init__(self, context, request):
        self.context = removeSecurityProxy(context)
        self.request = request
        self.message = u''

    @Lazy
    def baseDirectory(self):
        return util.getVarDirectory(self.request)

    @Lazy
    def sitePath(self):
        return getPath(self.context)[1:].replace('/', '_')

    @Lazy
    def resourceImportDirectory(self):
        return os.path.join(self.baseDirectory, 'import', self.sitePath)

    @Lazy
    def resourceExportDirectory(self):
        return os.path.join(self.baseDirectory, 'export', self.sitePath)

    def submit(self):
        action = self.request.get('loops.action', None)
        if action:
            method = getattr(self, action, None)
            if method:
                return method()
        return False

    def export(self):
        form = self.request.form
        nodes = parents = predicates = types = None
        nodePaths = form.get('nodes')
        if nodePaths:
            nodePaths = [p for p in nodePaths.splitlines() if p]
            nodes = [traverse(self.context.getViewManager(), p) for p in nodePaths]
            nodes = [p for p in nodes if p is not None]
        parentIds = form.get('parents')
        if parentIds:
            parentIds = [id for id in parentIds.splitlines() if id]
            parents = [self.conceptManager.get(id) for id in parentIds]
            parents = [p for p in parents if p is not None]
        predicateIds = form.get('predicates')
        if predicateIds:
            predicates = ([self.conceptManager[id] for id in predicateIds])
        typeIds = form.get('types')
        if typeIds:
            types = ([self.conceptManager[id] for id in typeIds])
        changed = form.get('changed')
        includeNodeTargets = form.get('include_node_targets')
        includeSubconcepts = form.get('include_subconcepts')
        includeResources = form.get('include_resources')
        extractor = Extractor(self.context, self.resourceExportDirectory)
        if changed:
            changed = self.parseDate(changed)
            if changed:
                elements = extractor.extractChanges(changed, parents,
                                    predicates, types)
        elif nodes:
            elements = extractor.extractNodes(topNodes=nodes,
                                              includeTargets=includeNodeTargets)
        elif parents:
            elements = extractor.extractForParents(parents, predicates, types,
                                    includeSubconcepts, includeResources)
        else:
            #elements = extractor.extract(types)
            elements = extractor.extract()
        return self.download(elements)

    def download(self, elements):
        writer = component.getUtility(IWriter)
        f = StringIO()
        writer.write(elements, f)
        text = f.getvalue()
        f.close()
        self.setDownloadHeader(self.request, text)
        return text

    @Lazy
    def conceptManager(self):
        return  self.context.getConceptManager()

    @Lazy
    def typePredicate(self):
        return self.conceptManager.getTypePredicate()

    @Lazy
    def types(self):
        ttype = self.conceptManager['type']
        return [dict(name=getName(p), title=p.title)
                for p in ttype.getChildren([self.typePredicate])]

    @Lazy
    def predicates(self):
        ptype = self.conceptManager['predicate']
        return [dict(name=getName(p), title=p.title)
                for p in ptype.getChildren([self.typePredicate])]

    def upload(self):
        data = self.request.get('field.data', None)
        resourceImportDirectory = (self.request.get('resourceImportDirectory', None)
                                   or self.resourceImportDirectory)
        if not data:
            return False
        reader = component.getUtility(IReader)
        elements = reader.read(data)
        loader = Loader(self.context, resourceImportDirectory)
        loader.load(elements)
        self.message = u'Content uploaded and imported.'
        return False

    def setDownloadHeader(self, request, text):
        response = request.response
        response.setHeader('Content-Disposition',
                           'attachment; filename=loopscontent.dmp')
        response.setHeader('Content-Type', 'text/plain')
        response.setHeader('Content-Length', len(text))

    def parseDate(self, s):
        return str2timeStamp(s)
