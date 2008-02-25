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
Definition of view classes and other browser related stuff for tasks.

$Id$
"""

from zope import interface, component
from zope.app.pagetemplate import ViewPageTemplateFile
from zope.cachedescriptors.property import Lazy

from loops.browser.action import DialogAction
from loops.browser.concept import ConceptView
from loops.util import _


organize_macros = ViewPageTemplateFile('view_macros.pt')


class TaskView(ConceptView):

    def getActions(self, category='object', page=None):
        actions = []
        if category == 'portlet':
            actions.append(DialogAction(self, title=_(u'Edit Task...'),
                  description=_(u'Modify task.'),
                  viewName='edit_concept.html',
                  dialogName='editTask',
                  page=page))
            self.registerDojoDateWidget()
        return actions
