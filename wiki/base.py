#
#  Copyright (c) 2009 Helmut Merz helmutm@cy55.de
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
Wiki base implementation for loops.

$Id$
"""

from zope.traversing.api import getName

from cybertools.wiki.base.wiki import WikiManager, Wiki, WikiPage
from cybertools.wiki.interfaces import ILinkManager

from loops import util


def wikiLinksActive(loops):
    records = loops.getRecordManager()
    if records is not None:
        links = records.get('links')
        return links is not None
    return False


class LoopsWikiManager(WikiManager):
    """ An adapter...
    """

    linkManager = 'tracking'
    nodeProcessors = dict(reference=['loops'])

    def __init__(self, context):
        super(LoopsWikiManager, self).__init__()
        self.context = context

    def getPlugin(self, type, name):
        if type == ILinkManager and name == 'tracking':
            return ILinkManager(self.context.getRecordManager()['links'])
        return super(LoopsWikiManager, self).getPlugin(type, name)

    def getUid(self, obj):
        return util.getUidForObject(obj)

    def getObject(self, uid):
        return util.getObjectForUid(uid)


class LoopsWiki(Wiki):

    def getPage(self, name):
        if name.startswith('.target'):
            return self.getManager().getObject(int(name[7:]))


class LoopsWikiPage(WikiPage):
    """ An adapter...
    """

    def __init__(self, context):
        self.context = context
        self.name = getName(context)

    def getUid(self):
        return util.getUidForObject(self.context)
