# loops.compound.book.browser

""" View class(es) book/section/page structures.
"""

from urllib.parse import parse_qs
from zope import interface, component
from zope.browserpage import ViewPageTemplateFile
from zope.cachedescriptors.property import Lazy
from zope.traversing.api import getName

from cybertools.meta.interfaces import IOptions
from cybertools.typology.interfaces import IType
from loops.browser.lobo import standard
from loops.browser.concept import ConceptView
from loops.browser.concept import ConceptRelationView as \
    BaseConceptRelationView
from loops.browser.resource import ResourceView as BaseResourceView
from loops.common import adapted, baseObject
from loops.util import _


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
    def tabview(self):
        if self.editable:
            return 'index.html'

    def children(self):
        for c in self.getChildren():
            if c.checkState():
                yield c

    def getResources(self):
        relViews = super(Base, self).getResources()
        return relViews

    @Lazy
    def textResources(self):
        self.images = [[]]
        self.otherResources = []
        result = []
        idx = 0
        for rv in self.getResources():
            if rv.context.contentType.startswith('text/'):
                if rv.checkState():
                        idx += 1
                        result.append(rv)
                        self.images.append([])
            elif rv.context.contentType.startswith('image/'):
                self.registerDojoLightbox()
                url = self.nodeView.getUrlForTarget(rv.context)
                src = '%s/mediaasset.html?v=small' % url
                fullSrc = '%s/mediaasset.html?v=medium' % url
                img = dict(src=src, fullImageUrl=fullSrc, title=rv.title,
                           description=rv.description, url=url, object=rv)
                self.images[idx].append(img)
            else:
                self.otherResources.append(rv)
        return result

    def getDocumentTypeForResource(self, r):
        for c in r.context.getConcepts([self.defaultPredicate]):
            if c.conceptType == self.documentTypeType:
                return c

    def getOptionsForResource(self, r, name):
        dt = self.getDocumentTypeForResource(r)
        if dt is not None:
            return IOptions(adapted(dt))(name)

    def getTitleForResource(self, r):
        if (IOptions(adapted(r.context.resourceType))('show_title_in_section') or 
                self.getOptionsForResource(r, 'show_title_in_section')):
            return r.title

    def getIconForResource(self, r):
        icon = self.getOptionsForResource(r, 'icon')
        if icon:
            return '/'.join((self.controller.resourceBase, icon[0]))

    def getCssClassForResource(self, r):
        dt = self.getDocumentTypeForResource(r)
        if dt is None:
            return 'textelement'
        css = IOptions(adapted(dt))('cssclass')
        if css:
            return css
        return getName(dt)

    def getMacroForResource(self, r):
        return self.book_macros['default_text']

    def getParentsForResource(self, r):
        for c in r.context.getConcepts([self.defaultPredicate]):
            if (c != self.context and 
                    c.conceptType != self.documentTypeType and
                    self.getViewForObject(c).checkState()):
                yield c


class BookView(Base, ConceptView):

    @Lazy
    def macro(self):
        return book_template.macros['book']


class SectionView(Base, ConceptView):

    @Lazy
    def macro(self):
        return book_template.macros['section']

    @Lazy
    def isPartOfPredicate(self):
        return self.conceptManager['ispartof']

    @Lazy
    def breadcrumbsParent(self):
        for p in self.context.getParents([self.isPartOfPredicate]):
            return self.nodeView.getViewForTarget(p)

    @Lazy
    def showNavigation(self):
        return self.typeOptions.show_navigation

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


class TopicView(Base, ConceptView):

    tabTitle = _(u'title_bookTopicView')

    @Lazy
    def macro(self):
        return book_template.macros['topic']

