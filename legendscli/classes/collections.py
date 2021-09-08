"""Classes that represent pools of game objects.

"""

from types import MappingProxyType
from itertools import combinations
from legendscli.utils.pool import Pool, PoolChangeEvent
from legendscli.constants import (
    PART_STAT_VALUES, SUMMONABLE, SUMMON_POOL, ENABLED, PLAYABLE
)
from legendscli.classes.particle import Particle
from legendscli.classes.character import Character

__all__ = ['Armory', 'Laboratory', 'Roster']

class Armory(Pool):
    """A pool of gear pieces.

    """

    def __init__(self):
        Pool.__init__(self)
        self.collapse = ['items']

class Laboratory(Pool):
    """A pool of particles.

    """

    def __init__(self):
        Pool.__init__(self)
        self.collapse = ['items']

    def fill(self):
        """Adds 1120 particles to the laboratory. For each of the 70
        possible stat combinations (excluding 'Resolve'), adds eight
        Nexus Field particles with that combination and eight Undo
        Damage particles with that combination. All added particles are
        Legendary, Level 5.

        """
        statNames = list(PART_STAT_VALUES)
        statNames.remove('Resolve')
        for combo in combinations(statNames, 4):
            for j in range(8):
                self.addItem(Particle('Nexus Field', *combo), safe=False)
                self.addItem(Particle('Undo Damage', *combo), safe=False)

