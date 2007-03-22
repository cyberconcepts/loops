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
Utilities for managing version informations.

$Id$
"""

from BTrees.OOBTree import OOBTree
from zope.component import adapts
from zope.interface import implements, Attribute
from zope.cachedescriptors.property import Lazy
from zope.schema.interfaces import IField
from zope.traversing.api import getName, getParent

from cybertools.text.mimetypes import extensions
from cybertools.typology.interfaces import IType
from loops.interfaces import IResource
from loops.versioning.interfaces import IVersionable


_not_found = object()
attrPattern = '__version_%s__'


class VersionableResource(object):
    """ An adapter that enables a resource to store version information.
    """

    implements(IVersionable)
    adapts(IResource)

    def __init__(self, context):
        self.context = context

    def getVersioningAttribute(self, attr, default):
        attrName = attrPattern % attr
        value = getattr(self.context, attrName, _not_found)
        if value is _not_found:
            return default
        return value

    def setVersioningAttribute(self, attr, value):
        attrName = attrPattern % attr
        setattr(self.context, attrName, value)

    def initVersions(self):
        attrName = attrPattern % 'versions'
        value = getattr(self.context, attrName, _not_found)
        if value is _not_found:
            versions = OOBTree()
            versions['1.1'] = self.context
            setattr(self.context, attrName, versions)
        #self.versions['1.1'] = self.context

    @Lazy
    def versionNumbers(self):
        return self.getVersioningAttribute('versionNumbers', (1, 1))

    @Lazy
    def variantIds(self):
        return self.getVersioningAttribute('variantIds', ())

    @Lazy
    def versionId(self):
        versionPart = '.'.join(str(n) for n in self.versionNumbers)
        return '_'.join([versionPart] + list(self.variantIds))

    @Lazy
    def master(self):
        return self.getVersioningAttribute('master', self.context)

    @Lazy
    def versionableMaster(self):
        """ The adapted master... """
        return IVersionable(self.master)

    @Lazy
    def parent(self):
        return self.getVersioningAttribute('parent', None)

    @Lazy
    def comment(self):
        return self.getVersioningAttribute('comment', u'')

    @property
    def versions(self):
        return self.versionableMaster.getVersioningAttribute('versions', {})

    @property
    def currentVersion(self):
        return self.versionableMaster.getVersioningAttribute('currentVersion', self.master)

    @property
    def releasedVersion(self):
        m = self.versionableMaster
        return self.versionableMaster.getVersioningAttribute('releasedVersion', None)

    def createVersion(self, level=1, comment=u''):
        context = self.context
        versionableMaster = self.versionableMaster
        # get the new version numbers
        vn = list(IVersionable(self.currentVersion).versionNumbers)
        while len(vn) <= level:
            vn.append(1)
        vn[level] += 1
        for l in range(level+1, len(vn)):
            # reset lower levels
            vn[l] = 1
        # create new object
        cls = context.__class__
        obj = cls()
        # set versioning attributes of new object
        versionableObj = IVersionable(obj)
        versionableObj.setVersioningAttribute('versionNumbers', tuple(vn))
        versionableObj.setVersioningAttribute('variantIds', self.variantIds)
        versionableObj.setVersioningAttribute('master', self.master)
        versionableObj.setVersioningAttribute('parent', context)
        versionableObj.setVersioningAttribute('comment', comment)
        # generate name for new object, register in parent
        versionId = versionableObj.versionId
        name = self.generateName(getName(context),
                                 extensions.get(context.contentType, ''),
                                 versionId)
        getParent(context)[name] = obj
        # set resource attributes
        ti = IType(context).typeInterface
        attrs = set((ti and list(ti) or [])
                    + ['title', 'description', 'data', 'contentType'])
        adaptedContext = ti and ti(context) or context
        adaptedObj = ti and ti(obj) or obj
        for attr in attrs:
            setattr(adaptedObj, attr, getattr(adaptedContext, attr))
        # set attributes of the master version
        versionableMaster.setVersioningAttribute('currentVersion', obj)
        versionableMaster.initVersions()
        self.versions[versionId] = obj
        return obj

    def generateName(self, name, ext, versionId):
        if ext:
            ext = '.' + ext
            if ext and name.endswith(ext):
                name = name[:-len(ext)]
        elif len(name) > 3 and name[-4] == '.':
            ext = name[-4:]
            name = name[:-4]
        return name + '_' + versionId + ext

