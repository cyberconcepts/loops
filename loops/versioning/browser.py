# loops.versioning.browser

""" View classes for versioning.
"""

from zope import interface, component
from zope.authentication.interfaces import IUnauthenticatedPrincipal
from zope.browserpage import ViewPageTemplateFile
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

