# loops.server.psu - python shell utilities
# use this from a Python command line (in a loops / bluebrem virtual environment).
#
# then:
#
#   from loops.server import psu
#   import config
#   psu.setup('path/to/loopsRoot', 'zope-0.conf')
#   obj = psu.byuid('578457950')
#

import atexit
import os
from transaction import commit, abort
from zope.app import wsgi
from zope.app.authentication.principalfolder import Principal
from zope.cachedescriptors.property import Lazy
from zope.catalog.interfaces import ICatalog
from zope.component.hooks import setSite
from zope.container.contained import ObjectAddedEvent, ObjectRemovedEvent
from zope.copypastemove.interfaces import IContainerItemRenamer
from zope import component
from zope.event import notify
from zope.exceptions.interfaces import DuplicationError
from zope.interface import Interface
from zope.lifecycleevent import ObjectCreatedEvent, ObjectModifiedEvent
from zope.publisher.browser import TestRequest as BaseTestRequest
from zope.security.management import getInteraction, newInteraction, endInteraction
#from zope.pluggableauth.plugins.principalfolder import PrincipalInfo

from cybertools.util.date import date2TimeStamp, strptime
from cybertools.util.jeep import Jeep
from loops.common import adapted, baseObject
from loops.util import getObjectForUid, getUidForObject, getCatalog, reindex

os.environ['NLS_LANG'] = 'German_Germany.UTF8'

try:
    import config
except ImportError:
    print('*** config file could not be loaded!')
    config = None


sc = Jeep()     # shortcuts
conn = None

def closeConnection():
    if conn is not None:
        print('closing ZODB connection...')
        conn.close()

def setup(zope_conf=None, loopsRootPath=None, config=config):
    if zope_conf is None:
        zope_conf = getattr(config, 'zope_conf', 'zope.conf')
    if loopsRootPath is None:
        loopsRootPath = getattr(config, 'loops_path', None)
    global conn, root, sm, smdefault, intids, pau, loopsRoot, sc
    print(f'opening ZODB connection... - conf: {zope_conf}, path: {loopsRootPath}')
    conn = wsgi.config(zope_conf).open()
    atexit.register(closeConnection)
    root = conn.root()['Application']
    setSite(root)
    sm = component.getSiteManager(root)
    smdefault = sm['default']
    intids = smdefault['IntIds']
    pau = smdefault['PluggableAuthentication']
    user = getattr(config, 'shell_user', 'zope.manager')
    password = (getattr(config, 'shell_pw', None) or
                input('Enter manager password: '))
    login(Principal(user, password, u'Manager'))
    loopsRoot = root
    if loopsRootPath is not None:
        for name in loopsRootPath.split('/'):
            if name:
                loopsRoot = loopsRoot[name]
        sc.concepts = loopsRoot['concepts']
        for name in ('standard', 'hasType',):
            sc[name] = sc.concepts[name]


def byuid(uid):
    return getObjectForUid(uid)

def uid(obj):
    return getUidForObject(obj)

def notifyModification(obj):
    obj = baseObject(obj)
    notify(ObjectModifiedEvent(obj))

def save(obj):
    notifyModification(obj)
    commit()

def notifyAdded(obj):
    obj = baseObject(obj)
    notify(ObjectAddedEvent(obj))

def notifyRemoved(obj):
    obj = baseObject(obj)
    notify(ObjectRemovedEvent(obj))

def delete(container, name, docommit=True):
    obj = container.get(name)
    if obj is None:
        print('*** Object', name, 'not found!')
        return
    notifyRemoved(obj)
    del container[name]
    if docommit:
        commit()

def rename(container, old, new, docommit=True):
    obj = container.get(old)
    if obj is None:
        print('*** Object', old, 'not found!')
        return
    renamer = IContainerItemRenamer(container)
    if new != old:
        try:
            renamer.renameItem(old, new)
        except DuplicationError:
            print('*** Object', new, 'already exists!')
    # container[new] = obj
    # notifyAdded(obj)
    notifyModification(obj)
    if docommit:
        commit()

