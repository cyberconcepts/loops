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


class TargetAction(object):

    @Lazy
    def url(self):
        return self.view.virtualTargetUrl

