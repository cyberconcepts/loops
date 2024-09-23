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
View class(es) for accessing Flash videos.
Mittwoch
$Id$
"""

from zope import interface, component
from zope.cachedescriptors.property import Lazy

from cybertools.browser.action import Action, actions
from loops.browser.action import DialogAction
from loops.common import adapted
from loops.integrator.content.browser import ExternalAccessRenderer
from loops.util import _


actions.register('edit_video', 'portlet', DialogAction,
        title=_(u'Edit Video...'),
        description=_(u'Modify video information.'),
        viewName='edit_concept.html',
        viewTitle=_(u'Edit Video'),
        dialogName='edit',
        prerequisites=['registerDojoEditor'],
)


class FlashVideo(ExternalAccessRenderer):

    def __call__(self):
        return self.index(self)

    def publishTraverse(self, request, name):
        if name == 'start':
            return self
        return self.adapted()[name]

    @Lazy
    def title(self):
        return self.adapted.title

