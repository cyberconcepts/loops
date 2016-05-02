# psu - paster shell utilities
# use this from (e.g.):
#
#   bin/paster shell deploy.ini
#
# then:
#
#   from loops import psu
#   psu.setup(root)
#   obj = psu.byuid('578457950')
#

from transaction import commit, abort
from zope.app.authentication.principalfolder import Principal
from zope.app.component.hooks import setSite
from zope.app.container.contained import ObjectAddedEvent, ObjectRemovedEvent
from zope.cachedescriptors.property import Lazy
from zope.catalog.interfaces import ICatalog
from zope import component
from zope.event import notify
from zope.lifecycleevent import ObjectCreatedEvent, ObjectModifiedEvent
from zope.publisher.browser import TestRequest as BaseTestRequest
from zope.security.management import getInteraction, newInteraction, endInteraction
from zope.interface import Interface

from cybertools.util.jeep import Jeep
from loops.common import adapted, baseObject
from loops.util import getObjectForUid, getUidForObject
#from xxx import config


sc = Jeep()     # shortcuts


def setup(root):
    global sm, smdefault, intids, pau, sc
    setSite(root)
    sm = component.getSiteManager(root)
    smdefault = sm['default']
    intids = smdefault['IntIds']
    pau = smdefault['PluggableAuthentication']
    #user = getattr(config, 'shell_user', 'zope.manager')
    #password = (getattr(config, 'shell_pw', None) or
    #            raw_input('Enter manager password: '))
    user = 'zope.manager'
    password = raw_input('Enter manager password: ')
    login(Principal(user, password, u'Manager'))


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

def delete(container, name):
    obj = container.get(name)
    if obj is None:
        print '*** Object', name, 'not found!'
        return
    notifyRemoved(obj)
    del container[name]
    commit()

def rename(container, old, new):
    obj = container.get(old)
    if obj is None:
        print '*** Object', old, 'not found!'
        return
    container[new] = obj
    #notifyAdded(obj)
    notifyModification(obj)
    commit()

def move(source, target, name):
    obj = source.get(name)
    if obj is None:
        print '*** Object', name, 'not found!'
        return
    #notifyRemoved(obj)
    #del source[name]
    target[name] = obj
    #notifyAdded(obj)
    notifyModification(obj)
    commit()

def get(container, obj):
    if isinstance(obj, basestring):
        name = obj
        obj = container.get(name)
        if obj is None:
            print '*** Object', name, 'not found!'
            return None
    return adapted(obj)

# catalog / indexing

def getCatalog(context):
    context = baseObject(context)
    for cat in component.getAllUtilitiesRegisteredFor(ICatalog, context=context):
        return cat
    print '*** No catalog found!'

def reindex(obj, catalog=None):
    obj = baseObject(obj)
    if catalog is None:
        catalog = getCatalog(obj)
    if catalog is not None:
        catalog.index_doc(int(getUidForObject(obj)), obj)


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

