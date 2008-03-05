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
Adapter implementations for export, import, ...

Obsolete, replaced by functionality in loops.external.base and other modules

$Id$
"""

from zope.interface import implements, Interface
from zope.app import zapi
from zope.component import adapts

from loops.interfaces import IViewManager
from loops.view import Node


# import/export interfaces (for adapters)

class IExternalContentSource(Interface):
    """ Provides content from an external source.
    """

    def getData():
        """ Retrieve content from the external source; return a sequence of
            dictionaries in a format like this:
            [{'name': ..., 'title': ..., 'body':... }, ...],
        """


class ILoader(Interface):
    """ Inserts data provided by an IExternalContentSource object into the
        database.
    """

    def load(data):
        """ Create objects as defined by the data given; this is a sequence
            as described for IExternalContentSource.getContent().
        """


class IExporter(Interface):
    """ Extracts data and in a format usable by ILoader.

        Optionally dump data to a file.
    """

    def extractData():
        """ Return a data object as described for
            IExternalContentSource.getData().
        """

    def dumpData(file):
        """ Dump data returned by extractData() to the file given in a
            format that might be read in by a suitable implementation of
            IExternalContentSource.
        """


# implementations for views/nodes

class NodesLoader(object):

    implements(ILoader)
    adapts(IViewManager)

    def __init__(self, context):
        self.context = context

    def load(self, data):
        for item in data:
            name = item['name']
            path = item['path']
            parent = zapi.traverse(self.context, path)
            if name in parent: # replace existing objects
                del parent[name]
            node = Node()
            node.title = item['title']
            node.description = item['description']
            node.body = item['body']
            node.nodeType = item['nodeType']
            parent[name] = node


class NodesExporter(object):

    implements(IExporter)
    adapts(IViewManager)

    filename = 'loops.dmp'

    def __init__(self, context):
        self.context = context

    def extractData(self):
        data = []
        for child in self.context.values():
            self.extractNodeData(child, '', data)
        return data

    def extractNodeData(self, item, path, data):
        name = zapi.getName(item)
        data.append({
                'name': name,
                'path': path,
                'description': item.description,
                'title': item.title,
                'body': item.body,
                'nodeType': item.nodeType
        })
        path = path and '%s/%s' % (path, name) or name
        for child in item.values():
            self.extractNodeData(child, path, data)


    def dumpData(self, file=None, noclose=False):
        if file is None:
            file = open(self.filename, 'w')
        data = self.extractData()
        text = `data`.replace('},', '},\n').replace('}],', '}],\n')
        file.write(text)
        if not noclose:
            file.close()


class NodesImporter(object):

    implements(IExternalContentSource)
    adapts(IViewManager)

    filename = 'loops.dmp'

    def __init__(self, context):
        self.context = context

    def getData(self, file=None):
        if file is None:
            file = open(self.filename, 'r')
        data = file.read().replace('\n', '')
        file.close()
        return eval(data, {}, {})

