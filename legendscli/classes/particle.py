"""This module contains the `Particle` class.

"""

from types import MappingProxyType
from legendscli.utils.pool import Item
from legendscli.utils.eventhandler import EventHandler
from legendscli.constants import (
    PART_STAT_UNLOCKED, PART_STAT_VALUES, PART_EFFECTS, RARITIES
)
from legendscli.functions import powerDelta

class Particle(Item):
    """A particle in Star Trek: Legends.

    Attributes:
        equippedOn (tuple of Character, int): The character and 0-based
            slot in which the particle is equipped.
        onChange (EventHandler): When the particle stats change, this
            event handler sends the Particle object to subscribers.

    """

    def __init__(self, type_, *statNames, level=5, rarity='Legendary'):
        """Creates a particle with the given type, stats, level, and
        rarity. Sets the `equippedOn` attribute to `None` and adds an
        event handler for tracking changes to the particle's stats.

        Args:
            type_ (str): The type of the particle. Should be a key in
                PART_EFFECTS.
            statNames (list of str): The stats to place on the particle.
            level (int): The level of the particle.
            rarity (str): The rarity of the particle.

        Raises:
            ValueError: If either the type or rarity is not recognized.

        """
        Item.__init__(self)
        if type_ not in PART_EFFECTS:
            raise ValueError('particle type not recognized')
        if rarity not in RARITIES:
            raise ValueError('rarity not recognized')
        self.equippedOn = None
        self._type_ = type_
        self._rarity = rarity
        self._effType = PART_EFFECTS[self.type_]['effect']
        self._effMult = (
            PART_EFFECTS[self.type_]['baseVal']
            + self.tier * PART_EFFECTS[self.type_]['incrPerTier']
        )
        self._statList = []
        self.level = level
        self.addStat(*statNames)

    @property
    def type_(self):
        """str: The type of the particle."""
        return self._type_

    @property
    def level(self):
        """int: The level of the particle. When the level changes, stat
        values are recalculated. Attempting to set the level to anything
        other than an integer between 1 and 5 raises a `ValueError`.
        """
        return self._level

    @level.setter
    def level(self, value):
        if type(value) != type(0) or value < 1 or value > 5:
            raise ValueError('level must be an integer between 1 and 5')
        self._level = value
        self.makeStats()

    @property
    def rarity(self):
        """str: The rarity of the particle."""
        return self._rarity

    @property
    def tier(self):
        """int: The tier of the particle."""
        return RARITIES.index(self.rarity)

    @property
    def numStats(self):
        """int: The number of unlocked stats on the particle."""
        return PART_STAT_UNLOCKED[self.rarity][self.level - 1]

    @property
    def effType(self):
        """str: The effect related to the particle's type"""
        return self._effType

    @property
    def effMult(self):
        """float: The multiplier associated with the particle's
        effect.
        """
        return self._effMult

    @property
    def statList(self):
        """tuple of str: The names of stats on the particle."""
        return tuple(self._statList)

    @property
    def stats(self):
        """dict of str:float: A dictionary mapping stat names to the
        values of those stats on the particle.
        """
        return self._stats

    def addStat(self, *statNames, silent=False, noCap=False):
        """Adds the given stats to the particle then triggers the stat
        values to be recalculated.

        Args:
            statNames (list of str): The stats to add to the particle.
            silent (bool): Set to True to silently block stats beyond
                the level/rarity cap, without error or interruption.
            noCap (bool): Set to True to allow adding four stats to any
                particle, regardless of rarity and level.

        Raises:
            ValueError: If a given stat name is not recognized or is
                already on the particle, or if there is not enough room
                on the particle.

        """
        if not noCap and len(statNames) + len(self._statList) > self.numStats:
            if silent:
                return
            else:
                raise ValueError('too many stats')
        for name in statNames:
            if name not in PART_STAT_VALUES:
                raise ValueError("stat name '" + name + "' unrecognized")
            if name in self._statList:
                raise ValueError("'" + name + "' already on particle")
            self._statList.append(name)
            self._stats = None
        self.makeStats()

    def makeStats(self):
        """Calculates the stats of the particle and stores them for
        retrieval by the `stats` property. Then notifies subscribers
        that the stats have changed.

        """
        stats = {statName: 0 for statName in PART_STAT_VALUES}
        for statName in self.statList:
            stats[statName] = (
                PART_STAT_VALUES[statName][self.rarity][self.level - 1]
            )
        stats['power'] = powerDelta(stats)
        self._stats = MappingProxyType(stats)
        self.onChange.notify(self)

    def copy(self):
        """Copies itself.

        Returns:
            Particle: The copy of the calling particle, with the same
                type, stats, level, and rarity.

        """
        return Particle(
            self.type_, *self._statList, level=self.level, rarity=self.rarity
        )

    def equals(self, particle, weak=False):
        """Checks if the calling particle is equivalent to the given
        particle. Particles are equivalent if they're the same type,
        rarity, and level, and have the same stats in the same order.
        Only unlocked stats are checked.

        Args:
            particle (Particle): The particle to check.
            weak (bool): Set to True to check for weak equality, which
                means the stats do not have to be in the same order.

        Returns:
            bool: True if the particles are equivalent.

        """
        if (self.type_ != particle.type_
            or self.rarity != particle.rarity
            or self.level != particle.level
        ):
            return False
        selfList = list(self.statList[:self.numStats])
        partList = list(particle.statList[:self.numStats])
        if weak:
            selfList.sort()
            partList.sort()
        return selfList == partList


    def shortName(self):
        """(override) Overrides the `shortName` method to include the
        particle's type, rarity, and level.

        """
        return (
            'Particle: ' + self.type_
            + ', ' + self.rarity
            + ' Level ' + str(self.level)
        )


