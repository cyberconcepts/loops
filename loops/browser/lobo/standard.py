# loops.browser.lobo.standard

""" View classes for lobo (blueprint-based) layouts.
"""

from urllib.parse import parse_qs
from zope import interface, component
from zope.app.pagetemplate import ViewPageTemplateFile
from zope.cachedescriptors.property import Lazy

from cybertools.typology.interfaces import IType
from loops.browser.concept import ConceptView as BaseConceptView
from loops.browser.concept import ConceptRelationView as BaseConceptRelationView
from loops.browser.resource import ResourceView as BaseResourceView
from loops.common import adapted, baseObject


standard_template = ViewPageTemplateFile('standard.pt')


class Base(BaseConceptView):

    template = standard_template
    templateName = 'lobo.standard'
    macroName = None

    #@Lazy      
    # better implementation in BaseView: 
    #       splits comma-separated list of values automatically
    #def params(self):
    #    ann = self.request.annotations.get('loops.view', {})
    #    return parse_qs(ann.get('params') or '')


class ConceptView(BaseConceptView):

    idx = 0

    def __init__(self, context, request):
        super(ConceptView, self).__init__(baseObject(context), request)

    @Lazy
    def resources(self):
        return self.getResources()

    @Lazy
    def representingResources(self):
        pred = self.representationPredicate
        if pred is None:
            return {}
        return self.getResources([pred])

    def getResources(self, predicates=None):
        result = dict(texts=[], images=[], files=[])
        if predicates is None:
            predicates = [self.defaultPredicate]
        for r in self.context.getResources(predicates):
            if r.contentType.startswith('text/'):
                result['texts'].append(r)
            if r.contentType.startswith('image/'):
                result['images'].append(r)
            else:
                result['files'].append(r)
        return result

    @Lazy
    def images(self):
        for r in self.resources['images']:
            yield r

    @Lazy
    def representationPredicate(self):
        return self.conceptManager.get('represents')

    # properties from base class: title, description, renderedDescription

    @Lazy
    def renderedText(self):
        for r in self.resources['texts']:
            return self.renderText(r.data, r.contentType)

    @Lazy
    def textDescription(self):
        for r in self.resources['texts']:
            return r.description

    @Lazy
    def renderedTextDescription(self):
        if self.textDescription is None:
            return u''
        return self.renderDescription(self.textDescription)

    @Lazy
    def textRepresentation(self):
        for r in self.representingResources.get('texts', []):
            return self.renderText(r.data, r.contentType)
        return self.renderedDescription

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
        return 'height: %s' % self.parentView.height

    @Lazy
    def img(self):
        self.registerDojoLightbox() # also provides access to info popup
        for r in self.parentView.parent.images:
            # fetch from iterator on layout object: avoid duplicates
            url = self.nodeView.getUrlForTarget(r)
            src = ('%s/mediaasset.html?v=%s' % (url, self.parentView.imageSize))
            fullSrc = ('%s/mediaasset.html?v=%s' % (url, self.parentView.fullImageSize))
            adImg = adapted(r)
            showInfo = adImg.showInfo and adImg.metaInfo
            return dict(src=src, fullImageUrl=fullSrc, title=r.title,
                        description=r.description,
                        url=url, cssClass=self.parentView.imageCssClass,
                        showInfo=showInfo)


class Layout(Base, ConceptView):

    macroName = 'layout'
    partPrefix = 'lobo_'
    defaultParts = ('h1', 'g3',)


class BasePart(Base):

    imageSize = 'small'
    fullImageSize = 'medium'
    imageCssClass = ''
    height = 260
    gridPattern = []
    showImage = True

    @Lazy
    def childPredicates(self):
        preds = [self.defaultPredicate]
        for name in ['ispartof', 'hasoverview']:
            pred = self.conceptManager.get(name)
            if pred is not None:
                preds.append(pred)
        return preds

    def getChildren(self):
        subtypeNames =  (self.params.get('subtypes') or [])
        subtypes = [self.conceptManager[st] for st in subtypeNames if st]
        result = []
        childRels = self.context.getChildRelations(self.childPredicates)
        if subtypes:
            childRels = [r for r in childRels
                           if r.second.conceptType in subtypes]
        for idx, r in enumerate(childRels):
            result.append(ConceptRelationView(r, self.request,
                                contextIsSecond=True, parent=self, idx=idx))
        return result

    def getView(self):
        view = component.getMultiAdapter((self.adapted, self.request),
                                         name='lobo_cell')
        view.parentView = self
        return view

    def getImages(self):
        result = []
        for idx, img in enumerate(self.parent.images):
            result.append(ResourceView(img, self.request, parent=self, idx=idx))
        return result


