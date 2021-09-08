"""This module contains the `AwayTeam` class.

"""

from types import MappingProxyType
from legendscli.utils.pool import PoolChangeEvent
from legendscli.classes.collections import Roster

class AwayTeam(Roster):
    """A subclass of Roster that can have only 4 members.

    Attributes:
        registeredSSC (tuple of SelaStatCal, int): A 2-tuple whose first
            item is the Sela stat calculator with which the away team is
            registered, and whose second item is the ID number used by
            the Sela stat calculator to identify the away team. This
            attribute is set by the `register` method of a SelaStatCalc
            instance.
    """

    def __init__(self):
        """Create an AwayTeam object by calling superclass constructor
        without a `max` argument.

        """
        Roster.__init__(self)
        self._blind = True
        self.noPrint = ['SSC', 'SSCid', 'selaStats']
        self.collapse = ['selaSurvivalProbs']
        self.registeredSSC = None
        self._weights = {}
        self._selaStats = None

    @property
    def summonRatesNonCommon(self):
        """(override) Summon rates not implements for away teams."""
        return None

    @property
    def summonRatesAll(self):
        """(override) Summon rates not implements for away teams."""
        return None

    @property
    def weights(self):
        """dict of str:float: A dictionary mapping character names to a
        weight (positive number) that represents the relative importance
        of the character to the away team.
        """
        return MappingProxyType(self._weights)

    @property
    def SSC(self):
        """The Sela stat calculator the away team is registered with. A
        shortcut for self.registeredSSC[0].
        """
        if self.registeredSSC is not None:
            return self.registeredSSC[0]
        else:
            return None

    @property
    def SSCid(self):
        """The away team's id number with the Sela stat calculator. A
        shortcut for self.registeredSSC[1].
        """
        if self.registeredSSC is not None:
            return self.registeredSSC[1]
        else:
            return None

    @property
    def selaStats(self):
        """dict of str:obj: A dictionary of stats related to surviving
        Sela's first attack. Computed by the registered Sela stat
        calculator. See the `SelaStatCalc` class for more details.
        """
        if self.SSC is not None:
            return MappingProxyType({
                'survivalProbs': self.SSC.survivalProbs[self.SSCid],
                'numSurvivors': self.SSC.numSurvivors[self.SSCid]
            })
        else:
            return None

    @property
    def selaSurvivalProbs(self):
        """A shortcut for self.selaStats['survivalProbs']."""
        if self.selaStats is None:
            return None
        else:
            return self.selaStats['survivalProbs']

    @property
    def selaNumSurvivors(self):
        """A shortcut for self.selaStats['numSurvivors']."""
        if self.selaStats is None:
            return None
        else:
            return self.selaStats['numSurvivors']

    def summonAll(self):
        """(override) Overrides the `summonAll` method to raise an
        attribute error.

        Raises:
            NotImplementedError: If called.

        """
        raise NotImplementedError(
            'cannot use the `summonAll` method with an `AwayTeam` object'
        )

    def addItem(self, char, weight=1):
        """(override) Adds the given characters to the away team in the
        given slot.

        Args:
            char (Character): The character to add to the away team.
            weight (float): The weight to assign to the added character.
                If not provided, the character is given weight 1. 

        Raises:
            ValueError: If the given character matches the name of a
                character on the away team.

        """
        if char.name in self.items:
            raise ValueError('character already on away team')
        self._weights[char.name] = weight
        Roster.addItem(self, char)

    def add(self, *chars):
        """Add multiple characters with default weight 1.

        Args:
            chars (list of Character): The characters to add.

        """
        for char in chars:
            self.addItem(char)

    def removeItem(self, char):
        """(override) Overrides the `remove` method to also remove the
        character's weight.

        """
        del self._weights[char.name]
        Roster.removeItem(self, char)

    def setWeight(self, char, weight):
        """Assigns the given weight to the given character and notifies
        subscribers that the away team has changed.

        Args:
            char (Character): The character whose weight to set.
            weight (float): The weight to assign to the given character.

        """
        self._weights[char.name] = weight
        self.onChange.notify(PoolChangeEvent(self))

    def onSSCChange(self, event):
        """This method is called when the Sela stat calculator with
        which the away team is registered changes.

        """
        pass

