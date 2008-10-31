#
#  Copyright (c) 2008 Helmut Merz helmutm@cy55.de
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
Recording changes to loops objects.

$Id$
"""

import os

from zope.app.publication.interfaces import IEndRequestEvent
from zope.interface import Interface
from zope.cachedescriptors.property import Lazy
from zope.component import adapter
from zope.security.proxy import removeSecurityProxy

from cybertools.meta.interfaces import IOptions
from cybertools.tracking.btree import Track, getTimeStamp
from cybertools.tracking.interfaces import ITrack
from cybertools.tracking.logfile import Logger, loggers
from loops.interfaces import ILoopsObject
from loops.organize.party import getPersonForUser
from loops.security.common import getCurrentPrincipal
from loops import util


request_key = 'loops.organize.tracking.access'
loggers_key = 'loops.access'

fields = {
    '001': ('principal', 'node', 'target', 'view', 'params'),
}


def record(request, **kw):
    data = request.annotations.setdefault(request_key, {})
    for k, v in kw.items():
        data[k] = v


@adapter(IEndRequestEvent)
def logAccess(event):
    object = removeSecurityProxy(event.object)
    context = getattr(object, 'context', None)
    if context is None:
        object = getattr(object, 'im_self', None)
        context = getattr(object, 'context', None)
        if context is None:
            return
    if not ILoopsObject.providedBy(context):
        return
    data = event.request.annotations.get(request_key)
    if not data:
        return
    logger = loggers.get(loggers_key)
    if not logger:
        options = IOptions(context.getLoopsRoot())
        logfile = options('organize.tracking.logfile')
        if not logfile:
            return
        path = os.path.join(util.getVarDirectory(), logfile[0])
        logger = loggers[loggers_key] = Logger(loggers_key, path)
    logger.log(marshall(data))


def marshall(data):
    version = '001'
    values = [version]
    for key in fields[version]:
        values.append(data.get(key) or '')
    return ';'.join(values)