class Grid3(BasePart):

    macroName = 'grid'
    imageSize = 'small'
    height = 'auto; padding-bottom: 10px'
    gridPattern = ['span-2 clear', 'span-2', 'span-2 last']


class ListThumbs(BasePart):

    macroName = 'list'
    imageSize = 'minithumb'
    gridPattern = [['span-1 clear', 'span-5 last']]


class List1(BasePart):

    macroName = 'list'
    imageSize = 'small'
    gridPattern = [['span-2 clear', 'span-4 last']]


class List2(BasePart):

    macroName = 'list'
    imageSize = 'medium'
    gridPattern = [['span-4 clear', 'span-2 last']]


class List3(BasePart):

    macroName = 'list3'
    imageSize = 'large'
    gridPattern = [['span-6 clear']]


class Header0(BasePart):

    macroName = 'header'
    cssClass = ['span-6 last', 'clear']
    showImage = False
    cssClass = ['', 'span-6 last', 'clear']


class HeaderThumbs(BasePart):

    macroName = 'header'
    imageSize = 'minithumb'
    cssClass = ['span-1', 'span-5 last', 'clear']


class Header1(BasePart):

    macroName = 'header'
    imageSize = 'small'
    cssClass = ['span-2', 'span-4 last', 'clear']


class Header2(BasePart):

    macroName = 'header'
    imageSize = 'medium'
    cssClass = ['span-4', 'span-2 last', 'clear']


class Header3(BasePart):

    macroName = 'header'
    imageSize = 'large'
    cssClass = ['span-6 last', 'clear', 'clear']


# resource parts


class ImageGrid3(BasePart):

    macroName = 'imagegrid'
    imageSize = 'small'
    height = 'auto; padding-bottom: 10px'
    gridPattern = ['span-2 clear', 'span-2', 'span-2 last']


# relation views, used for cells (components) of lists and grids

class ConceptRelationView(BaseConceptRelationView, ConceptView):

    def __init__(self, relation, request, contextIsSecond=False,
                 parent=None, idx=0):
        BaseConceptRelationView.__init__(self, relation, request, contextIsSecond)
        self.parentView = parent
        self.idx = idx

    @Lazy
    def img(self):
        self.registerDojoLightbox() # also provides access to info popup
        for r in self.images:
            # fetch from iterator on layout object: avoid duplicates
            url = self.nodeView.getUrlForTarget(r)
            src = ('%s/mediaasset.html?v=%s' % (url, self.parentView.imageSize))
            fullSrc = ('%s/mediaasset.html?v=%s' % (url, self.parentView.fullImageSize))
            adImg = adapted(r)
            showInfo = adImg.showInfo and adImg.metaInfo
            return dict(src=src, fullImageUrl=fullSrc, title=r.title,
                        description=r.description,
                        url=url, cssClass=self.parentView.imageCssClass,
                        showInfo=showInfo)


class ResourceView(BaseResourceView):

    def __init__(self, resource, request, parent=None, idx=0):
        BaseResourceView.__init__(self, resource, request)
        self.parentView = parent
        self.idx = idx

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
        return 'height: %s' % self.parentView.height

    @Lazy
    def img(self):
        self.registerDojoLightbox() # also provides access to info popup
        url = self.nodeView.getUrlForTarget(self.context)
        src = ('%s/mediaasset.html?v=%s' % (url, self.parentView.imageSize))
        fullSrc = ('%s/mediaasset.html?v=%s' % (url, self.parentView.fullImageSize))
        adImg = adapted(self.context)
        showInfo = adImg.showInfo and adImg.metaInfo
        return dict(src=src, fullImageUrl=fullSrc, title=self.context.title,
                    description=self.context.description,
                    url=url, cssClass=self.parentView.imageCssClass,
                    showInfo=showInfo)

