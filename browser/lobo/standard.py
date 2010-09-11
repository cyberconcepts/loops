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
from loops.browser.concept import ConceptView
from loops.common import adapted


standard_template = ViewPageTemplateFile('standard.pt')


class Base(ConceptView):

    template = standard_template
    templateName = 'lobo.standard'
    macroName = None

    @Lazy
    def macros(self):
        return self.controller.getTemplateMacros(self.templateName, self.template)

    @property
    def macro(self):
        return self.macros[self.macroName]


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
    height = 260
    gridPattern = []

    def getChildren(self):
        result = []
        for idx, c in enumerate(self.context.getChildren([self.defaultPredicate])):
            result.append(self.setupConcept(idx, c))
        return result

    def setupConcept(self, idx=0, obj=None):
        if obj is None:
            obj = self.context
        text = obj.title
        url = self.nodeView.getUrlForTarget(obj)
        style = 'height: %ipx' % self.height
        return dict(text=text, url=url, cssClass=self.getCssClass(idx, obj),
                    style=style, img=self.getImageData(idx, obj),
                    object=adapted(obj))

    def getCssClass(self, idx, obj):
        pattern = self.gridPattern
        if pattern:
            return pattern[idx % len(pattern)]

    def getImageData(self, idx, concept):
        for r in concept.getResources([self.defaultPredicate]):
            if r.contentType.startswith('image/'):
                src = ('%s/mediaasset.html?v=%s' %
                            (self.nodeView.getUrlForTarget(r), self.imageSize))
                return dict(src=src)


class Grid3(BasePart):

    macroName = 'grid'
    imageSize = 'small'
    height = 260
    gridPattern = ['span-2', 'span-2', 'span-2 last']


class List1(BasePart):

    macroName = 'list1'


class Header1(BasePart):

    macroName = 'header1'


class Header2(BasePart):

    macroName = 'header2'
    imageSize = 'medium'


