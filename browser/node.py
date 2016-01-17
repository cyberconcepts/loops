#
#  Copyright (c) 2015 Helmut Merz helmutm@cy55.de
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
View class for Node objects.
"""

from urlparse import urlparse, urlunparse
from zope import component, interface, schema
from zope.cachedescriptors.property import Lazy
from zope.annotation.interfaces import IAnnotations
from zope.app.catalog.interfaces import ICatalog
from zope.app.container.browser.contents import JustContents
from zope.app.container.browser.adding import Adding
from zope.app.container.traversal import ItemTraverser
from zope.app.pagetemplate import ViewPageTemplateFile
from zope.app.security.interfaces import IUnauthenticatedPrincipal
from zope.dottedname.resolve import resolve
from zope.event import notify
from zope.lifecycleevent import ObjectCreatedEvent, ObjectModifiedEvent
from zope.lifecycleevent import Attributes
from zope.formlib.form import Form, FormFields
from zope.proxy import removeAllProxies
from zope.publisher.defaultview import getDefaultViewName
from zope.security import canAccess, canWrite, checkPermission
from zope.security.proxy import removeSecurityProxy
from zope.traversing.api import getParent, getParents, getPath
from zope.traversing.browser import absoluteURL

from cybertools.ajax import innerHtml
from cybertools.browser import configurator
from cybertools.browser.action import Action
from cybertools.browser.view import GenericView
from cybertools.stateful.interfaces import IStateful
from cybertools.typology.interfaces import IType, ITypeManager
from cybertools.util.jeep import Jeep
from cybertools.xedit.browser import ExternalEditorView
from loops.browser.action import actions, DialogAction
from loops.browser.common import BaseView
from loops.browser.concept import ConceptView
from loops.common import adapted, AdapterBase, baseObject
from loops.i18n.browser import i18n_macros, LanguageInfo
from loops.interfaces import IConcept, IResource, IDocument, IMediaAsset, INode
from loops.interfaces import IViewConfiguratorSchema
from loops.organize.interfaces import IPresence
from loops.organize.tracking import access
from loops.resource import MediaAsset
from loops.security.common import canWriteObject
from loops import util
from loops.util import _
from loops.versioning.util import getVersion


node_macros = ViewPageTemplateFile('node_macros.pt')
info_macros = ViewPageTemplateFile('info.pt')
calendar_macros = ViewPageTemplateFile('calendar.pt')


class NodeView(BaseView):

    _itemNum = 0
    template = node_macros
    nextUrl = None
    setupTarget = True

    def __init__(self, context, request):
        super(NodeView, self).__init__(context, request)
        self.viewAnnotations.setdefault('nodeView', self)
        self.viewAnnotations.setdefault('node', self.context)
        viewConfig = getViewConfiguration(context, request)
        self.setSkin(viewConfig.get('skinName'))

    def __call__(self, *args, **kw):
        tv = self.viewAnnotations.get('targetView')
        if tv is not None:
            if tv.isToplevel:
                return tv(*args, **kw)
        if self.controller is not None:
            self.controller.setMainPage()
        return super(NodeView, self).__call__(*args, **kw)

    @Lazy
    def macro(self):
        return self.template.macros['content']

    @Lazy
    def subparts(self):
        def getParts(n):
            t = n.targetObjectView
            if t is None:
                return []
            return t.subparts
        parts = getParts(self)
        for n in self.textItems:
            parts.extend(getParts(n))
        return parts

    def update(self):
        result = super(NodeView, self).update()
        self.recordAccess()
        return result

    @Lazy
    def title(self):
        return self.context.title or getName(self.context)

    def breadcrumbs(self):
        if not self.globalOptions('showBreadcrumbs'):
            return []
        menu = self.menu
        data = [dict(label=menu.title, url=menu.url)]
        menuItem = self.getNearestMenuItem(all=True)
        if menuItem != menu.context:
            data.append(dict(label=menuItem.title,
                             url=absoluteURL(menuItem, self.request)))
            for p in getParents(menuItem):
                if p == menu.context:
                    break
                data.insert(1, dict(label=p.title,
                                    url=absoluteURL(p, self.request)))
        if self.virtualTarget:
            data.extend(self.virtualTarget.breadcrumbs())
        if data and not '?' in data[-1]['url']:
            if self.urlParamString:
                data[-1]['url'] += self.urlParamString
        return data

    def viewModes(self):
        if self.virtualTarget:
            return self.virtualTarget.viewModes()
        return Jeep()

    def recordAccess(self, viewName=''):
        target = self.virtualTargetObject
        targetUid = target is not None and util.getUidForObject(target) or ''
        access.record(self.request, principal=self.principalId,
                                    node=self.uniqueId,
                                    target=targetUid,
                                    view=viewName)

    def setupController(self):
        cm = self.controller.macros
        cm.register('css', identifier='loops.css', resourceName='loops.css',
                    media='all', priority=60)
        cm.register('js', 'loops.js', resourceName='loops.js', priority=60)
        cm.register('top_actions', 'top_actions', name='multi_actions',
                    subMacros=[node_macros.macros['page_actions'],
                               i18n_macros.macros['language_switch']])
        if self.globalOptions('expert.quicksearch'):
            from loops.expert.browser.search import search_template
            cm.register('top_actions', 'top_quicksearch', name='multi_actions',
                        subMacros=[search_template.macros['quicksearch']],
                        priority=20)
        cm.register('portlet_left', 'navigation', title='Navigation',
                    subMacro=node_macros.macros['menu'])
        if canWriteObject(self.context) or (
                # TODO: is this useful in any case?
                self.virtualTargetObject is not None and
                    canWriteObject(self.virtualTargetObject)):
            # check if there are any available actions;
            # store list of actions in macro object (evaluate only once)
            actions = [act for act in self.getAllowedActions('portlet',
                                            target=self.virtualTarget)
                            if act.condition]
            if actions:
                cm.register('portlet_right', 'actions', title=_(u'Actions'),
                            subMacro=node_macros.macros['actions'],
                            priority=100, actions=actions)
        if self.isAnonymous and self.globalOptions('provideLogin'):
            cm.register('portlet_right', 'login', title=_(u'Not logged in'),
                        subMacro=node_macros.macros['login'],
                        icon='cybertools.icons/user.png',
                        priority=10)
        if not self.isAnonymous:
            mi = self.controller.memberInfo
            title = mi.title.value or _(u'Personal Informations')
            url=None
            obj = mi.get('object')
            if obj is not None:
                query = self.conceptManager.get('personal_info')
                if query is None:
                    #url = self.url + '/personal_info.html'
                    url = self.getUrlForTarget(obj.value)
                else:
                    url = self.getUrlForTarget(query)
            cm.register('portlet_right', 'personal', title=title,
                        subMacro=node_macros.macros['personal'],
                        icon='cybertools.icons/user.png',
                        url=url,
                        priority=10)
            if self.globalOptions('organize.showPresence'):
                cm.register('portlet_right', 'presence', title=_(u'Presence'),
                            subMacro=node_macros.macros['presence'],
                            icon='cybertools.icons/group.png',
                            priority=11)
        if self.globalOptions('organize.showCalendar'):
            cm.register('portlet_left', 'calendar', title=_(u'Calendar'),
                        subMacro=calendar_macros.macros['main'],
                        priority=90)
        # force early portlet registrations by target by setting up target view
        if self.virtualTarget is not None:
            std = self.virtualTarget.typeOptions('portlet_states')
            if std:
                from loops.organize.stateful.browser import registerStatesPortlet
                registerStatesPortlet(self.controller, self.virtualTarget, std)

    @Lazy
    def usersPresent(self):
        presence = component.getUtility(IPresence)
        presence.update(self.request.principal.id)
        data = presence.getPresentUsers(self.context)
        for u in data:
            if IConcept.providedBy(u):
                url = self.getUrlForTarget(u)
            else:
                url = None
            yield dict(title=u.title, url=url)

    @Lazy
    def view(self):
        name = self.request.get('loops.viewName', '') or self.context.viewName
        if name and '?' in name:
            name, params = name.split('?', 1)
            ann = self.viewAnnotations
            ann['params'] = params
        if name:
            adapter = component.queryMultiAdapter(
                            (self.context, self.request), name=name)
            if adapter is not None:
                return adapter
        return self

    @Lazy
    def item(self):
        tv = self.viewAnnotations.get('targetView')
        if tv is not None:
            return tv
        viewName = self.request.get('loops.viewName') or ''
        # was there a .target... element in the URL?
        #target = self.virtualTargetObject  # ignores page even for direktly assignd target
        target = self.viewAnnotations.get('target')
        if target is not None:
            basicView = component.getMultiAdapter((target, self.request), name=viewName)
            # xxx: obsolete when self.targetObject is virtual target:
            if hasattr(basicView, 'view'):
                #basicView.setupController()
                return basicView.view
        return self.page

    @Lazy
    def targetItem(self):
        tv = self.viewAnnotations.get('targetView')
        if tv is not None:
            return tv
        viewName = self.request.get('loops.viewName') or ''
        target = self.virtualTargetObject
        if target is not None:
            basicView = component.getMultiAdapter((target, self.request), name=viewName)
            # xxx: obsolete when self.targetObject is virtual target:
            if hasattr(basicView, 'view'):
                #basicView.setupController()
                return basicView.view
        return self.page

    @Lazy
    def page(self):
        page = self.context.getPage()
        return page is not None and NodeView(page, self.request).view or None

    @Lazy
    def textItems(self):
        return [NodeView(child, self.request)
                    for child in self.context.getTextItems()]

    @Lazy
    def pageItems(self):
        return [NodeView(child, self.request)
                    for child in self.context.getPageItems()]

    @property
    def itemNum(self):
        self._itemNum += 1
        return self._itemNum

    @Lazy
    def nodeType(self):
        return self.context.nodeType

    def render(self, text=None):
        if text is None:
            text = self.context.body
        if not text:
            return u''
        if text.startswith('<'):  # seems to be HTML
            return text
        source = component.createObject(self.context.contentType, text)
        view = component.getMultiAdapter((removeAllProxies(source), self.request))
        return view.render()

    @Lazy
    def targetObject(self):
        # xxx: use virtualTargetObject
        #return self.virtualTargetObject
        target = self.context.target
        if target is not None:
            target = getVersion(target, self.request)
        return target

    @Lazy
    def targetObjectView(self):
        obj = self.targetObject
        if obj is not None:
            basicView = component.getMultiAdapter((obj, self.request))
            basicView._viewName = self.context.viewName
            if self.context.nodeType != 'text':
                basicView.setupController()
            return basicView.view

    @Lazy
    def targetUrl(self):
        t = self.targetObjectView
        if t is not None:
            return self.makeTargetUrl(self.url, t.uniqueId, t.title)
        return ''

    def renderTarget(self):
        target = self.targetObjectView
        return target is not None and target.render() or u''

    @Lazy
    def body(self):
        return self.render()

    @Lazy
    def bodyMacro(self):
        # TODO: replace by something like: return self.target.macroName
        target = self.targetObject
        if (target is None or IDocument.providedBy(target)
                or (IResource.providedBy(target) and
                    target.contentType.startswith('text/'))):
            return 'textbody'
        if IConcept.providedBy(target):
            return 'conceptbody'
        if IResource.providedBy(target) and target.contentType.startswith('image/'):
            return 'imagebody'
        return 'filebody'

    @Lazy
    def editable(self):
        return canWrite(self.context, 'body')

    # menu stuff

    @Lazy
    def menuObject(self):
        return self.context.getMenu()

    @Lazy
    def menu(self):
        menu = self.menuObject
        return menu is not None and NodeView(menu, self.request) or None

    @Lazy
    def topMenu(self):
        menu = self.menuObject
        parentMenu = None
        while menu is not None:
            parent = getParent(menu)
            if INode.providedBy(parent):
                parentMenu = parent.getMenu()
            if parentMenu is None or parentMenu is menu:
                return NodeView(menu, self.request)
            menu = parentMenu
        return menu is not None and NodeView(menu, self.request) or None

    @Lazy
    def headTitle(self):
        parts = []
        menuObject = self.menuObject
        if menuObject is not None and (menuObject != self.context or
                                       self.virtualTarget):
            parts.append(super(NodeView, self.menu).headTitle)
        if self.virtualTarget:
            ht = self.virtualTarget.headTitle
            if ht not in parts:
                parts.append(ht)
        if len(parts) < 2:
            ht = super(NodeView, self).headTitle
            if ht not in parts:
                parts.append(ht)
        if self.globalOptions('reverseHeadTitle'):
            parts.reverse()
        return ' - ' .join(parts)

    @Lazy
    def menuItems(self):
        return [NodeView(child, self.request)
                    for child in self.context.getMenuItems()]

    @Lazy
    def parents(self):
        return getParents(self.context)

    @Lazy
    def nearestMenuItem(self):
        return self.getNearestMenuItem()

    def getNearestMenuItem(self, all=False):
        menu = self.menuObject
        menuItem = None
        for p in [self.context] + self.parents:
            if not all and not p.isMenuItem():
                menuItem = None
            elif menuItem is None:
                menuItem = p
            if p == menu:
                return menuItem
        return None

    def selected(self, item):
        return item.context == self.nearestMenuItem

    def active(self, item):
        return item.context == self.context or item.context in self.parents

    # virtual target support

    @Lazy
    def virtualTargetObject(self):
        target = self.viewAnnotations.get('target')
        if target is None:
            target = self.context.target
            if target is not None:
                target = getVersion(target, self.request)
        return target

    target = virtualTargetObject

    @Lazy
    def targetUid(self):
        if self.virtualTargetObject:
            return util.getUidForObject(self.virtualTargetObject)
        else:
            return None

    def targetView(self, name='index.html', methodName='show'):
        if name == 'index.html':    # only when called for default view
            tv = self.viewAnnotations.get('targetView')
            if tv is not None and callable(tv):
                return tv()
        if '?' in name:
            name, params = name.split('?', 1)
        target = self.virtualTargetObject
        if target is not None:
            if isinstance(target, AdapterBase):
                target = target.context
            targetView = component.queryMultiAdapter(
                                (adapted(target), self.request), name=name)
            if targetView is None:
                targetView = component.getMultiAdapter(
                                (target, self.request), name=name)
            if name == 'index.html' and hasattr(targetView, 'show'):
                return targetView.show()
            method = getattr(targetView, methodName, None)
            if method:
                return method()
            return targetView()
        return u''

    def targetDefaultView(self):
        target = self.virtualTargetObject
        if target is not None:
            # zope.app.publisher.browser
            name = getDefaultViewName(target, self.request)
            return self.targetView(name)
        return u''

    def targetDownload(self):
        return self.targetView('download.html', 'download')

    def targetRender(self):
        return u'<div>%s</div>' % self.targetView('download.html', 'show')

    def getViewForTarget(self, obj, setup=True):
        if obj is not None:
            obj = baseObject(obj)
            basicView = component.getMultiAdapter((obj, self.request))
            if obj == self.targetObject:
                basicView._viewName = self.context.viewName
            if setup:
                basicView.setupController()
            if hasattr(basicView, 'view'):
                return basicView.view

    @Lazy
    def virtualTarget(self):
        tv = self.viewAnnotations.get('targetView')
        if tv is not None:
            tv.setupController()
            return tv
        setup = self.setupTarget
        return self.getViewForTarget(self.virtualTargetObject, setup=setup)

    @Lazy
    def targetId(self):
        target = self.virtualTargetObject
        if target is not None:
            return BaseView(target, self.request).uniqueId

    @Lazy
    def virtualTargetUrl(self):
        target = self.virtualTargetObject
        if target is not None:
            tv = BaseView(target, self.request)
            return self.makeTargetUrl(self.url, tv.uniqueId, tv.title)
        else:
            return self.url

    @Lazy
    def virtualTargetUrlWithSkin(self):
        url = self.virtualTargetUrl
        if self.skin:
            parts = urlparse(url)
            url = urlunparse(parts[:2] +
                             ('/++skin++' + self.skin.__name__ + parts[2],) +
                             parts[3:])
        return url

    @Lazy
    def realTargetUrl(self):
        target = self.virtualTargetObject
        if target is not None:
            return BaseView(target, self.request).url

    @Lazy
    def typeProvider(self):
        if self.virtualTargetObject is not None:
            return IType(self.virtualTargetObject).typeProvider
        return None

    # target viewing and editing support

    def getUrlForTarget(self, target):
        """ Return URL of given target view given as .XXX URL.
        """
        if isinstance(target, BaseView):
            return self.makeTargetUrl(self.url, target.uniqueId, target.title)
        else:
            target = baseObject(target)
            return self.makeTargetUrl(self.url, util.getUidForObject(target),
                                      target.title)

    def getActions(self, category='object', page=None, target=None):
        actions = []
        #self.registerDojo()
        self.registerDojoFormAll()
        if target is None:
            target = self.virtualTarget
            #target = self.getViewForTarget(self.virtualTargetObject,
            #                               setup=False)
        if category in self.actions:
            actions.extend(self.actions[category](self, target=target))
        if target is not None and self.setupTarget:
            actions.extend(target.getActions(
                                    category, page=self, target=target))
        if target is not None and target.context != self.virtualTargetObject:
            # self view must be used directly for target
            actions.extend(self.view.getAdditionalActions(
                                    category, self, target))
        return actions

    def getPortletActions(self, target=None):
        actions = []
        cmeUrl = self.conceptMapEditorUrl
        if cmeUrl:
            actions.append(Action(self, title='Edit Concept Map',
                      targetWindow='loops_cme',
                      description='Open concept map editor in new window',
                      url=cmeUrl, target=target))
        if self.checkAction('create_resource', 'portlet', target):
            actions.append(DialogAction(self, name='create_resource',
                      title='Create Resource...',
                      description='Create a new resource object.',
                      page=self, target=target,
                      permission='zope.ManageContent'))
        return actions

    actions = dict(portlet=getPortletActions)

    def checkAction(self, name, category, target):
        if target is not None:
            return target.checkAction(name, category, target)
        return super(NodeView, self).checkAction(name, category, target)

    @Lazy
    def popupCreateObjectForm(self):
        return ("javascript:function%%20openDialog(url){"
                    "window.open('%s/create_object_popup.html"
                            "?title='+document.title+'"
                            "&form.type=.loops/concepts/note&fixed_type=yes&linkUrl='+url,"
                        "'loops_dialog',"
                        "'width=650,height=550,left=300,top=200');;"
                        "}"
                    "openDialog(window.location.href);" % self.topMenu.url)

    @Lazy
    def hasEditableTarget(self):
        return IResource.providedBy(self.virtualTargetObject)

    @Lazy
    def inlineEditable(self):
        target = self.virtualTarget
        return target and target.inlineEditable or False

    def inlineEdit(self, id):
        self.registerDojo()
        cm = self.controller.macros
        jsCall = 'dojo.require("dijit.Editor")'
        cm.register('js-execute', jsCall, jsCall=jsCall)
        return ('return inlineEdit("%s", "%s/inline_save")'
                                        % (id, self.virtualTargetUrl))

    def checkRTE(self):
        target = self.virtualTarget
        if target and target.inlineEditable:
            self.registerDojo()
            cm = self.controller.macros
            jsCall = 'dojo.require("dijit.Editor")'
            cm.register('js-execute', jsCall, jsCall=jsCall)

    def externalEdit(self):
        target = self.virtualTargetObject
        if target is None:
            target = self.context
            url = self.url
        else:
            ti = IType(target).typeInterface
            if ti is not None:
                target = ti(target)
            url = self.virtualTargetUrl
        self.recordAccess('external_edit')
        return ExternalEditorView(target, self.request).load(url=url)

    def externalEditorSaveAsNewVersion(self):
        # ignore versioning requests issued by external editor client
        pass

    # work items

    @Lazy
    def work_macros(self):
        from loops.organize.work.browser import work_macros
        return work_macros.macros

    # comments

    @Lazy
    def comment_macros(self):
        from loops.organize.comment.browser import comment_macros
        return comment_macros.macros

    @Lazy
    def comments(self):
        return component.getMultiAdapter((self.context, self.request),
                                         name='comments.html')


# inner HTML views


class ObjectInfo(NodeView):

    __call__ = innerHtml

    @Lazy
    def macros(self):
        return self.controller.getTemplateMacros('info', info_macros)

    @Lazy
    def macro(self):
        return self.macros['object_info']

    @Lazy
    def dialog_name(self):
        return self.request.get('dialog', 'object_info')


class MetaInfo(ObjectInfo):

    __call__ = innerHtml

    @Lazy
    def macro(self):
        return self.macros['meta_info']


class InlineEdit(NodeView):
    """ Provides inline editor as inner HTML"""

    @Lazy
    def macro(self):
        return self.template.macros['inline_edit']

    def __call__(self):
        return innerHtml(self)

    @property
    def body(self):
        return self.virtualTargetObject.data

    def save(self):
        target = self.virtualTargetObject
        ti = IType(target).typeInterface
        if ti is not None:
            target = ti(target)
        data = self.request.form['editorContent']
        if type(data) != unicode:
            try:
                data = data.decode('ISO-8859-15')  # IE hack
            except UnicodeDecodeError:
                print 'loops.browser.node.InlineEdit.save():', data
                return
        #    data = data.decode('UTF-8')
        target.data = data
        notify(ObjectModifiedEvent(target, Attributes(IResource, 'data')))
        #versionParam = self.hasVersions and '?version=this' or ''
        #self.request.response.redirect(self.virtualTargetUrl + versionParam)
        return 'OK'


# special (named) views for nodes

class SpecialNodeView(NodeView):

    macroName = None # to be provided by subclass

    @Lazy
    def macro(self):
        return self.template.macros[self.macroName]

    @Lazy
    def view(self):
        return self


class ContentView(SpecialNodeView):

    macroName = 'content_only'


class ListPages(SpecialNodeView):

    macroName = 'listpages'


class ListResources(SpecialNodeView):

    macroName = 'listresources'


class ListChildren(SpecialNodeView):

    macroName = 'listchildren'


class ListSubobjects(SpecialNodeView):

    macroName = 'listsubobjects'


class ConfigureView(NodeView):
    """ An editing view for configuring a node, optionally creating
        a target object.
    """

    def __init__(self, context, request):
        #self.context = context
        self.context = removeSecurityProxy(context)
        self.request = request

    @Lazy
    def target(self):
        obj = self.targetObject
        if obj is not None:
            return component.getMultiAdapter((obj, self.request))

    def update(self):
        request = self.request
        action = request.get('action')
        if action is None or action == 'search':
            return True
        if action == 'create':
            return self.createAndAssign()
        if action == 'assign':
            token = request.get('token')
            if token:
                target = self.loopsRoot.loopsTraverse(token)
            else:
                target = None
            self.context.target = target
        # TODO: raise error
        return True

    def createAndAssign(self):
        form = self.request.form
        root = self.loopsRoot
        token = form.get('create.type', 'loops.resource.MediaAsset')
        type = ITypeManager(self.context).getType(token)
        factory = type.factory
        container = type.defaultContainer
        name = form.get('create.name', '')
        if not name:
            viewManagerPath = getPath(root.getViewManager())
            name = getPath(self.context)[len(viewManagerPath)+1:]
            name = name.replace('/', '.')
        # check for duplicates:
        num = 1
        basename = name
        while name in container:
            name = '%s-%d' % (basename, num)
            num += 1
        container[name] = removeSecurityProxy(factory())
        target = container[name]
        target.title = form.get('create.title', u'')
        if IConcept.providedBy(target):
            target.conceptType = type.typeProvider
        elif IResource.providedBy(target):
            target.resourceType = type.typeProvider
        notify(ObjectCreatedEvent(target))
        notify(ObjectModifiedEvent(target))
        self.context.target = target
        return True

    def targetTypes(self):
        return util.KeywordVocabulary([(t.token, t.title)
                        for t in ITypeManager(self.context).types])

    def targetTypesForSearch(self):
        general = [('loops:*', 'Any'), ('loops:concept:*', 'Any Concept'),
                   ('loops:resource:*', 'Any Resource'),]
        return util.KeywordVocabulary(general + [(t.tokenForSearch, t.title)
                        for t in ITypeManager(self.context).types])

    @Lazy
    def search(self):
        request = self.request
        if request.get('action') != 'search':
            return []
        searchTerm = request.get('searchTerm', None)
        searchType = request.get('searchType', None)
        if searchTerm or searchType:
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
            cat = component.getUtility(ICatalog)
            result = cat.searchResults(**criteria)
            # TODO: can this be done in a faster way?
            result = [r for r in result if r.getLoopsRoot() == self.loopsRoot]
        else:
            result = (list(self.loopsRoot.getConceptManager().values())
                    + list(self.loopsRoot.getResourceManager().values()))
        return list(self.viewIterator(result))

    def viewIterator(self, objs):
        request = self.request
        for o in objs:
            if o == self.context.target:
                continue
            yield BaseView(o, request)


class NodeAdding(Adding):

    pass

    def xx_addingInfo(self):
        info = super(NodeAdding, self).addingInfo()
        #info.append({'title': 'Document',
        #             'action': 'AddLoopsNodeDocument.html',
        #             'selected': '',
        #             'has_custom_add_view': True,
        #             'description': 'This creates a node with an associated document'})
        return info


class ViewPropertiesConfigurator(object):

    interface.implements(IViewConfiguratorSchema)
    component.adapts(INode)

    def __init__(self, context):
        self.context = removeSecurityProxy(context)

    def setSkinName(self, skinName):
        ann = IAnnotations(self.context)
        setting = ann.get(configurator.ANNOTATION_KEY, {})
        setting['skinName'] = {'value': skinName}
        ann[configurator.ANNOTATION_KEY] = setting
    def getSkinName(self):
        ann = IAnnotations(self.context)
        setting = ann.get(configurator.ANNOTATION_KEY, {})
        return setting.get('skinName', {}).get('value', '')
    skinName = property(getSkinName, setSkinName)

    def setOptions(self, options):
        ann = IAnnotations(self.context)
        setting = ann.get(configurator.ANNOTATION_KEY, {})
        setting['options'] = {'value': options}
        ann[configurator.ANNOTATION_KEY] = setting
    def getOptions(self):
        ann = IAnnotations(self.context)
        setting = ann.get(configurator.ANNOTATION_KEY, {})
        return setting.get('options', {}).get('value', [])
    options = property(getOptions, setOptions)


class NodeViewConfigurator(configurator.AnnotationViewConfigurator):
    """ Take properties from next menu item...
    """

    @property
    def viewProperties(self):
        result = []
        for p in list(reversed(getParents(self.context))) + [self.context]:
            if not INode.providedBy(p) or p.nodeType != 'menu':
                continue
            ann = IAnnotations(p)
            propDefs = ann.get(configurator.ANNOTATION_KEY, {})
            if propDefs:
                result.extend([self.setupViewProperty(prop, propDef)
                                for prop, propDef in propDefs.items() if propDef])
        return result


# traveral adapter

class NodeTraverser(ItemTraverser):

    component.adapts(INode)

    def publishTraverse(self, request, name):
        viewAnnotations = request.annotations.setdefault('loops.view', {})
        viewAnnotations['node'] = self.context
        #context = removeSecurityProxy(self.context)
        context = self.context
        if context.nodeType == 'menu':
            setViewConfiguration(context, request)
        if name == '.loops':
            name = self.getTargetUid(request)
            #return self.context.getLoopsRoot()
        if name.startswith('.'):
            name = self.cleanUpTraversalStack(request, name)[1:]
            target = self.getTarget(name)
            if target is not None:
                # remember self.context in request
                if request.method == 'PUT':
                    # we have to use the target object directly
                    return target
                else:
                    # switch to correct version if appropriate
                    target = getVersion(target, request)
                    # we'll use the target object in the node's context
                    viewAnnotations['target'] = target
                    return self.context
        target = viewAnnotations.get('target')
        if target is not None:      # name may be a view name for target
            langInfo = LanguageInfo(self.context, request)
            adTarget = adapted(target, langInfo)
            view = component.queryMultiAdapter((adTarget, request), name=name)
            if isinstance(view, BaseView):
                viewAnnotations['targetView'] = view
                view.logInfo('NodeTraverser:targetView = %r' % view)
                return self.context
        obj = super(NodeTraverser, self).publishTraverse(request, name)
        return obj

    def getTargetUid(self, request):
        parent = self.context.getLoopsRoot()
        stack = request._traversal_stack
        for i in range(2):
            name = stack.pop()
            obj = parent.get(name)
            if not obj:
                return name
            parent = obj
        return '.' + util.getUidForObject(obj)

    def cleanUpTraversalStack(self, request, name):
        #traversalStack = request._traversal_stack
        #while traversalStack and traversalStack[0].startswith('.'):
            # skip obsolete target references in the url
        #    name = traversalStack.pop(0)
        traversedNames = request._traversed_names
        for n in list(traversedNames):
            if n.startswith('.'):
                # remove obsolete target refs
                traversedNames.remove(n)
        #if traversedNames:
        #    lastTraversed = traversedNames[-1]
        #    if lastTraversed.startswith('.') and lastTraversed != name:
                # let <base .../> tag show the current object
        #        traversedNames[-1] = name
        # let <base .../> tag show the current object
        traversedNames.append(name)
        return name

    def getTarget(self, name):
        if name.startswith('target'):
            name = name[6:]
        if '-' in name:
            name, ignore = name.split('-', 1)
        if name and name.isdigit():
            return util.getObjectForUid(int(name))
        return self.context.target


def setViewConfiguration(context, request):
    viewAnnotations = request.annotations.setdefault('loops.view', {})
    config = IViewConfiguratorSchema(context)
    skinName = config.skinName
    if not skinName:
        skinName = context.getLoopsRoot().skinName
    if skinName:
        viewAnnotations['skinName'] = skinName
    if config.options:
        viewAnnotations['options'] = config.options
    return dict(skinName=skinName, options=config.options)

def getViewConfiguration(context, request):
    if INode.providedBy(context) and context.nodeType == 'menu':
        setViewConfiguration(context, request)
    viewAnnotations = request.annotations.get('loops.view', {})
    return dict(skinName=viewAnnotations.get('skinName'),
                options=viewAnnotations.get('options'))



class TestView(NodeView):

    def __call__(self):
        print '*** begin'
        for i in range(500):
            #x = util.getObjectForUid('1994729849')
            x = util.getObjectForUid('2018653366')
            self.c = list(x.getChildren())
            #self.c = list(x.getChildren([self.defaultPredicate]))
        print '*** end', len(self.c)
        return 'done'

