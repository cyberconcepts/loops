# loops.base

""" Implementation of loops root object.
"""

from zope.container.btree import BTreeContainer
from zope.site.folder import Folder
from zope.site.interfaces import IFolder
from zope.traversing.api import getPath, traverse
from zope.interface import implementer

from cybertools.util.jeep import Jeep
from loops.interfaces import ILoops

loopsPrefix = '.loops'


@implementer(ILoops)
class Loops(Folder):

    _skinName = ''
    def getSkinName(self): return self._skinName
    def setSkinName(self, skinName): self._skinName = skinName
    skinName = property(getSkinName, setSkinName)

    def getOptions(self): return getattr(self, '_options', [])
    def setOptions(self, value): self._options = value
    options = property(getOptions, setOptions)

    def getLoopsRoot(self):
        return self

    def getAllParents(self, collectGrants=False, ignoreTypes=False):
        return Jeep()

    def getConceptManager(self):
        return self['concepts']

    def getResourceManager(self):
        return self['resources']

    def getViewManager(self):
        return self['views']

    def getRecordManager(self):
        return self.get('records')

    def getLoopsUri(self, obj):
        uri = loopsPrefix + getPath(obj)[len(getPath(self)):]
        return uri

    def loopsTraverse(self, uri):
        prefix = loopsPrefix + '/'
        if uri.startswith(prefix):
            return traverse(self, uri[len(prefix):])


class ParentInfo(object):

    def __init__(self, obj, relations=None, grants=None):
        self.object = obj
        self.relations = relations or []
        self.grants = grants or []


# backward compatibility for old loops sites that got their Loops object
# directly from loops/__init__.py
import loops
loops.Loops = Loops