class Roster(Pool):
    """A pool of characters.

    """

    def __init__(self, maxed=False, allChars=False):
        """Creates the Roster object.

        Args:
            maxed (bool): Set to True to create a full roster of all
                summonable characters with max rank, level, skills, and
                gear.
            allChars (bool): If `maxed` is True, set `all` to True to
                summon all characters from PLAYABLE, rather than
                ENABLED.

        """
        Pool.__init__(self)
        self.collapse = ['idFromName', 'items']
        self._ignoreCharChange = False  # set to True to prevent calls
                                        # to the `onCharChange` method
        if maxed:
            self.summonAll(allChars)
            self.maxRankAll()
            self.maxLevelAll()
            if not allChars:
                self.maxSkillsAll()
            self.maxGearAll()
        self.makeStats()

    @property
    def idFromName(self):
        """dict of str:int: A dictionary mapping names of characters in
        the roster to their internal ID number.
        """
        return {char.name: idNum for idNum, char in self._items.items()}

    @property
    def power(self):
        """float: The total power of all characters in the roster."""
        return self._power

    @property
    def xp(self):
        """int: The total xp of all characters in the roster."""
        return self._xp

    @property
    def summonRatesNonCommon(self):
        """dict of str:float: A dictionary mapping the names of summon
        pools to the expected number of non-common tokens per 150 orbs.
        """
        return MappingProxyType(self._summonRatesNonCommon)

    @property
    def summonRatesAll(self):
        """dict of str:float: A dictionary mapping the names of summon
        pools to the expected number of tokens per 150 orbs.
        """
        return MappingProxyType(self._summonRatesAll)

    def addItem(self, char, update=True, safe=True):
        """(override) Adds a character to the roster, then subscribes to
        its `onChange` and `onCalcChange` event handlers, calls for the
        roster stats to be recalculated, and notifies subscribers of the
        change.

        Args:
            char (Character): The Character object to add to the roster.
            update (bool): Set to false to avoid recalculating the
                roster stats and notifying subscribers of the change.

        Raises:
            ValueError: If the name of the given character matches the
                name of a character in the roster.

        """
        Pool.addItem(self, char, safe=safe)
        char.onCalcChange.subscribe(self.onItemChange)
        if update:
            self.makeStats()
            self.onChange.notify(PoolChangeEvent(self, char, 'new'))

    def removeItem(self, char, update=True):
        """(override) Unsubscribes from the given character's `onChange`
        and `onCalcChange` event handlers, then removes it from the
        roster. Fails silently if the given character is not in the
        roster. Finally, calls for the roster stats to be recalculated.

        Args:
            char (Character): The Character object to remove from the
                roster.
            update (bool): Set to false to avoid recalculating the
                roster stats and notifying subscribers of the change.

        """
        if char not in self._items.values():
            return
        char.onChange.unsubscribe(self.onItemChange)
        char.onCalcChange.unsubscribe(self.onItemChange)
        del self._items[char.inPool[1]]
        if update:
            self.makeStats()
            self.onChange.notify(PoolChangeEvent(self, char, 'removed'))

    def get(self, *charNames):
        """Returns character objects from the roster with the given
        names. Returns `None` if there is no such character.

        Args:
            charNames (list of str): The names of the character to get.

        Returns:
            tuple of Character: The character objects with the given
                names.

        """
        chars = []
        for charName in charNames:
            for char in self.items.values():
                if char.name == charName:
                    chars.append(char)
                    break
            else:
                chars.append(None)
        return chars[0] if len(chars) == 1 else tuple(chars)

    def addEffStatCalc(self, effStatCalc):
        """Registers every character in the roster with the given
        effective stat calculator.

        Does not check for duplicates in the effective stat calculator.
        Can produce unexpected behavior if any characters in the roster
        are already registered with the given stat calculator.

        Args:
            effStatCalc (EffStatCalc): The effective stat calculator
                that all characters are registered with.

        """
        for char in self.items.values():
            effStatCalc.register(char, safe=False)

    def addSelaStatCalc(self, selaStatCalc):
        """Registers every character in the roster with the given
        Sela stat calculator.

        Does not check for duplicates in the Sela stat calculator. Can
        produce unexpected behavior if any characters in the roster are
        already registered with the given stat calculator.

        Args:
            selaStatCalc (SelaStatCalc): The Sela stat calculator that
                all characters are registered with.

        """
        for char in self.items.values():
            selaStatCalc.registerChar(char, safe=False)

    def summonAll(self, allChars=False):
        """For each name in `ENABLED` that is not already in the roster,
        creates and adds a new Rank 1, Level 1 character of that name,
        and sets its attack skill to Level 1. Characters are added with
        the `update` flag set to false, to suppress stat recalculations
        and subscriber notifications with each summon. At the end, stats
        are recalculated once and subscribers are notified of a global
        change.

        Args:
            allChars (bool): Set to True to summon all characters from
                PLAYABLE instead of ENABLED.

        """
        chars = PLAYABLE if allChars else ENABLED
        rosterNames = [char.name for char in self._items.values()]
        for name in chars:
            if name not in rosterNames:
                char = Character(name, 1, 1)
                for skill in char.skills:
                    if skill.skillID[-6:] == 'attack':
                        skill.level = 1
                        break
                self.addItem(char, update=False)
        self.makeStats()
        self.onChange.notify(PoolChangeEvent(self))

    def maxRankAll(self):
        """Set all characters in the roster to Rank 9. Ignores change
        notifications from Character objects during the ranking, to
        suppress stat recalculations and subscriber notifications with
        each rank-up. At the end, stats are recalculated once and
        subscribers are notified of a global change.

        """
        self._ignoreCharChange = True
        for char in self._items.values():
            char.rank = 9
        self._ignoreCharChange = False
        self.makeStats()
        self.onChange.notify(PoolChangeEvent(self))

    def maxLevelAll(self):
        """Set all characters in the roster to Level 99. Ignores change
        notifications from Character objects during the leveling, to
        suppress stat recalculations and subscriber notifications with
        each level-up. At the end, stats are recalculated once and
        subscribers are notified of a global change.

        """
        self._ignoreCharChange = True
        for char in self._items.values():
            char.level = 99
        self._ignoreCharChange = False
        self.makeStats()
        self.onChange.notify(PoolChangeEvent(self))

    def maxSkillsAll(self):
        """For each character in the roster, sets all skills to Level 2.

        """
        for char in self._items.values():
            char.maxSkills()

    def maxGearAll(self):
        """For each character in the roster, adds max-level, non-unique
        gear to every slot, replacing whatever gear is already there.
        Ignores change notifications from Character objects during the
        gearing, to suppress stat recalculations and subscriber
        notifications with each gear piece. At the end, stats are
        recalculated once and subscribers are notified of a global
        change.

        """
        self._ignoreCharChange = True
        for char in self._items.values():
            char.addMaxGear()
        self._ignoreCharChange = False
        self.makeStats()
        self.onChange.notify(PoolChangeEvent(self))

    def addParticleAll(self, particle, slot=None):
        """For each character in the roster, equips a copy of the given
        particle into the given slot, removing whatever particle was
        already there. If no slot is provided, two copies of the given
        particle will be placed on each character.

        Ignores change notifications from Character objects while adding
        particles, to suppress stat recalculations and subscriber
        notifications with each particle. At the end, stats are
        recalculated once and subscribers are notified of a global
        change.        

        Args:
            particle (Particle): The particle to copy.
            slot (int): The slot to place the copy. If not provided,
                both slots get a copy.

        """
        slots = [0, 1] if slot is None else [slot]
        self._ignoreCharChange = True
        for char in self._items.values():
            for index in slots:
                char.addParticle(particle.copy(), index)
        self._ignoreCharChange = False
        self.makeStats()
        self.onChange.notify(PoolChangeEvent(self))

    def getExpectedTokens(self, poolName='Crew', common=False):
        """Gets the expected number of non-Common tokens per summon for
        the given pool type. Does not count summons for max-rank
        characters, since those return Latinum, not tokens.

        Args:
            poolName (str): Either 'Crew' or a role. Should match a key
                in `SUMMON_POOL`.
            common (bool): Set to True if you want to include Common
                tokens in the calculation.

        Returns:
            float: The expected number of tokens.

        """
        expTokens = 0
        for charName in SUMMONABLE:
            char = self.get(charName)
            if char and char.rank == 9:
                continue
            if not common and SUMMONABLE[charName]['Rarity'] == 'Common':
                continue
            expTokens += 10 * SUMMON_POOL[poolName].get(charName, 0)
        return expTokens

    def onItemChange(self, char):
        """(override) This method is called when the `totalStats`
        property of a character in the roster changes, or when a stat
        calculator with which the character is registered changes. It
        calls for the roster stats to be recalculated, then notifies
        subscribers that the character has changed.

        Args:
            char (Character): The character whose total stats changed.

        """
        if self._ignoreCharChange:
            return
        self.makeStats()
        self.onChange.notify(PoolChangeEvent(self, char, 'changed'))

    def makeStats(self):
        """Computes the total power and xp of all characters in the
        roster, and stores them for retrieval by the relevant
        properties.

        """
        self._power = sum(
            char.power for char in self._items.values()
        )
        self._xp = sum(
            char.xp for char in self._items.values()
        )
        self._summonRatesNonCommon = {}
        self._summonRatesAll = {}
        for poolName in SUMMON_POOL:
            cost = 50 if poolName == 'Crew' else 75
            self._summonRatesNonCommon[poolName] = (
                (150/cost) * self.getExpectedTokens(poolName, common=False)
            )
            self._summonRatesAll[poolName] = (
                (150/cost) * self.getExpectedTokens(poolName, common=True)
            )