def move(source, target, name):
    obj = source.get(name)
    if obj is None:
        print('*** Object', name, 'not found!')
        return
    #notifyRemoved(obj)
    #del source[name]
    target[name] = obj
    #notifyAdded(obj)
    notifyModification(obj)
    commit()

def get(container, obj):
    if isinstance(obj, str):
        name = obj
        obj = container.get(name)
        if obj is None:
            print('*** Object', name, 'not found!')
            return None
    return adapted(obj)

# startup, loop, finish...

def startup(msg, **kw):
    print('***', msg)
    step = kw.pop('step', 10)
    return Jeep(count=0, step=step, message=msg, **kw)

def update(fct, obj, info):
    info.count += 1
    start = info.get('start')
    if start and info.count < start:
        return
    if info.count % info.step == 0:
        try:
            objInfo = obj.__name__
        except:
            try:
                objInfo = obj.context.__name__
            except:
                objInfo = obj
        print('*** Processing object # %i: %s' % (info.count, objInfo))
        if info.get('updated'):
            print('*** updated: %i.' % info.updated)
        if info.get('errors'):
            print('*** errors: %i.' % info.error)
        commit()
    return fct(obj, info)

def finish(info):
    print('*** count: %i.' % info.count)
    if info.get('updated'):
        print('*** updated: %i.' % info.updated)
    if info.get('errors'):
        print('*** errors: %i.' % info.error)
    commit()

def stop_condition(info):
    stop = info.get('stop')
    return stop is not None and info.count > stop

def loop(message, objects, fct, **kw):
    def _fct(obj, info):
        params = info.get('fctparams', {})
        fct(obj, info, **params)
    info = startup(message, **kw)
    for obj in objects:
        update(_fct, obj, info)
        if stop_condition(info):
            break
    finish(info)


# indexing

def reindex_objects(objs, **kw):
    catalog = getCatalog(objs[0])
    def do_reindex(obj, info):
        util.reindex(obj, catalog)
    loop('reindex %s objects' % len(objs), objs, do_reindex, **kw)

def reindex_all(root, step=1000, **kw):
    catalog = getCatalog(root)
    def _updateObj(params, info):
        uid, obj = params
        for index in catalog.values():
            index.index_doc(uid, obj)
    info = startup('Indexing all objects', step=step, **kw)
    for uid, obj in catalog._visitSublocations():
        update(_updateObj, (uid, obj), info)
    finish(info)


# some common repair tasks

def get_type_instances(name):
    return sc.concepts[name].getChildren([sc.hasType])

def notify_modification(c, info):
    notifyModification(c)

def update_type_instances(**kw):
    objs = get_type_instances(kw.pop('type'))
    loop('Notify Type Instances', objs, notify_modification, **kw)

def update_type_instances_title_from_adapted(**kw):
    def update_type_title_from_adapted(c, info):
        c.title = adapted(c).title
        notifyModification(c)
    objs = get_type_instances(kw.pop('type'))
    loop('Update Type Instances Title', objs, update_type_title_from_adapted, **kw)

def removeRecords(container, **kw):
    """Remove records from container selected by the criteria given."""
    def remove(obj, info):
        notifyRemoved(obj)
        del container[obj.__name__]
    info = startup('Remove records', **kw)
    date = kw.pop('date', None)
    if date:
        kw['timeFromTo'] = (
            date2TimeStamp(strptime(date + ' 00:00:00')),
            date2TimeStamp(strptime(date + ' 23:59:59')))
    loop('Remove records', container.query(**kw), remove, **kw)


# helper functions and classes

def login(principal):
    endInteraction()
    newInteraction(Participation(principal))


class TestRequest(BaseTestRequest):

    basePrincipal = BaseTestRequest.principal

    @Lazy
    def principal(self):
        interaction = getInteraction()
        if interaction is not None:
            parts = interaction.participations
            if parts:
                prin = parts[0].principal
                if prin is not None:
                    return prin
        return self.basePrincipal


class Participation(object):
    """ Dummy Participation class for testing.
    """

    interaction = None

    def __init__(self, principal):
        self.principal = principal


