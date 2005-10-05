#
#  Copyright (c) 2004 Helmut Merz helmutm@cy55.de
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
Definition of the Task view class.

$Id$
"""

from zope.app import zapi
from zope.app.dublincore.interfaces import ICMFDublinCore
from zope.security.proxy import removeSecurityProxy

from loops.interfaces import ITask

class Details(object):

    def modified(self):
        """ get date/time of last modification
        """
        dc = ICMFDublinCore(self.context)
        d = dc.modified or dc.created
        return d and d.strftime('%Y-%m-%d %H:%M') or ''


class SubtaskAssignments(Details):

    def assignSubtask(self):
        """ Add a subtask denoted by the path given in the
            request variable subtaskPath.
        """
        subtaskPath = self.request.get('subtaskPath')
        #if subtaskPath:
        subtask = zapi.traverse(zapi.getRoot(self.context), subtaskPath, None, self.request)
        #if subtask:
        self.context.assignSubtask(removeSecurityProxy(subtask))
        self.request.response.redirect('.')
