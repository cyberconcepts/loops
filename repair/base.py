#
#  Copyright (c) 2016 Helmut Merz helmutm@cy55.de
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
Basic stuff for database fixes.
"""

import os

from cybertools.util.date import date2TimeStamp, strptime
from cybertools.util.jeep import Jeep
from loops.common import baseObject
from loops import psu

os.environ['NLS_LANG'] = 'German_Germany.UTF8'


# start, loop, finish...

def startup(msg, **kw):
    print '***', msg
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
        print '*** Processing object # %i: %s.' % (info.count, objInfo)
        if info.get('updated'):
            print '*** updated: %i.' % info.updated
        psu.commit()
    return fct(obj, info)

def finish(info):
    print '*** count: %i.' % info.count
    if info.get('updated'):
        print '*** updated: %i.' % info.updated
    psu.commit()

def stop_condition(info):
    stop = info.get('stop')
    return stop is not None and info.count > stop


# generic loop

def loop(message, objects, fct, **kw):
    def _fct(obj, info):
        params = info.get('fctparams', {})
        fct(obj, **params)
    info = startup(message, **kw)
    for obj in objects:
        update(_fct, obj, info)
        if stop_condition(info):
            break
    finish(info)


# auxiliary functions

def get_type_instances(name):
    return psu.sc.concepts[name].getChildren([psu.sc.hasType])

def notify_modification(c, info):
    psu.notifyModification(c)


# some common repair tasks

def removeRecords(container, **kw):
    """Remove records from container selected by the criteria given."""

    def remove(obj, info):
        psu.notifyRemoved(obj)
        del info.container[obj.__name__]

    info = startup('Remove records', container=container, **kw)
    dateTo = kw.pop('dateTo', None)
    if dateTo:
        timeTo = date2TimeStamp(strptime(dateTo + ' 23:59:59'))
        kw['timeTo'] = timeTo
    date = kw.pop('date', None)
    if date:
        kw['timeFromTo'] = (
            date2TimeStamp(strptime(date + ' 00:00:00')),
            date2TimeStamp(strptime(date + ' 23:59:59')))
    for obj in container.query(**kw):
        update(remove, obj, info)
        if stop_condition(info):
            break
    finish(info)

