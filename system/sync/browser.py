#
#  Copyright (c) 2010 Helmut Merz helmutm@cy55.de
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
view class(es) for import/export.

$Id$
"""

import os
import time
from zope import component
from zope.interface import Interface, implements
from zope.app.pagetemplate.viewpagetemplatefile import ViewPageTemplateFile
from zope.cachedescriptors.property import Lazy
from zope.traversing.api import getName, getPath

from cybertools.browser.form import FormController
from cybertools.util.date import str2timeStamp, formatTimeStamp
from loops.browser.concept import ConceptView
from loops.external.base import Extractor
from loops.external.interfaces import IWriter
from loops import util


control_macros = ViewPageTemplateFile('control.pt')


class SyncChanges(ConceptView):
    """ View for controlling the transfer of changes from a loops site
        to another one.
    """

    @Lazy
    def macro(self):
        return control_macros.macros['main']

    @Lazy
    def changed(self):
        return (self.request.get('changed_since') or
                formatTimeStamp(self.lastSyncTimeStamp))

    @Lazy
    def lastSyncTime(self):
        if self.lastSyncTimeStamp is None:
            return u'-'
        return formatTimeStamp(self.lastSyncTimeStamp)

    @Lazy
    def lastSyncTimeStamp(self):
        return None


class ChangesSave(FormController):

    @Lazy
    def baseDirectory(self):
        return util.getVarDirectory(self.request)

    @Lazy
    def sitePath(self):
        return getPath(self.view.virtualTargetObject)[1:].replace('/', '_')

    @Lazy
    def exportDirectory(self):
        return os.path.join(self.baseDirectory, 'export', self.sitePath)

    @Lazy
    def targetView(self):
        return self.view.virtualTarget

    def update(self):
        typeIds = self.targetView.options('types')
        types = [self.view.conceptManager[t] for t in typeIds]
        since = self.request.get('changed_since')
        changed = since and str2timeStamp(since) or self.targetView.lastSyncTimeStamp
        extractor = Extractor(self.view.loopsRoot, self.exportDirectory)
        elements = extractor.extractChanges(changed, types)
        writer = component.getUtility(IWriter)
        f = open(os.path.join(self.exportDirectory, '_changes.dmp'), 'w')
        writer.write(elements, f)
        f.close()
        return True


class ChangesSync(ChangesSave):

    pass
