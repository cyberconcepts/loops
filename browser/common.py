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
Common base class for loops browser view classes.

$Id$
"""

from cgi import parse_qs, parse_qsl
#import mimetypes   # use more specific assignments from cybertools.text
from datetime import datetime
import re
from time import strptime
from urllib import urlencode
from zope import component
from zope.app.form.browser.interfaces import ITerms
from zope.app.i18n.interfaces import ITranslationDomain
from zope.app.security.interfaces import IAuthentication, IUnauthenticatedPrincipal
from zope.app.pagetemplate import ViewPageTemplateFile
from zope.app.security.interfaces import IUnauthenticatedPrincipal
from zope.app.security.interfaces import PrincipalLookupError
from zope.cachedescriptors.property import Lazy
from zope.dottedname.resolve import resolve
from zope.dublincore.interfaces import IZopeDublinCore
from zope.formlib import form
from zope.formlib.form import FormFields
from zope.formlib.namedtemplate import NamedTemplate
from zope.interface import Interface, implements
from zope.proxy import removeAllProxies
from zope.publisher.browser import applySkin
from zope.publisher.interfaces.browser import IBrowserSkinType, IBrowserView
from zope import schema
from zope.schema.vocabulary import SimpleTerm
from zope.security import canAccess, checkPermission
from zope.security.interfaces import ForbiddenAttribute, Unauthorized
from zope.security.proxy import removeSecurityProxy
from zope.traversing.browser import absoluteURL
from zope.traversing.api import getName, getParent

from cybertools.ajax.dojo import dojoMacroTemplate
from cybertools.browser.view import GenericView
from cybertools.meta.interfaces import IOptions
from cybertools.relation.interfaces import IRelationRegistry
from cybertools.stateful.interfaces import IStateful
from cybertools.text import mimetypes
from cybertools.typology.interfaces import IType, ITypeManager
from loops.common import adapted, baseObject
from loops.config.base import DummyOptions
from loops.i18n.browser import I18NView
from loops.interfaces import IResource, IView, INode, ITypeConcept
from loops.organize.tracking import access
from loops.resource import Resource
from loops.security.common import canAccessObject, canListObject, canWriteObject
from loops.type import ITypeConcept
from loops import util
from loops.util import _
from loops import version
from loops.versioning.interfaces import IVersionable


concept_macros = ViewPageTemplateFile('concept_macros.pt')
conceptMacrosTemplate = concept_macros      #
resource_macros = ViewPageTemplateFile('resource_macros.pt')


class NameField(schema.ASCIILine):

    def _validate(self, value):
        super(NameField, self)._validate(value)


class IAddForm(Interface):

    name = NameField(
            title=_(u'Object name'),
            description=_(u'Name of the object - will be used for addressing the '
                        'object via a URL; should therefore be unique within '
                        'the container and not contain special characters')
        )


class AddForm(form.AddForm):

    form_fields = FormFields(IAddForm)
    template = NamedTemplate('loops.pageform')


class EditForm(form.EditForm):

    template = NamedTemplate('loops.pageform')

    def deleteObjectAction(self):
        return None  # better not to show the delete button at the moment
        parent = getParent(self.context)
        parentUrl = absoluteURL(parent, self.request)
        return parentUrl + '/contents.html'


class BaseView(GenericView, I18NView):

    actions = {}
    icon = None

    def __init__(self, context, request):
        super(BaseView, self).__init__(context, request)
        # TODO: get rid of removeSecurityProxy() call - not yet...
        self.context = removeSecurityProxy(context)
        try:
            if not self.checkPermissions():
                raise Unauthorized(str(self.contextInfo))
        except ForbiddenAttribute:  # ignore when testing
            pass

    def checkPermissions(self):
        return canAccessObject(self.context)

    @Lazy
    def contextInfo(self):
        return dict(view=self, context=getName(self.context))

    @Lazy
    def conceptMacros(self):
        return self.controller.getTemplateMacros('concept', concept_macros)
        #return concept_macros.macros

    concept_macros = conceptMacros

    @Lazy
    def resource_macros(self):
        return self.controller.getTemplateMacros('resource', resource_macros)
        #return resource_macros.macros

    @Lazy
    def name(self):
        return getName(self.context)

    @Lazy
    def principalId(self):
        principal = self.request.principal
        return principal and principal.id or ''

    @Lazy
    def isAnonymous(self):
        return IUnauthenticatedPrincipal.providedBy(self.request.principal)

    def recordAccess(self, viewName, **kw):
        access.record(self.request, principal=self.principalId, view=viewName, **kw)

    @Lazy
    def versions(self):
        return version.versions

    @Lazy
    def longVersions(self):
        return version.longVersions

    def update(self):
        result = super(BaseView, self).update()
        self.checkLanguage()
        return result

    def registerPortlets(self):
        pass

    @Lazy
    def target(self):
        # allow for having a separate object the view acts upon
        return self.context

    @Lazy
    def viewAnnotations(self):
        return self.request.annotations.get('loops.view', {})

    @Lazy
    def node(self):
        return self.viewAnnotations.get('node')

    @Lazy
    def nodeView(self):
        ann = self.request.annotations.get('loops.view', {})
        return self.viewAnnotations.get('nodeView')

    @Lazy
    def params(self):
        result = {}
        paramString = self.request.annotations.get('loops.view', {}).get('params')
        if paramString:
            result = parse_qs(paramString)
            for k, v in result.items():
                if len(v) == 1:
                    v = [x.strip() for x in v[0].split(',')]
                    result[k] = v
        return result

    def setSkin(self, skinName):
        skin = None
        if skinName and IView.providedBy(self.context):
            skin = component.queryUtility(IBrowserSkinType, skinName)
            if skin:
                applySkin(self.request, skin)
        self.skin = skin

    @Lazy
    def modifiedRaw(self):
        """ get date/time of last modification
        """
        d = getattr(self.adapted, 'modified', None)
        if not d:
            dc = IZopeDublinCore(self.context)
            d = dc.modified or dc.created
        if isinstance(d, str):
            d = datetime(*(strptime(d, '%Y-%m-%dT%H:%M')[:6]))
        return d

    @Lazy
    def modified(self):
        d = self.modifiedRaw
        return d and d.strftime('%Y-%m-%d %H:%M') or ''

    @Lazy
    def creators(self):
        # TODO: use an IAuthorInfo (or similar) adapter
        creators = getattr(self.adapted, 'authors', None) or []
        if not creators:
            cr = IZopeDublinCore(self.context).creators or []
            pau = component.getUtility(IAuthentication)
            for c in cr:
                try:
                    principal = pau.getPrincipal(c)
                    creators.append(principal.title)
                except PrincipalLookupError:
                    creators.append(c)
        return ', '.join(creators)

    @Lazy
    def loopsRoot(self):
        return self.context.getLoopsRoot()

    @Lazy
    def conceptManager(self):
        return self.loopsRoot.getConceptManager()

    @Lazy
    def resourceManager(self):
        return self.loopsRoot.getResourceManager()

    @Lazy
    def typePredicate(self):
        return self.conceptManager.getTypePredicate()

    @Lazy
    def defaultPredicate(self):
        return self.conceptManager.getDefaultPredicate()

    @Lazy
    def isPartOfPredicate(self):
        return self.conceptManager.get('ispartof')

    @Lazy
    def url(self):
        return absoluteURL(self.context, self.request)

    @Lazy
    def rootUrl(self):
        return absoluteURL(self.loopsRoot, self.request)

    @Lazy
    def view(self):
        return self

    @Lazy
    def token(self):
        return self.loopsRoot.getLoopsUri(self.context)

    @Lazy
    def adapted(self):
        return adapted(self.context, self.languageInfo)

    @Lazy
    def baseObject(self):
        return baseObject(self.context)

    @Lazy
    def title(self):
        return self.adapted.title or getName(self.context)

    @Lazy
    def description(self):
        return self.adapted.description

    @Lazy
    def additionalInfos(self):
        return []

    @Lazy
    def dublincore(self):
        zdc = IZopeDublinCore(self.context)
        zdc.languageInfo = self.languageInfo
        return zdc

    @Lazy
    def dcTitle(self):
        return self.dublincore.title or self.title

    @Lazy
    def dcDescription(self):
        return self.dublincore.description or self.description

    @Lazy
    def headTitle(self):
        return self.dcTitle

    @Lazy
    def value(self):
        return self.context

    @Lazy
    def uniqueId(self):
        return util.getUidForObject(self.context)

    # type stuff

    @Lazy
    def type(self):
        return IType(self.baseObject)

    @Lazy
    def typeProvider(self):
        return self.type.typeProvider

    @Lazy
    def typeInterface(self):
        return self.type.typeInterface

    @Lazy
    def typeAdapter(self):
        ifc = self.typeInterface
        if ifc is not None:
            return ifc(self.context)

    @Lazy
    def typeTitle(self):
        return self.type.title

    @Lazy
    def longTypeTitle(self):
        ct = getattr(self.context, 'contentType', None)
        if ct:
            ext = mimetypes.extensions.get(ct)
            #ext = mimetypes.guess_extension(ct)
            if ext:
                #return '%s (%s)' % (t, ext.upper())
                return ext.upper()  #.lstrip('.')
        return self.typeTitle

    @Lazy
    def typeUrl(self):
        provider = self.typeProvider
        if provider is not None:
            return absoluteURL(provider, self.request)
        return None

    def viewIterator(self, objs):
        request = self.request
        for o in objs:
            view = component.queryMultiAdapter((o, request), name='index.html')
            #if view is None:
            #    view = component.queryMultiAdapter((o, request), IBrowserView)
            if view is None:
                view = BaseView(o, request)
            yield view

    def renderText(self, text, contentType):
        text = util.toUnicode(text)
        typeKey = util.renderingFactories.get(contentType, None)
        if typeKey is None:
            if contentType == u'text/html':
                return text
            return u'<pre>%s</pre>' % util.html_quote(text)
        source = component.createObject(typeKey, text)
        view = component.getMultiAdapter((removeAllProxies(source), self.request))
        return view.render()

    def renderDescription(self, text=None):
        if text is None:
            text = self.description
        htmlPattern = re.compile(r'<(.+)>.+</\1>')
        if htmlPattern.search(text):
            return text
        return self.renderText(text, 'text/restructured')

    @Lazy
    def renderedDescription(self):
        return self.renderDescription()

    # type listings

    def listTypes(self, include=None, exclude=None, sortOn='title'):
        types = [dict(token=t.token, title=t.title)
                    for t in ITypeManager(self.context).listTypes(include, exclude)]
        #if sortOn:
        #    types.sort(key=lambda x: x[sortOn])
        return types

    def getTypesVocabulary(self, include=None):
        return util.KeywordVocabulary(self.listTypes(include, ('hidden',)))

    def resourceTypes(self):
        return util.KeywordVocabulary(self.listTypes(('resource',), ('hidden',)))
            #if t.factory == Resource]) # ? if necessary -> type.qualifiers

    def conceptTypes(self):
        return util.KeywordVocabulary(self.listTypes(('concept',), ('hidden',)))

    def listTypesForSearch(self, include=None, exclude=None, sortOn='title'):
        types = [dict(token=t.tokenForSearch, title=t.title)
                    for t in ITypeManager(self.context).listTypes(include, exclude)]
        if sortOn:
            types.sort(key=lambda x: x[sortOn])
        return types

    def typesForSearch(self):
        general = [('loops:resource:*', 'Any Resource'),
                   ('loops:concept:*', 'Any Concept'),]
        return util.KeywordVocabulary(general
                        + self.listTypesForSearch(exclude=('system', 'hidden',))
                        + [('loops:*', 'Any')])

    def conceptTypesForSearch(self):
        general = [('loops:concept:*', 'Any Concept'),]
        return util.KeywordVocabulary(general
                        + self.listTypesForSearch(('concept',),
                                                  ('hidden',),))
                                                  #('system', 'hidden',),))

    def resourceTypesForSearch(self):
        general = [('loops:resource:*', 'Any Resource'),]
        return util.KeywordVocabulary(general
                        + self.listTypesForSearch(('resource',),
                                                  ('system', 'hidden',),))

    def isPartOnlyResource(self, obj):
        if not IResource.providedBy(obj):
            return False
        isPart = False
        for r in obj.getConceptRelations():
            if r.predicate == self.isPartOfPredicate:
                isPart = True
            elif r.predicate != self.typePredicate:
                return False
        return isPart

    # options/settings

    @Lazy
    def options(self):
        if ITypeConcept.providedBy(self.adapted):
            return DummyOptions()
        return component.queryAdapter(self.adapted, IOptions) or DummyOptions()

    @Lazy
    def globalOptions(self):
        return IOptions(self.loopsRoot)

    @Lazy
    def typeOptions(self):
        return IOptions(adapted(self.typeProvider))

    def getPredicateOptions(self, relation):
        return IOptions(adapted(relation.predicate), None) or DummyOptions()

    # versioning

    @Lazy
    def versionable(self):
        return IVersionable(self.target, None)

    @Lazy
    def useVersioning(self):
        if self.globalOptions('useVersioning'):
            return True
        options = getattr(self.controller, 'options', None)
        if options:
            return 'useVersioning' in options.value

    @Lazy
    def showVersions(self):
        permissions = self.globalOptions('showVersionsPermissions')
        if permissions:
            for p in permissions:
                if checkPermission(p, self.target):
                    return True
            else:
                return False
        return True

    @Lazy
    def versionLevels(self):
        if self.versionable is not None:
            return reversed([dict(token=idx, label=label)
                        for idx, label in enumerate(self.versionable.versionLevels)])
        return []

    @Lazy
    def versionId(self):
        versionable = IVersionable(self.target, None)
        return versionable and versionable.versionId or ''

    @Lazy
    def currentVersionId(self):
        versionable = IVersionable(self.target, None)
        return versionable and versionable.currentVersion.versionId or ''

    @Lazy
    def hasVersions(self):
        versionable = IVersionable(self.target, None)
        return versionable and len(versionable.versions) > 1 or False

    @Lazy
    def versionInfo(self):
        if not self.useVersioning:
            return None
        target = self.target
        versionable = IVersionable(target, None)
        if versionable is None:
            return ''
        versionId = versionable.versionId
        td = component.getUtility(ITranslationDomain, _._domain)
        current = ((versionable.currentVersion == target)
                   and td.translate(_(u'current'), context=self.request)
                   or u'')
        released = ((versionable.releasedVersion == target)
                    and td.translate(_(u'released'), context=self.request)
                    or u'')
        if not current and not released:
            return versionId
        addInfo = u', '.join(e for e in (current, released) if e)
        return u'%s (%s)' % (versionId, addInfo)

    # states

    @Lazy
    def states(self):
        result = []
        if not checkPermission('loops.ManageSite', self.context):
            # TODO: replace by more sensible permission
            return result
        if IResource.providedBy(self.target):
            statesDefs = self.globalOptions('organize.stateful.resource', ())
        else:
            statesDefs = self.globalOptions('organize.stateful.concept', ())
        for std in statesDefs:
            stf = component.getAdapter(self.target, IStateful, name=std)
            result.append(stf)
        return result

    # controlling actions and editing

    @Lazy
    def editable(self):
        return canWriteObject(self.context)

    def getActions(self, category='object', page=None, target=None):
        """ Return a list of actions that provide the view and edit actions
            available for the context object.
        """
        actions = []
        if category in self.actions:
            actions.extend(self.actions[category](self, page=page, target=target))
        return actions

    def getAdditionalActions(self, category='object', page=None, target=None):
        """ Provide additional actions; override by subclass.
        """
        return []

    @Lazy
    def showObjectActions(self):
        return not IUnauthenticatedPrincipal.providedBy(self.request.principal)

    def checkAction(self, name, category, target):
        if name in ('create_resource',):
            return not self.globalOptions('hideCreateResource')
        return True

    @Lazy
    def canAccessRestricted(self):
        return checkPermission('loops.ViewRestricted', self.context)

    def openEditWindow(self, viewName='edit.html'):
        if self.editable:
            if checkPermission('loops.ManageSite', self.context):
                return "openEditWindow('%s/@@%s')" % (self.url, viewName)
        return ''

    @Lazy
    def xeditable(self):
        ct = getattr(self.context, 'contentType', '')
        if not ct or ct == 'application/pdf':
            return False
        if ct.startswith('text/') and ct != 'text/rtf':
            return checkPermission('loops.ManageSite', self.context)
        return canWriteObject(self.context)

    @Lazy
    def inlineEditingActive(self):
        # this may depend on system and user settings...
        return True

    @Lazy
    def conceptMapEditorUrl(self):
        return (checkPermission('loops.xmlrpc.ManageConcepts', self.context)
                    and self.rootUrl + '/swf.html'
                    or None)

    inlineEditable = False

    # work items
    @Lazy
    def workItems(self):
        return []

    # comments

    @Lazy
    def comments(self):
        return []

    # dojo stuff

    def inlineEdit(self, id):
        self.registerDojo()
        return 'return inlineEdit("%s", "")' % id

    def registerDojo(self):
        cm = self.controller.macros
        cm.register('js', 'dojo.js', template=dojoMacroTemplate, name='main',
                    position=0,
                    djConfig='parseOnLoad: true, usePlainJson: true, '
                             #'isDebug: true, '
                             'locale: "%s"' % self.languageInfo.language)
        jsCall = ('dojo.require("dojo.parser"); '
                  'dojo.registerModulePath("jocy", "/@@/cybertools.jocy"); '
                  'dojo.require("jocy.data");')
        cm.register('js-execute', 'dojo_registration', jsCall=jsCall)
        cm.register('css', identifier='Lightbox.css', position=0,
                    resourceName='ajax.dojo/dojox/image/resources/Lightbox.css',
                    media='all')
        cm.register('css', identifier='tundra.css', position=0,
                    resourceName='ajax.dojo/dijit/themes/tundra/tundra.css',
                    media='all')
        #cm.register('css', identifier='dojo.css', position=1,
        #            resourceName='ajax.dojo/dojo/resources/dojo.css', media='all')

    def registerDojoDialog(self):
        self.registerDojo()
        jsCall = 'dojo.require("dijit.Dialog")'
        self.controller.macros.register('js-execute', jsCall, jsCall=jsCall)

    def registerDojoTooltipDialog(self):
        self.registerDojo()
        jsCall = ('dojo.require("dijit.Dialog");'
                  'dojo.require("dijit.form.Button");')
        self.controller.macros.register('js-execute', jsCall, jsCall=jsCall)

    def registerDojoDateWidget(self):
        self.registerDojo()
        jsCall = ('dojo.require("dijit.form.DateTextBox"); '
                  'dojo.require("dijit.form.TimeTextBox");')
        self.controller.macros.register('js-execute', jsCall, jsCall=jsCall)

    def registerDojoTextWidget(self):
        self.registerDojo()
        jsCall = 'dojo.require("dijit.form.ValidationTextBox");'
        self.controller.macros.register('js-execute', jsCall, jsCall=jsCall)

    def registerDojoTextarea(self):
        self.registerDojo()
        jsCall = 'dojo.require("dijit.form.SimpleTextarea");'
        self.controller.macros.register('js-execute', jsCall, jsCall=jsCall)

    def registerDojoNumberWidget(self):
        self.registerDojo()
        jsCall = 'dojo.require("dijit.form.NumberTextBox");'
        self.controller.macros.register('js-execute', jsCall, jsCall=jsCall)

    def registerDojoEditor(self):
        self.registerDojo()
        jsCall = 'dojo.require("dijit.Editor");'
        self.controller.macros.register('js-execute', jsCall, jsCall=jsCall)
        jsCall = 'dojo.require("dijit._editor.plugins.LinkDialog");'
        self.controller.macros.register('js-execute', jsCall, jsCall=jsCall)
        jsCall = 'dojo.require("dijit._editor.plugins.ViewSource")'
        self.controller.macros.register('js-execute', jsCall, jsCall=jsCall)

    def registerDojoLightbox(self):
        self.registerDojo()
        jsCall = 'dojo.require("dojox.image.Lightbox");'
        self.controller.macros.register('js-execute', jsCall, jsCall=jsCall)

    def registerDojoFormAll(self):
        self.registerDojo()
        cm = self.controller.macros
        jsCall = ('dojo.require("dijit.form.Form"); '
                  'dojo.require("dijit.form.DateTextBox"); '
                  'dojo.require("dijit.form.TimeTextBox"); '
                  'dojo.require("dijit.form.SimpleTextarea"); '
                  'dojo.require("dijit.form.FilteringSelect"); '
                  'dojo.require("dojox.data.QueryReadStore"); ')
        cm.register('js-execute', 'dojo.form.all', jsCall=jsCall)

    def registerDojoFormAllGrid(self):
        self.registerDojoFormAll()
        cm = self.controller.macros
        jsCall = ('dojo.require("dijit.layout.TabContainer"); '
                  'dojo.require("dojox.grid.DataGrid"); '
                  'dojo.require("dojo.data.ItemFileWriteStore"); ')
        cm.register('js-execute', 'dojo.form.grid', jsCall=jsCall)
        cm.register('css', identifier='dojox.grid.css', position=0,
                    resourceName='ajax.dojo/dojox/grid/resources/Grid.css', media='all')
        cm.register('css', identifier='dojox.grid_tundra.css', position=0,
                    resourceName='ajax.dojo/dojox/grid/resources/tundraGrid.css',
                    media='all')


class LoggedIn(object):

    messages = dict(success=_(u'You have been logged in.'),
                    nosuccess=_(u'Login not successful.'),
                    error=_(u'Try again later.'))

    def __call__(self):
        code = 'success'
        if IUnauthenticatedPrincipal.providedBy(self.request.principal):
            code = 'nosuccess'
        info = self.request.form.get('message')
        if info == 'error' and code == 'nosuccess':
            code = 'error'
        message = self.messages[code]
        return self.request.response.redirect(self.nextUrl(message, code))
	
    def nextUrl(self, message, code):
        camefrom = self.request.form.get('camefrom', '').strip('?')
        url = camefrom or self.request.URL[-1]
        params = []
        if '?' in url:
            url, qs = url.split('?', 1)
            params = parse_qsl(qs)
        params = [(k, v) for k, v in params if k != 'loops.messages.top:record']
        params.append(('loops.messages.top:record', message.encode('UTF-8')))
        return '%s?%s' % (url, urlencode(params))

# vocabulary stuff

class SimpleTerms(object):
    """ Provide the ITerms interface, e.g. for usage in selection
        lists.
    """

    implements(ITerms)

    def __init__(self, source, request):
        # the source parameter is a list of tuples (token, title).
        self.source = source
        self.terms = dict(source)

    def getTerm(self, value):
        token, title = value
        return SimpleTerm(token, token, title)

    def getValue(self, token):
        return (token, self.terms[token])


class LoopsTerms(object):
    """ Provide the ITerms interface, e.g. for usage in selection
        lists.
    """

    implements(ITerms)

    def __init__(self, source, request):
        # the source parameter is a view or adapter of a real context object:
        self.source = source
        self.context = source.context
        self.request = request

    @Lazy
    def loopsRoot(self):
        return self.context.getLoopsRoot()

    def getTerm(self, value):
        #if value is None:
        #    return SimpleTerm(None, '', u'not assigned')
        title = value.title or getName(value)
        token = self.loopsRoot.getLoopsUri(value)
        return SimpleTerm(value, token, title)

    def getValue(self, token):
        return self.loopsRoot.loopsTraverse(token)


class InterfaceTerms(object):
    """ Provide the ITerms interface for source list of interfaces.
    """

    implements(ITerms)

    def __init__(self, source, request):
        self.source = source
        self.request = request

    def getTerm(self, value):
        token = '.'.join((value.__module__, value.__name__))
        return SimpleTerm(value, token, token)

    def getValue(self, token):
        return resolve(token)


