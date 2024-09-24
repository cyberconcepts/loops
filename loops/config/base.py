# loops.config.base

""" Adapters and others classes for analyzing resources.
"""

import os
from zope.cachedescriptors.property import Lazy
from zope import component
from zope.component import adapts
from zope.traversing.api import getName, getParent

from cybertools.meta.config import Options
from cybertools.meta.config import GlobalOptions as BaseGlobalOptions
from cybertools.meta.interfaces import IOptions
from cybertools.meta.namespace import Executor, ExecutionError
from cybertools.typology.interfaces import IType
from loops.common import AdapterBase
from loops.interfaces import ILoops, ILoopsObject, ITypeConcept, IPredicate
#from loops.query import IQueryConcept
from loops.expert.concept import IQueryConcept
from loops import util


class GlobalOptions(BaseGlobalOptions):

    @Lazy
    def _filename(self):
        return os.path.join(util.getEtcDirectory(), 'loops.cfg')


class LoopsOptions(Options):

    adapts(ILoopsObject)

    builtins = Options.builtins + ('True', 'False')
    #True, False = True, False
    _initialized = False

    def __init__(self, context, *args, **kw):
        self.context = context
        self['True'] = True
        self['False'] = False
        super(LoopsOptions, self).__init__(*args, **kw)

    def __getitem__(self, key):
        if not self._initialized:
            self._initialized = True
            self.loadContextOptions()
        return super(LoopsOptions, self).__getitem__(key)

    def __call__(self, key, default=None):
        value = super(LoopsOptions, self).__call__(key)
        if value is None:
            value = component.getUtility(IOptions)(key, default)
        return value

    def parseContextOptions(self):
        def result():
            options = getattr(self.context, 'options', None) or []
            for opt in options:
                parts = opt.split(':', 1)
                key = parts[0].strip()
                if len(parts) == 1:
                    value = 'True'
                else:
                    value = repr([p.strip() for p in parts[1].split(',')])
                yield '='.join((key, value))
        return '\n'.join(result())

    def loadContextOptions(self):
        code = self.parseContextOptions()
        rc = Executor(self).execute(code)
        if rc:
            raise ExecutionError('\n' + rc)

    def set(self, key, value):
        options = getattr(self.context, 'options', [])
        new_opt = []
        found = False
        def createItem(k, v):
            if v is True:
                return k
            if isinstance(v, (list, tuple)):
                v = ','.join(v)
            return '%s:%s' % (k, v)
        for item in options:
            parts = item.split(':', 1)
            if parts[0] == key:
                found = True
                if not value:
                    continue
                item = createItem(key, value)
            new_opt.append(item)
        if not found:
            new_opt.append(createItem(key, value))
        self.context.options = new_opt


class TypeOptions(LoopsOptions):

    adapts(ITypeConcept)


class QueryOptions(LoopsOptions):

    adapts(IQueryConcept)


class PredicateOptions(LoopsOptions):

    adapts(IPredicate)


class ConceptAdapterOptions(LoopsOptions):

    adapts(AdapterBase)


class DummyOptions(Options):

    def __getitem__(self, key):
        return []
