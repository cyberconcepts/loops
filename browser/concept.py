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
from zope.cachedescriptors.property import Lazy
from zope.security.proxy import removeSecurityProxy
from loops.browser.common import BaseView


class ConceptView(BaseView):

    def children(self):
        request = self.request
        for c in self.context.getChildren():
            yield ConceptView(c, request)

    def parents(self):
        request = self.request
        for c in self.context.getParents():
            yield ConceptView(c, request)

    def update(self):
        concept_name = self.request.get('concept_name', None)
        if concept_name:
            concept = zapi.getParent(self.context)[concept_name]
            self.context.assignChild(removeSecurityProxy(concept))
        return True

