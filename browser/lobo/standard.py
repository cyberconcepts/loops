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
View classes for lobo (blueprint-based) layouts.

$Id$
"""

from cgi import parse_qs
from zope import interface, component
from zope.app.pagetemplate import ViewPageTemplateFile
from zope.cachedescriptors.property import Lazy

from cybertools.typology.interfaces import IType
from loops.browser.concept import ConceptView as BaseConceptView
from loops.browser.concept import ConceptRelationView as BaseConceptRelationView
from loops.common import adapted, baseObject


standard_template = ViewPageTemplateFile('standard.pt')


class Base(BaseConceptView):

    template = standard_template
    templateName = 'lobo.standard'
    macroName = None

    @Lazy
    def macros(self):
        return self.controller.getTemplateMacros(self.templateName, self.template)

    @property
    def macro(self):
        return self.macros[self.macroName]


class ConceptView(BaseConceptView):

    idx = 0

    def __init__(self, context, request):
        super(ConceptView, self).__init__(baseObject(context), request)
        self.adapted = context

    @Lazy
    def resources(self):
        result = dict(texts=[], images=[], files=[])
        for r in self.context.getResources([self.defaultPredicate]):
            if r.contentType.startswith('text/'):
                result['texts'].append(r)
            if r.contentType.startswith('image/'):
                result['images'].append(r)
            else:
                result['files'].append(r)
        return result

    # properties from base class: title, description, renderedDescription

    @Lazy
    def renderedText(self):
        for r in self.resources['texts']:
                return self.renderText(r.data, r.contentType)

    @Lazy
    def targetUrl(self):
        return self.nodeView.getUrlForTarget(self.context)

    @Lazy
    def cssClass(self):
        pattern = self.parentView.gridPattern
        if pattern:
            return pattern[self.idx % len(pattern)]

    @Lazy
    def style(self):
        return 'height: %ipx' % self.parentView.height

    @Lazy
    def img(self):
        for r in self.resources['images']:
                src = ('%s/mediaasset.html?v=%s' %
                            (self.nodeView.getUrlForTarget(r),
                             self.parentView.imageSize))
                return dict(src=src, cssClass=self.parentView.imageCssClass)


class ConceptRelationView(BaseConceptRelationView, ConceptView):

    def __init__(self, relation, request, contextIsSecond=False,
                 parent=None, idx=0):
        BaseConceptRelationView.__init__(self, relation, request, contextIsSecond)
        self.parentView = parent
        self.idx = idx


class Layout(Base):

    macroName = 'layout'

    def getParts(self):
        result = []
        ann = self.request.annotations.get('loops.view', {})
        params = parse_qs(ann.get('params') or '')
        parts = (params.get('parts') or ['h1,g3'])[0].split(',')
        for p in parts:
            viewName = 'lobo_' + p
            view = component.queryMultiAdapter((self.context, self.request),
                                               name=viewName)
            if view is not None:
                result.append(view)
        return result


class BasePart(Base):

    imageSize = 'small'
    imageCssClass = ''
    height = 260
    gridPattern = []

    def getChildren(self):
        result = []
        for idx, r in enumerate(
                self.context.getChildRelations([self.defaultPredicate])):
            result.append(ConceptRelationView(r, self.request,
                                contextIsSecond=True, parent=self, idx=idx))
        return result

    def getView(self):
        view = component.getMultiAdapter((self.adapted, self.request),
                                         name='lobo_cell')
        view.parentView = self
        return view


class Grid3(BasePart):

    macroName = 'grid'
    imageSize = 'small'
    height = 260
    gridPattern = ['span-2', 'span-2', 'span-2 last']


class List1(BasePart):

    macroName = 'list1'
    imageSize = 'small'
    gridPattern = [['span-2 clear', 'span-4 last']]


class Header1(BasePart):

    macroName = 'header1'
    imageSize = 'small'
    imageCssClass = 'flow-left'


class Header2(BasePart):

    macroName = 'header2'
    imageSize = 'medium'
    imageCssClass = 'flow-left'


