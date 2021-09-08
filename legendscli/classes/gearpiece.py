"""This module contains the `GearPiece` class.

"""

from types import MappingProxyType
from legendscli.utils.pool import Item
from legendscli.utils.eventhandler import EventHandler
from legendscli.constants import GEAR, GEAR_LEVEL, RARITIES
from legendscli.functions import powerDelta

class GearPiece(Item):
    """A piece of gear in Star Trek: Legends.

    Attributes:
        equippedOn (Character): The character on which the piece is
            equipped.
        onChange (EventHandler): When the gear level changes, this event
            handler sends the GearPiece object to subscribers.

    """

    def __init__(self, name, role=None, level=1, rarity=None):
        """Creates a gear piece with the given name, role, level, and
        rarity. Sets the `equippedOn` attribute to `None` and adds an
        event handler for tracking changes to the gear stats.

        Args:
            name (str): The name of the gear piece. For non-unique gear,
                the names in use are 'Starfleet PADD', 'Type II Phaser',
                'Tricorder', and 'Communicator'. (This is as of June 19,
                2021).
            role (str): The role the gear piece is meant for.
            level (int): The level of the gear piece. If a rarity
                argument is included, level should be an integer between
                1 and 5 and match the level displayed in game.
                Otherwise, level should be an integer between 1 and 25
                that incorporates the rarity. For example, a Level 15
                gear piece displays in game as a Level 5 Very Rare gear
                piece.
            rarity (str): The rarity of the gear piece.

        Raises:
            ValueError: If the name and role combination cannot be found
                in the game assets.

        """
        Item.__init__(self)
        key = name
        if role:
            key += ' 2256 ' + role
        if key not in GEAR:
            raise ValueError('item not recognized')
        self._key = key
        self._name = name
        self._role = role
        self.equippedOn = None
        self.onChange = EventHandler()
        if rarity is not None:
            level += 5 * RARITIES.index(rarity)
        self.level = level

    @property
    def key(self):
        """str: A key used to look up the gear in the `GEAR`
        dictionary.
        """
        return self._key

    @property
    def name(self):
        """str: The name of the gear piece."""
        return self._name

    @property
    def role(self):
        """str: The role that the gear is meant for."""
        return self._role

    @property
    def level(self):
        """int: The gear level. Rarity is incorporated into level.
        For example, a Level 15 gear piece displays in game as a Level 5
        Very Rare gear piece. If the gear is equipped, its level cannot
        be changed to a value exceeding that determined by the rarity of
        the character on which it is equipped. Attempting to set the
        level to an invalid value raises a `ValueError`. Changing the
        level causes the gear stats to be recalculated.
        """
        return self._level

    @level.setter
    def level(self, value):
        if type(value) != type(0) or value < 1:
            raise ValueError('level must be a positive integer')
        if self.equippedOn is not None:
            maxLevel = 5 * self.equippedOn.tier + 5
            if value > maxLevel:
                raise ValueError('level cannot exceed ' + str(maxLevel))
        self._level = value
        self.makeStats()

    @property
    def tier(self):
        """int: The tier (0-based index of rarity) of the gear piece."""
        return (self.level - 1)//5

    @property
    def displayLevel(self):
        """int: The level of the gear piece as it is displayed in game
        (i.e. an integer between 1 and 5).
        """
        dlvl = self.level - 5 * self.tier
        return dlvl

    @property
    def rarity(self):
        """str: The rarity of the gear piece."""
        return RARITIES[self.tier]

    @property
    def slot(self):
        """int: The 0-based slot into which the gear piece must be
        equipped.
        """
        return GEAR[self.key]['m_Slot']

    @property
    def stats(self):
        """dict of str:float: A dictionary mapping stat names to the
        value of that stat on the gear piece. Includes only 'Health',
        'Attack', 'Defense', 'Tech', and 'power'. Stores the stats and
        only recalculates when needed.
        """
        return self._stats

    def makeStats(self):
        """Calculates the stats of the gear piece and stores them for
        retrieval by the `stats` property. Then notifies subscribers
        that the stats have changed.
        """
        stats = {
            'Health': 0, 'Attack': 0, 'Defense': 0, 'Tech': 0
        }
        gearLevelKey = '[' + self.key + ', ' + str(self.level) + ']'
        numStats = GEAR_LEVEL[gearLevelKey]['m_StatBrancheCount']
        for i in range(numStats):
            statDict = GEAR[self.key]['m_Stats'][i]
            statName = statDict['m_Type']
            statBase = statDict['m_BaseValue']
            statIncr = statDict['m_IncreaseValue']
            statVal = statBase + (self.level - 10 * i) * statIncr
            stats[statName] += statVal
        stats['power'] = powerDelta(stats)
        self._stats = MappingProxyType(stats)
        self.onChange.notify(self)

    def shortName(self):
        """(override) Overrides the `shortName` method to include the
        gear piece's name, role, rarity, and level.

        """
        return (
            'GearPiece: ' + self.key
            + ', ' + self.rarity
            + ' Level ' + str(self.displayLevel)
        )


