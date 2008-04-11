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
Adapters and others classes for analyzing resources.

$Id$
"""

from zope.cachedescriptors.property import Lazy
from zope import component
from zope.component import adapts
from zope.traversing.api import getName, getParent

from cybertools.meta.config import Options
from cybertools.meta.namespace import Executor, ExecutionError
from cybertools.typology.interfaces import IType
from loops.interfaces import ILoops


class LoopsOptions(Options):

    adapts(ILoops)

    builtins = Options.builtins + ('True', 'False')
    True, False = True, False

    def __init__(self, context, *args, **kw):
        self.context = context
        super(LoopsOptions, self).__init__(*args, **kw)
        self.loadContextOptions()

    def parseContextOptions(self):
        def result():
            for opt in  self.context.options:
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
            raise ExecutionError('\n' + result)

    #def __getitem__(self, key):
    #    opt = self.baseOptions.get(key)
    #    return opt
