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
View class(es) for change tracks.

$Id$
"""

from zope import component
from zope.app.security.interfaces import IAuthentication, PrincipalLookupError
from zope.cachedescriptors.property import Lazy
from zope.app.pagetemplate import ViewPageTemplateFile
from zope.traversing.browser import absoluteURL
from zope.traversing.api import getName

from cybertools.browser.action import actions
from cybertools.tracking.browser import TrackView
from loops.browser.action import DialogAction
from loops.browser.form import ObjectForm, EditObject
from loops.organize.tracking.browser import BaseTrackView
from loops import util


work_macros = ViewPageTemplateFile('work_macros.pt')


class WorkItemView(BaseTrackView):

    pass


class CreateWorkItemForm(ObjectForm):

    template = work_macros

    @Lazy
    def macro(self):
        return self.template.macros['create_workitem']


# actions

actions.register('createWorkitem', 'portlet', DialogAction,
        title=_(u'Create Work Item...'),
        description=_(u'Create a work item for this object.'),
        viewName='create_workitem.html',
        dialogName='createWorkitem',
)
