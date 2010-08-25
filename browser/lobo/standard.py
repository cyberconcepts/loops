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


class Basic3Columns(ConceptView):

    @Lazy
    def standard_macros(self):
        return self.controller.getTemplateMacros('lobo.standard', standard_template)

    @property
    def macro(self):
        return self.standard_macros['basic-image']

    def content(self):
        result = []
        for idx, c in enumerate(self.context.getChildren([self.defaultPredicate])):
            text = c.title
            url = self.nodeView.getUrlForTarget(c)
            cssClass = 'span-2'
            if idx % 3 == 2:
                cssClass += ' last'
            style = 'height: 260px'
            result.append(dict(text=text, url=url, cssClass=cssClass,
                               style=style, img=self.getImageData(c),
                               object=adapted(c)))
        return result

    def getImageData(self, concept):
        for r in concept.getResources([self.defaultPredicate]):
            if r.contentType.startswith('image/'):
                src = '%s/mediaasset.html?v=small' % self.nodeView.getUrlForTarget(r)
                return dict(src=src)
