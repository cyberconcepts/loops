# loops.knowledge.qualification.base

""" Controlling qualification activities of persons.

Central part of CCM competence and certification management framework.
"""

from zope.component import adapts
from zope.interface import implementer

from loops.common import AdapterBase
from loops.interfaces import IConcept
from loops.knowledge.qualification.interfaces import ICompetence
from loops.type import TypeInterfaceSourceList


TypeInterfaceSourceList.typeInterfaces += (ICompetence,)


@implementer(ICompetence)
class Competence(AdapterBase):

    _contextAttributes = list(ICompetence)


