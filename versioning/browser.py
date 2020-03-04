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
View classes for versioning.
"""

from zope import interface, component
from zope.app.pagetemplate import ViewPageTemplateFile
from zope.app.security.interfaces import IUnauthenticatedPrincipal
from zope.cachedescriptors.property import Lazy

from loops.browser.common import BaseView
from loops.resource import Resource
from loops.versioning.interfaces import IVersionable
from loops.versioning.util import getVersion


version_macros = ViewPageTemplateFile('version_macros.pt')


class ListVersions(BaseView):

    template = version_macros

    @Lazy
    def version_macros(self):
        return self.controller.getTemplateMacros('versions', version_macros)

    @Lazy
    def macro(self):
        return self.version_macros['versions']

    def versions(self):
        versionable = IVersionable(self.context)
        versions = versionable.versions
        cls = getattr(self.controller, 'versionViewClass', None)
        for v in sorted(versions):
            if cls is not None:
                yield(cls(versions[v], self.request))
            elif isinstance(versions[v], Resource):
                from loops.browser.resource import ResourceView
                yield ResourceView(versions[v], self.request)
            else:
                yield BaseView(versions[v], self.request)

