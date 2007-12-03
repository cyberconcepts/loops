#
#  Copyright (c) 2007 Helmut Merz helmutm@cy55.de
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
Base classes (sort of views) for action portlet items.

$Id$
"""

from urllib import urlencode
from zope import component
from zope.app.pagetemplate import ViewPageTemplateFile
from zope.cachedescriptors.property import Lazy

action_macros = ViewPageTemplateFile('action_macros.pt')


class Action(object):

    template = action_macros
    macroName = 'action'
    condition = True
    permission = None
    url = '.'
    targetWindow = ''
    title = ''
    description = ''
    icon = ''
    cssClass = ''
    onClick = ''
    innerHtmlId = ''

    def __init__(self, view, **kw):
        self.view = view
        for k, v in kw.items():
            setattr(self, k, v)

    @Lazy
    def macro(self):
        return self.template.macros[self.macroName]

    @Lazy
    def url(self):
        return self.view.url


class TargetAction(Action):

    @Lazy
    def url(self):
        return self.view.virtualTargetUrl


class DialogAction(Action):

    jsOnClick = "objectDialog('%s', '%s/%s?%s'); return false;"

    page = None
    viewName = 'create_object.html'
    dialogName = 'create'
    qualifier = typeToken = innerForm = None
    fixedType = False

    @Lazy
    def url(self):
        return self.viewName

    @Lazy
    def onClick(self):
        urlParams = dict(dialog=self.dialogName)
        if self.qualifier:
            urlParams['qualifier'] = self.qualifier
        if self.typeToken:
            urlParams['form.type'] = self.typeToken
        if self.innerForm:
            urlParams['inner_form'] = self.innerForm
        if self.fixedType:
            urlParams['fixed_type'] = 'yes'
        return self.jsOnClick % (self.dialogName, self.page.virtualTargetUrl,
                                 self.viewName, urlencode(urlParams))

    @Lazy
    def innerHtmlId(self):
        return 'dialog.' + self.dialogName

