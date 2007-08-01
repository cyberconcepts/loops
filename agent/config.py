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
Management of agent configuration.

$Id$
"""

import os
from zope.interface import implements
from loops.agent.interfaces import IConfigurator


class Configurator(object):

    implements(IConfigurator)

    def __init__(self, *sections, **kw):
        for s in sections:
            setattr(self, s, ConfigSection())
        self.filename = kw.get('filename')

    def load(self, p=None, filename=None):
        if p is None:
            fn = self.getConfigFile(filename)
            if fn is not None:
                f = open(fn, 'r')
                p = f.read()
                f.close()
        if p is None:
            return
        exec p in self.__dict__

    def save(self, filename=None):
        fn = self.getConfigFile(filename)
        if fn is None:
            fn = self.getDefaultConfigFile()
        if fn is not None:
            f = open(fn, 'w')
            f.write(repr(self))
            f.close()

    def __repr__(self):
        result = []
        for name, value in self.__dict__.items():
            if isinstance(value, ConfigSection):
                value.collect(name, result)
        return '\n'.join(sorted(result))

    def getConfigFile(self, filename=None):
        if filename is not None:
            self.filename = filename
        if self.filename is None:
            fn = self.getDefaultConfigFile()
            if os.path.isfile(fn):
                self.filename = fn
        return self.filename

    def getDefaultConfigFile(self):
        return os.path.join(os.path.expanduser('~'), '.loops.agent.cfg')


class ConfigSection(list):

    def __getattr__(self, attr):
        value = ConfigSection()
        setattr(self, attr, value)
        return value

    def __getitem__(self, idx):
        while idx >= len(self):
            self.append(ConfigSection())
        return list.__getitem__(self, idx)

    def setdefault(self, attr, value):
        if attr not in self.__dict__:
            setattr(self, attr, value)
            return value
        return getattr(self, attr)

    def collect(self, ident, result):
        for idx, element in enumerate(self):
            element.collect('%s[%i]' % (ident, idx), result)
        for name, value in self.__dict__.items():
            if isinstance(value, ConfigSection):
                value.collect('%s.%s' % (ident, name), result)
            elif isinstance(value, (str, int)):
                result.append('%s.%s = %s' % (ident, name, repr(value)))

