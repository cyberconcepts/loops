#
#  Copyright (c) 2008 Helmut Merz helmutm@cy55.de
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
View class(es) for integrating external objects.

$Id$
"""

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
    macroName = 'basic'
    imageSize = 'small'
    height = 260
    gridPattern = ['span-2', 'span-2', 'span-2 last']

    @Lazy
    def macros(self):
        return self.controller.getTemplateMacros(self.templateName, self.template)

    @property
    def macro(self):
        return self.macros[self.macroName]

    def content(self):
        result = []
        for idx, c in enumerate(self.context.getChildren([self.defaultPredicate])):
            result.append(self.setupItem(idx, c))
        return result

    def setupItem(self, idx, obj):
        text = obj.title
        url = self.nodeView.getUrlForTarget(obj)
        # TODO: use layout settings of context and c for display
        style = 'height: %ipx' % self.height
        return dict(text=text, url=url, cssClass=self.getCssClass(idx, obj),
                    style=style, img=self.getImageData(idx, obj),
                    object=adapted(obj))

    def getCssClass(self, idx, obj):
        pattern = self.gridPattern
        return pattern[idx % len(pattern)]

    def getImageData(self, idx, concept):
        for r in concept.getResources([self.defaultPredicate]):
            if r.contentType.startswith('image/'):
                src = ('%s/mediaasset.html?v=%s' %
                            (self.nodeView.getUrlForTarget(r), self.imageSize))
                return dict(src=src)


class Grid3(Base):

    pass


class Single1(Base):

    pass

