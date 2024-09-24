# loops.schema.field

""" Field and field instance classes for grids.
"""

import json
from zope import component
from zope.browserpage import ViewPageTemplateFile
from zope.cachedescriptors.property import Lazy
from zope.component import adapts
import zope.schema
from zope.traversing.api import getName

from cybertools.composer.schema.factory import createField
from cybertools.composer.schema.field import FieldInstance, ListFieldInstance
from cybertools.composer.schema.interfaces import IField, IFieldInstance
from cybertools.composer.schema.interfaces import fieldTypes, undefined
from cybertools.util.format import toStr, toUnicode
from loops.common import baseObject
from loops import util


relation_macros = ViewPageTemplateFile('relation_macros.pt')


class BaseRelationFieldInstance(object):

    @Lazy
    def selection_view(self):
        return (getattr(self.context, 'selection_view', None) or
                                            'listConceptsForComboBox.js')

    @Lazy
    def typesParams(self):
        result = []
        types = self.context.target_types
        for t in types:
            result.append('searchType=loops:concept:%s' % t)
        if result:
            return '?' + '&'.join(result)
        return ''

    def getPresetTargets(self, view):
        if view.adapted.__is_dummy__:
            # only for object in creation
            target = view.virtualTargetObject
            if getName(target.conceptType) in self.context.target_types:
                return [dict(title=target.title, uid=util.getUidForObject(target))]
        return []


class RelationSetFieldInstance(ListFieldInstance, BaseRelationFieldInstance):

    def marshall(self, value):
        if value is None:
            return []
        return [dict(title=v.title, uid=util.getUidForObject(baseObject(v)))
                for v in value]

    def display(self, value):
        if value is None:
            return []
        nodeView = self.clientInstance.view.nodeView
        return [dict(url=nodeView.getUrlForTarget(baseObject(v)),
                     label=v.title) for v in value]

    def unmarshall(self, value):
        return [util.getObjectForUid(v) for v in value]

    def getRenderer(self, name):
        return relation_macros.macros.get(name)


class RelationFieldInstance(FieldInstance, BaseRelationFieldInstance):

    def marshall(self, value):
        if value:
            return dict(title=value.title,
                        uid=util.getUidForObject(baseObject(value)))

    def display(self, value):
        if value:
            nodeView = self.clientInstance.view.nodeView
            return dict(url=nodeView.getUrlForTarget(baseObject(value)),
                        label=value.title)
        return u''

    def unmarshall(self, value):
        return util.getObjectForUid(value)

    def getRenderer(self, name):
        return relation_macros.macros[name]

