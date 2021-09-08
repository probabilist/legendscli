"""This module contains the `Skill` class.

"""

from types import MappingProxyType
from legendscli.utils.printable import Printable
from legendscli.constants import SKILL, SKILL_IDS

class Skill(Printable):
    """A skill in Star Trek: Legends.

    """

    # a template of properties for a Skill object
    _template = {
        "skillID": None,
        "level": 0,
        "cooldown": None,
        "startingCooldown": None,
        "numTargets": None,
        "targetType": None,
        "targetState": None,
        "effects": [
            {
                "effect": None,
                "fraction": None
            }
        ],
        "isSingleTarget": None,
        "isMultiRandom": None,
        "isAOE": None
    }

    def __init__(self, skillID, level=0):
        """Creates a skill with the given skill ID and level.

        Args:
            skillID (str): The skill ID of the skill to be created.
            level (int): The level of the skill to be created.

        Raises:
            ValueError: If given skill ID is not associated with an
                enabled character in the game assets.
        """
        Printable.__init__(self)
        if skillID not in SKILL_IDS:
            raise ValueError('skill ID ' + repr(skillID) + ' not recognized')
        self._skillDict = Skill._template.copy()
        self._skillDict['skillID'] = skillID
        if level != 0:
            self.level = level

    @property
    def skillID(self):
        """str: The skill ID used to look up the skill in the game
        assets."""
        return self._skillDict['skillID']

    @property
    def level(self):
        """int: The skill's level. If set to 0, all attributes are set
        to `None` except for `level` and `skillID`. Otherwise,
        attributes are copied from the game assets using the skill ID
        and level. If the combination of the skill's ID and the given
        level cannot be found in the game assets, raises a
        `ValueError`."""
        return self._skillDict['level']

    @level.setter
    def level(self, value):
        skillID = self._skillDict['skillID']
        if value == 0:
            self._skillDict = Skill._template.copy()
        else:
            key = (
                'GSSkillKey(id = "' + skillID
                + '", level = "' + str(value) + '")'
            )
            if key not in SKILL:
                raise ValueError('level not recognized')
            self._skillDict = SKILL[key]
        self._skillDict['skillID'] = skillID

    @property
    def cooldown(self):
        """int: The skill's cooldown."""
        return self._skillDict['cooldown']
    
    @property
    def startingCooldown(self):
        """int: The skill's starting cooldown."""
        return self._skillDict['startingCooldown']

    @property
    def numTargets(self):
        """int: The number of characters the skill targets."""
        return self._skillDict['numTargets']

    @property
    def targetType(self):
        """str: The type of characters the skill targets."""
        return self._skillDict['targetType']

    @property
    def targetState(self):
        """str: The state of characters the skill targets."""
        return self._skillDict['targetState']

    @property
    def effects(self):
        """tuple of (dict of str:obj): A tuple of skill effects. Each
        effect is represented by a dictionary with two keys, 'effect'
        and 'fraction'. The value of 'effect' is a string describing the
        effect. The value of fraction is a float that measures the
        strength of the effect."""
        return tuple(
            MappingProxyType(effect) for effect in self._skillDict['effects']
        )

    @property
    def isSingleTarget(self):
        """bool: True if the skill is a single target skill."""
        return self._skillDict['isSingleTarget']

    @property
    def isMultiRandom(self):
        """bool: True if the skill is a multi random skill."""
        return self._skillDict['isMultiRandom']

    @property
    def isAOE(self):
        """bool: True if the skill is an AOE skill."""
        return self._skillDict['isAOE']

    def shortName(self):
        """(override) Overrides the `shortName` method to include the
        skill's skill ID and level.

        """
        return (
            'Skill: ' + self.skillID
            + ', ' + ' Level ' + str(self.level)
        )

