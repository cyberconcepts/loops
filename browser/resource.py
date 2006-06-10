#
#  Copyright (c) 2006 Helmut Merz helmutm@cy55.de
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
View class for resource objects.

$Id$
"""

from zope.cachedescriptors.property import Lazy
from zope.app import zapi
from zope.app.catalog.interfaces import ICatalog
from zope.app.dublincore.interfaces import ICMFDublinCore
from zope.app.pagetemplate import ViewPageTemplateFile
from zope.formlib.form import FormFields
from zope.formlib.interfaces import DISPLAY_UNWRITEABLE
from zope.proxy import removeAllProxies
from zope.security import canAccess, canWrite
from zope.security.proxy import removeSecurityProxy

from loops.interfaces import IDocument, IMediaAsset
from loops.interfaces import IFileSystemResource, IControlledResource
from loops.browser.common import EditForm, BaseView
from loops.browser.concept import ConceptRelationView, ConceptConfigureView
from loops.browser.node import NodeView

renderingFactories = {
    'text/plain': 'zope.source.plaintext',
    'text/stx': 'zope.source.stx',
    'text/structured': 'zope.source.stx',
    'text/rest': 'zope.source.rest',
    'text/restructured': 'zope.source.rest',
}


class DocumentEditForm(EditForm):
    #form_fields = FormFields(IDocument, IFileSystemResource, IControlledResource)
    form_fields = FormFields(IDocument)
    for f in form_fields:
        f.render_context |= DISPLAY_UNWRITEABLE

class MediaAssetEditForm(EditForm):
    form_fields = FormFields(IMediaAsset)


class ResourceView(BaseView):

    template = ViewPageTemplateFile('resource_macros.pt')

    def concepts(self):
        for r in self.context.getConceptRelations():
            yield ConceptRelationView(r, self.request)

    def clients(self):
        for node in self.context.getClients():
            yield NodeView(node, self.request)


class ResourceConfigureView(ResourceView, ConceptConfigureView):

    def update(self):
        request = self.request
        action = request.get('action')
        if action is None:
            return True
        if action == 'create':
            self.createAndAssign()
            return True
        tokens = request.get('tokens', [])
        for token in tokens:
            parts = token.split(':')
            token = parts[0]
            if len(parts) > 1:
                relToken = parts[1]
            concept = self.loopsRoot.loopsTraverse(token)
            if action == 'assign':
                predicate = request.get('predicate') or None
                if predicate:
                    predicate = removeSecurityProxy(
                                    self.loopsRoot.loopsTraverse(predicate))
                self.context.assignConcept(removeSecurityProxy(concept), predicate)
            elif action == 'remove':
                predicate = self.loopsRoot.loopsTraverse(relToken)
                self.context.deassignConcept(concept, [predicate])
        return True

    def search(self):
        request = self.request
        if request.get('action') != 'search':
            return []
        searchTerm = request.get('searchTerm', None)
        searchType = request.get('searchType', None)
        result = []
        if searchTerm or searchType != 'none':
            criteria = {}
            if searchTerm:
                criteria['loops_title'] = searchTerm
            if searchType:
                if searchType.endswith('*'):
                    start = searchType[:-1]
                    end = start + '\x7f'
                else:
                    start = end = searchType
                criteria['loops_type'] = (start, end)
            cat = zapi.getUtility(ICatalog)
            result = cat.searchResults(**criteria)
            # TODO: can this be done in a faster way?
            result = [r for r in result if r.getLoopsRoot() == self.loopsRoot]
        else:
            result = self.loopsRoot.getConceptManager().values()
        if searchType == 'none':
            result = [r for r in result if r.conceptType is None]
        return self.viewIterator(result)


class DocumentView(ResourceView):

    macro = ResourceView.template.macros['render']
    
    def render(self):
        """ Return the rendered content (data) of the context object.
        """
        text = self.context.data
        typeKey = renderingFactories.get(self.context.contentType, None)
        if typeKey is None:
            return text
        source = zapi.createObject(typeKey, text)
        view = zapi.getMultiAdapter((removeAllProxies(source), self.request))
        return view.render()

    def show(self):
        data = self.context.data
        response = self.request.response
        response.setHeader('Content-Type', self.context.contentType)
        response.setHeader('Content-Length', len(data))
        return data

    
class MediaAssetView(ResourceView):

    @property
    def macro(self):
        if 'image/' in self.context.contentType:
            return self.template.macros['image']
        else:
            return self.template.macros['download']
