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
from zope import component
from zope.component import adapts
from zope.interface import implements, Attribute
from zope.cachedescriptors.property import Lazy
from zope.schema.interfaces import IField
from zope.traversing.api import getName, getParent

from cybertools.meta.interfaces import IOptions
from cybertools.stateful.interfaces import IStateful
from cybertools.text.mimetypes import extensions
from cybertools.typology.interfaces import IType
from loops.common import adapted, baseObject
from loops.interfaces import IResource, IExternalFile
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
        self.__parent__ = context

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
            versionId = '.'.join('1' for x in self.versionLevels)
            #versions['1.1'] = self.context
            versions[versionId] = self.context
            setattr(self.context, attrName, versions)

    @Lazy
    def versionLevels(self):
        options = IOptions(self.master.getLoopsRoot()).useVersioning
        if options:
            if isinstance(options, list):
                return options
            return ['major', 'minor']
        return []

    @Lazy
    def versionNumbers(self):
        #return self.getVersioningAttribute('versionNumbers', (1, 1))
        return self.getVersioningAttribute('versionNumbers',
                                    tuple(1 for x in self.versionLevels))

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

    def createVersionObject(self, versionNumbers, variantIds, comment=u''):
        versionableMaster = self.versionableMaster
        versionableMaster.initVersions()
        context = self.context
        # create object
        cls = context.__class__
        obj = cls()
        # set versioning attributes of new object
        versionableObj = IVersionable(obj)
        versionableObj.setVersioningAttribute('versionNumbers', tuple(versionNumbers))
        versionableObj.setVersioningAttribute('variantIds', variantIds)
        versionableObj.setVersioningAttribute('master', self.master)
        versionableObj.setVersioningAttribute('parent', context)
        versionableObj.setVersioningAttribute('comment', comment)
        # generate name for new object, register in parent
        versionId = versionableObj.versionId
        name = self.generateName(getName(self.master),
                                 extensions.get(context.contentType, ''),
                                 versionId)
        getParent(context)[name] = obj
        # record version on master
        self.versions[versionableObj.versionId] = obj
        # set resource attributes
        ti = IType(context).typeInterface
        attrs = set((ti and list(ti) or [])
                    + ['title', 'description', 'data', 'contentType'])
        adaptedContext = ti and ti(context) or context
        adaptedObj = ti and ti(obj) or obj
        if 'context' in attrs:
            attrs.remove('context')
        if IExternalFile.providedBy(adaptedObj):
            for name in ('data', 'externalAddress',):
                attrs.remove(name)
        for attr in attrs:
            setattr(adaptedObj, attr, getattr(adaptedContext, attr))
        if IExternalFile.providedBy(adaptedObj):
            adaptedObj.storageParams = adaptedContext.storageParams
            adaptedObj.storageName = adaptedContext.storageName
            extAddr = adaptedContext.externalAddress
            newExtAddr = self.generateName(adapted(self.master).externalAddress,
                                 extensions.get(context.contentType, ''),
                                 versionId)
            adaptedObj.externalAddress = newExtAddr
            adaptedObj.data = adaptedContext.data
            adaptedObj.externalAddress = newExtAddr # trigger post-processing
        self.setStates(obj)
        return obj

    def createVersion(self, level=1, comment=u''):
        # get the new version numbers
        vn = list(IVersionable(self.currentVersion).versionNumbers)
        while len(vn) <= level:
            vn.append(1)
        vn[level] += 1
        for l in range(level+1, len(vn)):
            # reset lower levels
            vn[l] = 1
        # create new object
        obj = self.createVersionObject(vn, self.variantIds, comment)
        # set attributes of the master version
        self.versionableMaster.setVersioningAttribute('currentVersion', obj)
        return obj

    def generateName(self, name, ext, versionId):
        if ext:
            if ext and name.endswith(ext):
                name = name[:-len(ext)]
        else:
            parts = name.rsplit('.', 1)
            if len(parts) == 2 and len(parts[1]) <= 4:
                name, ext = parts
        #elif len(name) > 3 and name[-4] == '.':
        #    ext = name[-4:]
        #    name = name[:-4]
        if not ext.startswith('.'):
            ext = '.' + ext
        return name + '_' + versionId + ext

    def setStates(self, obj):
        options = IOptions(self.master.getLoopsRoot()).organize.stateful.resource
        if options:
            for name in options:
                stf = component.getAdapter(self.context, IStateful, name=name)
                stfn = component.getAdapter(obj, IStateful, name=name)
                stfn.state = stf.state


def cleanupVersions(context, event):
    """ Called upon deletion of a resource.
    """
    vContext = IVersionable(context, None)
    if vContext is None:
        return
    rm = context.getLoopsRoot().getResourceManager()
    if context == vContext.master:
        toBeDeleted = []
        for v in vContext.versions.values():
            if v != context:
                toBeDeleted.append(getName(v))
        for name in toBeDeleted:
            del rm[name]
    else:
        vId = vContext.versionId
        vMaster = IVersionable(vContext.master)
        del vMaster.versions[vId]
        if vMaster.getVersioningAttribute('currentVersion', None) == context:
            newCurrent = sorted(vMaster.versions.items())[-1][1]
            vMaster.setVersioningAttribute('currentVersion', newCurrent)

