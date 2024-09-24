# loops.browser.action

""" Base classes (sort of views) for action portlet items.
"""

from urllib.parse import urlencode
from zope import component
from zope.app.pagetemplate import ViewPageTemplateFile
from zope.cachedescriptors.property import Lazy

from cybertools.browser.action import Action, actions
from loops.util import _


class TargetAction(Action):

    page = None
    qualifier = typeToken = None
    fixedType = False
    viewTitle = ''
    addParams = {}

    @Lazy
    def url(self):
        if self.page is None:   # how could this happen?
            baseUrl = self.view.virtualTargetUrl
        else:
            if self.target is not None:
                baseUrl = self.page.getUrlForTarget(self.target)
            else:
                baseUrl = self.page.virtualTargetUrl
        paramString = ''
        urlParams = {}
        if self.typeToken:
            urlParams['form.type'] = self.typeToken
        if self.fixedType:
            urlParams['fixed_type'] = 'yes'
        urlParams.update(self.addParams)
        if urlParams:
            paramString = '?' + urlencode(urlParams)
        url = self.getActionUrl(baseUrl)
        return url + paramString


class DialogAction(Action):

    jsOnClick = "objectDialog('%s', '%s/%s?%s'); return false;"

    page = None
    viewName = 'create_object.html'
    dialogName = 'create'
    qualifier = typeToken = innerForm = None
    fixedType = False
    viewTitle = ''
    addParams = {}

    @Lazy
    def url(self):
        if self.target is not None:
            url = self.page.getUrlForTarget(self.target)
        else:
            url = self.page.virtualTargetUrl
        return '%s/%s' % (url, self.viewName)

    @Lazy
    def onClick(self):
        urlParams = dict(dialog=self.dialogName, version='this')
        if self.qualifier:
            urlParams['qualifier'] = self.qualifier
        if self.typeToken:
            urlParams['form.type'] = self.typeToken
        if self.innerForm:
            urlParams['inner_form'] = self.innerForm
        if self.fixedType:
            urlParams['fixed_type'] = 'yes'
        if self.viewTitle:
            urlParams['view_title'] = self.viewTitle
        #for k, v in self.page.sortInfo.items():
        #    urlParams['sortinfo_' + k] = v['fparam']
        urlParams.update(self.addParams)
        if self.target is not None:
            url = self.page.getUrlForTarget(self.target)
        else:
            url = self.page.virtualTargetUrl
        return self.jsOnClick % (self.dialogName, url, self.viewName,
                                 urlencode(urlParams))

    @Lazy
    def innerHtmlId(self):
        return 'dialog.' + self.dialogName


# standard actions

actions.register('info', 'object', DialogAction,
        description=_(u'Information about this object.'),
        viewName='object_info.html',
        dialogName='',
        icon='cybertools.icons/info.png',
        cssClass='icon-action',
        addParams=dict(version='this'),
)

actions.register('external_edit', 'object', TargetAction,
        description=_(u'Edit with external editor.'),
        viewName='external_edit',
        icon='edit.gif',
        cssClass='icon-action',
)

actions.register('create_object', 'portlet', DialogAction,
        title=_('Create Resource...'),
        description=_('Create a new resource object.'),
        viewName='create_object.html',
        dialogName='edit',
        prerequisites=['registerDojoEditor'],
        permission='zope.ManageContent',
)

actions.register('edit_object', 'portlet', DialogAction,
        title=_(u'Edit Resource...'),
        description=_(u'Modify resource object.'),
        viewName='edit_object.html',
        dialogName='edit',
        prerequisites=['registerDojoEditor'],
        permission='zope.ManageContent',
)

actions.register('edit_concept', 'portlet', DialogAction,
        title=_(u'Edit Concept...'),
        description=_(u'Modify concept object.'),
        viewName='edit_concept.html',
        dialogName='edit',
        prerequisites=['registerDojoEditor'],
        permission='zope.ManageContent',
)

actions.register('create_concept', 'portlet', DialogAction,
        title=_(u'Create Concept...'),
        description=_(u'Create a new concept.'),
        viewName='create_concept.html',
        dialogName='createConcept',
        qualifier='create_concept',
        innerForm='inner_concept_form.html',
        permission='loops.AssignAsParent',
)

actions.register('create_subtype', 'portlet', DialogAction,
        title=_(u'Create Concept...'),
        description=_(u'Create a new concept.'),
        viewName='create_concept.html',
        dialogName='createConcept',
        qualifier='subtype',
        innerForm='inner_concept_form.html',
        permission='loops.AssignAsParent',
)
