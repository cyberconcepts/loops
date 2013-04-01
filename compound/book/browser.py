#
#  Copyright (c) 2013 Helmut Merz helmutm@cy55.de
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
View class(es) book/section/page structures.
"""

from cgi import parse_qs
from zope import interface, component
from zope.app.pagetemplate import ViewPageTemplateFile
from zope.cachedescriptors.property import Lazy
from zope.traversing.api import getName

from cybertools.typology.interfaces import IType
from loops.browser.lobo import standard
from loops.browser.concept import ConceptView
from loops.browser.concept import ConceptRelationView as \
    BaseConceptRelationView
from loops.browser.resource import ResourceView as BaseResourceView
from loops.common import adapted, baseObject


standard_template = standard.standard_template
book_template = ViewPageTemplateFile('view_macros.pt')


class Base(object):

    @Lazy
    def book_macros(self):
        return book_template.macros

    @Lazy
    def documentTypeType(self):
        return self.conceptManager['documenttype']

    @Lazy
    def sectionType(self):
        return self.conceptManager['section']

    @Lazy
    def isPartOfPredicate(self):
        return self.conceptManager['ispartof']

    @Lazy
    def showNavigation(self):
        return self.typeOptions.show_navigation

    @Lazy
    def breadcrumbsParent(self):
        for p in self.context.getParents([self.isPartOfPredicate]):
            return self.nodeView.getViewForTarget(p)

    @Lazy
    def neighbours(self):
        pred = succ = None
        parent = self.breadcrumbsParent
        if parent is not None:
            myself = None
            children = list(parent.context.getChildren([self.isPartOfPredicate]))
            for idx, c in enumerate(children):
                if c == self.context:
                    if idx > 0:
                        pred = self.nodeView.getViewForTarget(children[idx-1])
                    if idx < len(children) - 1:
                        succ = self.nodeView.getViewForTarget(children[idx+1])
        return pred, succ

    @Lazy
    def predecessor(self):
        return self.neighbours[0]

    @Lazy
    def successor(self):
        return self.neighbours[1]

    @Lazy
    def tabview(self):
        if self.editable:
            return 'index.html'

    def getResources(self):
        relViews = super(Base, self).getResources()
        return relViews

    @Lazy
    def textResources(self):
        self.images = [[]]
        result = []
        idx = 0
        for rv in self.getResources():
            if rv.context.contentType.startswith('text/'):
                idx += 1
                result.append(rv)
                self.images.append([])
            else:
                self.registerDojoLightbox()
                url = self.nodeView.getUrlForTarget(rv.context)
                src = '%s/mediaasset.html?v=small' % url
                fullSrc = '%s/mediaasset.html?v=medium' % url
                img = dict(src=src, fullImageUrl=fullSrc, title=rv.title,
                           description=rv.description, url=url, object=rv)
                self.images[idx].append(img)
        return result

    def getCssClassForResource(self, r):
        for c in r.context.getConcepts([self.defaultPredicate]):
            if c.conceptType == self.documentTypeType:
                return getName(c)
        return 'textelement'

    def getParentsForResource(self, r):
        for c in r.context.getConcepts([self.defaultPredicate]):
            if c != self.context and c.conceptType != self.documentTypeType:
                yield c


class BookView(Base, ConceptView):

    @Lazy
    def macro(self):
        return book_template.macros['book']


class SectionView(Base, ConceptView):

    @Lazy
    def macro(self):
        return book_template.macros['section']


class TopicView(Base, ConceptView):

    @Lazy
    def macro(self):
        return book_template.macros['topic']

