"""This module contains the `RosterViewer` class.

"""

from types import MappingProxyType
from legendscli.utils.pool import PoolViewer

class RosterViewer(PoolViewer):
    """A PoolViewer subclass for Roster objects.

    """

    def __init__(self, roster):
        """Creates a RosterViewer object to view the given roster.

        Args:
            roster (Roster): The roster to associate with the viewer.

        """
        PoolViewer.__init__(self, roster)

    def makeDisplayStats(self, char=None, safe=True):
        """(override) Makes a simplified dictionary of character
        statistics, suitable for displaying in a spreadsheet, then
        stores it for retrieval by the `displayStats` property.

        Args:
            char (Character): Uses statistics from this character. If no
                character is provided, the method is run on every
                character in the associated roster.
            safe (bool): Set to False to skip checking for the given
                character in the associated roster.

        Raises:
            ValueError: If the given character is not in the associated
                roster.

        """
        if char is None:
            for char in self._pool.items.values():
                self.makeDisplayStats(char, False)
            return
        if safe and char not in self._pool.items.values():
            raise ValueError('character not in roster')
        attrs = ['name', 'role', 'rarity', 'tier', 'rank', 'level', 'xp']
        displayStats = {attr: getattr(char, attr) for attr in attrs}
        displayStats.update(char.totalStats)
        for i in range(4):
            if char.gear[i]:
                gearLevel = char.gear[i].level
            else:
                gearLevel = 0
            displayStats['gearLevel' + str(i)] = gearLevel
        displayStats.update(char.derivedStats)
        displayStats.update(char.particleEffects)
        effStatNames = ['effHealth', 'effAttDmg', 'effTechDmg']
        for statName in effStatNames:
            displayStats[statName] = (
                char.effStats[statName] if char.effStats else ''
            )
        selaStatNames = [
            'survSelaCover', 'survSelaNoCover',
            'survSelaCrit', 'survSelaTwoHits'
        ]
        for statName in selaStatNames:
            displayStats[statName] = (
                char.selaStats[statName] if char.selaStats else ''
            )
        self._displayStats[char.inPool[1]] = MappingProxyType(displayStats)

