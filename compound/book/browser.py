#
#  Copyright (c) 2012 Helmut Merz helmutm@cy55.de
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
    def isPartOfPredicate(self):
        return self.conceptManager['ispartof']

    @Lazy
    def breadcrumbsParent(self):
        for p in self.context.getParents([self.isPartOfPredicate]):
            return self.nodeView.getViewForTarget(p)


class SectionView(Base, ConceptView):

    @Lazy
    def macro(self):
        return book_template.macros['section']

    @Lazy
    def tabview(self):
        if self.editable:
            return 'index.html'

    @Lazy
    def documentTypeType(self):
        return self.conceptManager['documenttype']

    @Lazy
    def sectionType(self):
        return self.conceptManager['section']

    def getCssClassForResource(self, r):
        for c in r.context.getConcepts([self.defaultPredicate]):
            if c.conceptType == self.documentTypeType:
                return getName(c)
        return 'textelement'

    def getParentsForResource(self, r):
        for c in r.context.getConcepts([self.defaultPredicate]):
            if c.conceptType not in (self.documentTypeType, self.sectionType):
                yield c


# layout parts - probably obsolete:

class PageLayout(Base, standard.Layout):

    def getParts(self):
        parts = ['headline', 'keyquestions', 'quote', 'maintext', 
                 'story', 'usecase']
        return self.getPartViews(parts)


class PagePart(object):

    template = book_template
    templateName = 'compound.book'
    macroName = 'text'
    partName = None     # define in subclass
    gridPattern = ['span-4']

    def getResources(self):
        result = []
        res = self.adapted.getParts().get(self.partName) or []
        for idx, r in enumerate(res):
            result.append(standard.ResourceView(
                                r, self.request, parent=self, idx=idx))
        return result


class Headline(PagePart, standard.Header2):

    macroName = 'headline'


class MainText(PagePart, standard.BasePart):

    partName = 'maintext'


class KeyQuestions(PagePart, standard.BasePart):

    partName = 'keyquestions'


class Story(PagePart, standard.BasePart):

    partName = 'story'


class UseCase(PagePart, standard.BasePart):

    partName = 'usecase'


class Quote(PagePart, standard.BasePart):

    partName = 'quote'
    gridPattern = ['span-2 last']
