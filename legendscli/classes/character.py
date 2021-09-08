"""This module contains the `Character` class.

"""

from types import MappingProxyType
from legendscli.utils.eventhandler import EventHandler
from legendscli.utils.pool import Item
from legendscli.constants import (
    CHARACTER, RARITIES, BASE_STAT, LEVEL, RANK, GEAR_NAMES
)
from legendscli.functions import power
from legendscli.classes.skill import Skill
from legendscli.classes.gearpiece import GearPiece

class Character(Item):
    """A character in Star Trek: Legends. Characters can equip instances
    of other classes, like `GearPiece` and `Particle`. The general
    paradigm for equipping an item is: (1) store information about the
    item, (2) subscribe to any event handlers, (3) store information
    about self on equipped item, (4) have item subscribe to any event
    handlers. The general procedure for unequipping is to reverse these
    steps.

    The `onChange` event handler inherited from the Item supreclass is
    only used when the character's total stats change.
    
    Attributes:
        onCalcChange (EventHandler): This event handler sends the
            character object to subscribers when any of the calculators
            with which the character is registered changes. This
            includes calculator instances of classes such as
            `EffStatCalc` and `SelaStatCalc`.
        skills (tuple of Skill): The character's skills. Initialized at
            level 0.

    """

    def __init__(self, name, rank=9, level=None, xp=None):
        """First calls the superclass constructor, then sets the
        `noPrint` attribute to ignore properties that are simply
        aliases. Then creates a character of the given name, rank, and
        level. Accepts either a level or a total xp amount, but not
        both. If neither is specified, it defaults to Level 99. Also
        adds an event handler for tracking changes to the character's
        total stats.

        Args:
            name (str): The name of the character to be created.
            rank (int): The rank of the character to be created.
            level (int): The level of the character to be created.
            rank (int): The xp of the character to be created.

        Raises:
            ValueError: If `name` does not match a key in CHARACTER.
            AttributeError: If trying to set both level and xp.

        """
        Item.__init__(self)
        self.noPrint = [
            'ESC', 'ESCid', 'SSC', 'SSCid',
            'health', 'attack', 'defense', 'tech', 'speed',
            'cc', 'cd', 'gc', 'gd', 'resolve', 'power'
        ]
        self.collapse = ['gearStats', 'nakedStats', 'particleStats']
        if name not in CHARACTER:
            raise ValueError("name '" + name + "' not recognized")
        self._registeredESC = None
        self._registeredSSC = None
        self.onCalcChange = EventHandler()
        self._name = name
        self._rank = rank
        self.skills = tuple(
            Skill(skillID) for skillID in CHARACTER[self.name]['SkillIDs']
        )
        self._gear = [None] * 4
        self._gearStats = {}
        self._particles = [None] * 2
        self._particleStats = {}
        self._particleEffects = {}
        if level is not None and xp is not None:
            raise AttributeError("can't assign both level and xp")
        elif xp is None:
            if level is None:
                level = 99
            self.level = level
        else:
            self.xp = xp
        self.makeGearStats()
        self.makeParticleStats()

    @property
    def name(self):
        """str: The name of the character."""
        return self._name

    @property
    def role(self):
        """str: The role of the character."""
        return CHARACTER[self.name]['Role']

    @property
    def rarity(self):
        """str: The rarity of the character."""
        return CHARACTER[self.name]['Rarity']

    @property
    def tier(self):
        """str: The tier of the character."""
        return RARITIES.index(self.rarity)

    @property
    def rank(self):
        """int: The rank of the character. Changing its value causes the
        character's naked stats to be recalculated. Raises a value error
        when changing rank to anything other than an integer between 1
        and 9.
        """
        return self._rank

    @rank.setter
    def rank(self, value):
        if type(value) != type(0) or value < 1 or value > 9:
            raise ValueError('rank must be an integer between 1 and 9')
        self._rank = value
        self.makeNakedStats()

    @property
    def xp(self):
        """int: The total XP the character has earned. Changing its
        value calls the `makeLevelFromXP` method, which in turn triggers
        a recalculation of the character's naked stats. Raises a
        `ValueError` if changed to anything other than a nonnegative
        integer.
        """
        return self._xp

    @xp.setter
    def xp(self, value):
        if type(value) != type(0) or value < 0:
            raise ValueError('xp must be a nonnegative integer')
        self._xp = value
        self.makeLevelFromXP()

    @property
    def level(self):
        """int: The level of the character. Changing its value calls the
        `makeXPFromLevel` method, which in turn triggers a recalculation
        of the character's naked stats. Raises a `ValueError` if changed
        to anything other than an integer between 1 and 99.
        """
        return self._level

    @level.setter
    def level(self, value):
        if type(value) != type(0) or value < 1 or value > 99:
            raise ValueError('level must be an integer between 1 and 99')
        self._level = value
        self.makeXPFromLevel()

    @property
    def gear(self):
        """tuple of GearPiece: The gear pieces equipped on the
        character.
        """
        return tuple(self._gear)

    @property
    def particles(self):
        return tuple(self._particles)

    @property
    def nakedStats(self):
        """dict of str:float: A dictionary mapping stat names to their
        values. Considers only the character itself, disregarding gear
        and particles. Includes all stats in `BASE_STAT` as well as
        'power'.
        """
        return self._nakedStats

    @property
    def gearStats(self):
        """dict of str:int: The sum of the stats properties of the
        equipped gear pieces.
        """
        return self._gearStats

    @property
    def particleStats(self):
        """dict of str:int: The sum of the stats properties of the
        equipped particles.
        """
        return self._particleStats

    @property
    def particleEffects(self):
        """dict of str:float: A dictionary mapping particle effect names
        to the total multiplier of that effect for the equipped
        particles.
        """
        return self._particleEffects

    @property
    def totalStats(self):
        """dict of str:float: A dictionary mapping stat names to their
        values. Considers the character, gear, and particles. Includes
        all stats in `BASE_STAT` as well as 'power'.
        """
        return self._totalStats

    @property
    def derivedStats(self):
        """dict of str:float: A dictionary of stats that are derived
        from more fundamental stats.

        Keys:
            xpToMax: The amount of XP needed to reach Level 99.
            missingSkillLvls: The number of missing skill levels on the
                character.
            missingGearLvls: The number of missing gear levels on the
                character.
            missingHighGearLvls: The number of missing gear levels on
                the character, not counting the first 10.

        """
        return self._derivedStats

    @property
    def registeredESC(self):
        """tuple of EffStatCal, int: A 2-tuple whose first item is the
        effective stat calculator with which the character is
        registered, and whose second item is the ID number used by the
        effective stat calculator to identify the character. This
        attribute is set by the `register` method of an EffStatCalc
        instance. When this attribute changes, the `onCalcChange` event
        handler notifies subscribers.
        """
        return self._registeredESC

    @registeredESC.setter
    def registeredESC(self, value):
        self._registeredESC = value
        self.onCalcChange.notify(self)

    @property
    def ESC(self):
        """The effective stat calculator the character is registered
        with. A shortcut for self.registeredESC[0].
        """
        if self.registeredESC is not None:
            return self.registeredESC[0]
        else:
            return None

    @property
    def ESCid(self):
        """The character's id number with the effective stat calculator.
        A shortcut for self.registeredESC[1].
        """
        if self.registeredESC is not None:
            return self.registeredESC[1]
        else:
            return None

    @property
    def effStats(self):
        """dict of str:float: A dictionary of stats that denote
        averages. Computed by the registered effective stat calculator.
        See the `EffStatCalc` class for more details.
        """
        if self.ESC is not None:
            return MappingProxyType({
                'effHealth': self.ESC.effHealth[self.ESCid],
                'effAttDmg': self.ESC.effAttDmg[self.ESCid],
                'effTechDmg': self.ESC.effTechDmg[self.ESCid]
            })
        else:
            return None

    @property
    def registeredSSC(self):
        """tuple of SelaStatCal, int: A 2-tuple whose first item is the
        Sela stat calculator with which the character is registered, and
        whose second item is the ID number used by the Sela stat
        calculator to identify the character. This attribute is set by
        the `register` method of a SelaStatCalc instance. When this
        attribute changes, the `onCalcChange` event handler notifies
        subscribers.
        """
        return self._registeredSSC

    @registeredSSC.setter
    def registeredSSC(self, value):
        self._registeredSSC = value
        self.onCalcChange.notify(self)

    @property
    def SSC(self):
        """The Sela stat calculator the character is registered with. A
        shortcut for self.registeredSSC[0].
        """
        if self.registeredSSC is not None:
            return self.registeredSSC[0]
        else:
            return None

    @property
    def SSCid(self):
        """The character's id number with the Sela stat calculator. A
        shortcut for self.registeredSSC[1].
        """
        if self.registeredSSC is not None:
            return self.registeredSSC[1]
        else:
            return None

    @property
    def selaStats(self):
        """dict of str:float: A dictionary of stats related to surviving
        Sela's first attack. Computed by the registered Sela stat
        calculator. See the `SelaStatCalc` class for more details.
        """
        if self.SSC is not None:
            return MappingProxyType({
                'survSelaCover': self.SSC.survSelaCover[self.SSCid],
                'survSelaNoCover': self.SSC.survSelaNoCover[self.SSCid],
                'survSelaCrit': self.SSC.survSelaCrit[self.SSCid],
                'survSelaTwoHits': self.SSC.survSelaTwoHits[self.SSCid]
            })
        else:
            return None

    @property
    def health(self):
        """The total health stat of the character. A shortcut for
        `totalStats['Health']`.
        """
        return self.totalStats['Health']

    @property
    def attack(self):
        """The total attack stat of the character. A shortcut for
        `totalStats['Attack']`.
        """
        return self.totalStats['Attack']

    @property
    def defense(self):
        """The total defense stat of the character. A shortcut for
        `totalStats['Defense']`.
        """
        return self.totalStats['Defense']

    @property
    def tech(self):
        """The total tech stat of the character. A shortcut for
        `totalStats['Tech']`.
        """
        return self.totalStats['Tech']

    @property
    def speed(self):
        """The total speed stat of the character. A shortcut for
        `totalStats['Speed']`.
        """
        return self.totalStats['Speed']

    @property
    def cc(self):
        """The total crit chance stat of the character. A shortcut for
        `totalStats['CritChance']`.
        """
        return self.totalStats['CritChance']

    @property
    def cd(self):
        """The total crit damage stat of the character. A shortcut for
        `totalStats['CritDamage']`.
        """
        return self.totalStats['CritDamage']

    @property
    def gc(self):
        """The total glancing chance stat of the character. A shortcut
        for `totalStats['GlancingChance']`.
        """
        return self.totalStats['GlancingChance']

    @property
    def gd(self):
        """The total glancing damage stat of the character. A shortcut
        for `totalStats['GlancingDamage']`.
        """
        return self.totalStats['GlancingDamage']

    @property
    def resolve(self):
        """The total resolve stat of the character. A shortcut for
        `totalStats['Resolve']`.
        """
        return self.totalStats['Resolve']

    @property
    def power(self):
        """The total power of the character. A shortcut for
        `totalStats['power']`.
        """
        return self.totalStats['power']

    def makeLevelFromXP(self):
        """Calculates the level of the character from its XP and stores
        it for retrieval by the `level` property. Then calls for
        recalculation of the character's naked stats.
        """
        for level in reversed(range(100)):
            xpNeeded = LEVEL[self.rarity + '_' + str(level)]['Experience']
            if self.xp >= xpNeeded:
                self._level = level
                break
        self.makeNakedStats()

    def makeXPFromLevel(self):
        """Calculates the minimum XP of the character from its level and
        stores it for retrieval by the `xp` property. Then calls for
        recalculation of the character's naked stats.
        """
        self._xp = LEVEL[self.rarity + '_' + str(self.level)]['Experience']
        self.makeNakedStats()

    def maxSkills(self):
        """Sets all skills to Level 2.

        """
        for skill in self.skills:
            skill.level = 2

    def addGear(self, gearPiece, replace=False):
        """Equips a `GearPiece` object. Then calls for recalculation of
        the character's gear stats.

        Args:
            gearPiece (GearPiece): The gear piece to equip.
            replace (bool): Set to true to replace gear that is already
                equipped.

        Raises:
            ValueError: If (1) gear is already equipped on a character,
                (2) gear is meant for a different role, (3) the gear
                level is too high for the rarity of the character, or
                (4) `replace` is `False` and a gear piece is already
                equipped in that slot.

        """
        if gearPiece.equippedOn is not None:
            raise ValueError(
                "gear is equipped by '" + gearPiece.equippedOn.name + "'"
            )
        if gearPiece.role is not None and gearPiece.role != self.role:
            raise ValueError('gear has wrong role')
        if gearPiece.level > 5 * self.tier + 5:
            raise ValueError('gear level is too high')
        if self._gear[gearPiece.slot] is not None:
            if not replace:
                raise ValueError('gear slot is occupied')
            else:
                self._gear[gearPiece.slot].equippedOn = None
                self._gear[gearPiece.slot].onChange.unsubscribe(
                    self.makeGearStats
                )

        self._gear[gearPiece.slot] = gearPiece
        gearPiece.onChange.subscribe(self.makeGearStats)

        gearPiece.equippedOn = self

        self.makeGearStats()

    def addMaxGear(self):
        """Add max-level, non-unique gear to every slot, replacing
        whatever gear is already there.

        """
        for name in GEAR_NAMES:
            self.addGear(
                GearPiece(name, self.role, 5, self.rarity),
                True
            )

    def removeParticle(self, slot):
        """Removes the particle from the given slot. Does nothing if the
        slot is empty. Then calls for recalculation of the character's
        particle stats.

        Args:
            slot (int): The 0-based index of the slot from which to
                remove a particle.

        """
        if self._particles[slot] is None:
            return
        self._particles[slot].equippedOn = None
        self._particles[slot].onChange.unsubscribe(self.makeParticleStats)
        self._particles[slot] = None
        self.makeParticleStats()

    def addParticle(self, particle, slot=None):
        """Unequips the given particle from whatever character it is on.
        Unequips whatever particle is in the given slot. Then equips the
        given particle into the given slot. Finally, calls for
        recalculation of the character's particle stats.

        Args:
            particle (Particle): The particle to equip.
            slot (int): The 0-based index of the slot into which to
                place the particle. If not provided, the particle is
                added to slot 0, and then a copy of the particle is
                added to slot 1.

        """
        if slot is None:
            self.addParticle(particle, 0)
            self.addParticle(particle.copy(), 1)
            return
        if particle.equippedOn is not None:
            otherChar = particle.equippedOn[0]
            otherSlot = particle.equippedOn[1]
            otherChar.removeParticle(otherSlot)
        self.removeParticle(slot)
        self._particles[slot] = particle
        particle.onChange.subscribe(self.makeParticleStats)
        particle.equippedOn = (self, slot)
        self.makeParticleStats()

    def makeNakedStats(self):
        """Calculates the naked stats of the character and stores them
        for retrieval by the `nakedStats` property. Then calls for
        recalculation of the character's total stats.

        """
        stats = {}
        for statName in BASE_STAT:
            m = BASE_STAT[statName]['MinValue']
            M = BASE_STAT[statName]['MaxValue']
            t = CHARACTER[self.name][statName]
            baseStat = m + t * (M - m)

            try:
                levelMod = LEVEL[self.rarity + '_' + str(self.level)][
                        statName + 'Modifier'
                    ]
                rankMod = RANK[self.rarity + '_' + str(self.rank)][
                        statName + 'Modifier'
                    ]
            except KeyError:
                levelMod = 1
                rankMod = 1

            nakedStat = baseStat * levelMod * rankMod
            stats[statName] = nakedStat
        stats['power'] = power(stats)
        self._nakedStats = MappingProxyType(stats)
        self.makeTotalStats()

    def makeGearStats(self, event=None):
        """Calculates the total gear stats of the character and stores
        them for retrieval by the `nakedStats` property. Then calls for
        recalculation of the character's total stats.

        Args:
            event (obj): The event sent by an event handler. Not used by
                the method.

        """
        stats = {
            'Health': 0, 'Attack': 0, 'Defense': 0, 'Tech': 0, 'power': 0
        }
        for gear in self.gear:
            if gear is None:
                continue
            for statName, statVal in gear.stats.items():
                stats[statName] += statVal
        self._gearStats = MappingProxyType(stats)
        self.makeTotalStats()

    def makeParticleStats(self, event=None):
        """Calculates the total particle stats of the character and
        stores them for retrieval by the `nakedStats` property. Then
        calls for recalculation of the character's total stats.

        Args:
            event (obj): The event sent by an event handler. Not used by
                the method.

        """
        stats = {statName: 0 for statName in self.nakedStats}
        effects = {'attBonus': 0, 'shield': 0, 'regen': 0}
        del stats['Speed']
        for part in self.particles:
            if part is not None:
                for statName, statVal in part.stats.items():
                    stats[statName] += statVal
                if part.effType:
                    effects[part.effType] += part.effMult
        self._particleStats = MappingProxyType(stats)
        self._particleEffects = MappingProxyType(effects)
        self.makeTotalStats()

    def makeTotalStats(self):
        """Calculates the total stats of the character and stores them
        for retrieval by the `totalStats` property. Then calls for
        recalculation of the derived stats and notifies subscribers that
        the stats have changed. Finally calls for retrieval of the
        effective stats and Sela stats from the registered stat
        calculators.

        """
        stats = {
            statName: self.nakedStats.get(statName, 0)
                + self.gearStats.get(statName, 0)
                + self.particleStats.get(statName, 0)
            for statName in self.nakedStats
        }
        self._totalStats = MappingProxyType(stats)
        self.makeDerivedStats()
        self.onChange.notify(self)

    def makeDerivedStats(self):
        """Calculates the derived stats of the character and stores them
        for retrieval by the `derivedStats` property.

        """
        xpToMax = max(
            LEVEL[self.rarity + '_99']['Experience'] - self.xp,
            0
        )
        missingSLs = 2 * len(self.skills) - sum(
            s.level for s in self.skills
        )
        missingGLs = 4 * (5 + 5 * self.tier) - sum(
            (g.level if g else 0) for g in self.gear
        )
        if self.tier > 1:
            missingHGLs = 4 * (5 + 5 * self.tier) - sum(
                max((g.level if g else 0), 10) for g in self.gear
            )
        else:
            missingHGLs = 0
        self._derivedStats = MappingProxyType({
            'xpToMax': xpToMax,
            'missingSkillLvls': missingSLs,
            'missingGearLvls': missingGLs,
            'missingHighGearLvls': missingHGLs
        })

    def onESCChange(self, event):
        """When the effective stat calculator with which the character
        is registered changes, the `onCalcChange` event handler notifies
        subscribers.

        """
        self.onCalcChange.notify(self)

    def onSSCChange(self, event):
        """When the Sela stat calculator with which the character is
        registered changes, the `onCalcChange` event handler notifies
        subscribers.
        
        """
        self.onCalcChange.notify(self)

    def shortName(self):
        """(override) Overrides the `shortName` method to include the
        character's name, rank, and level.

        """
        return (
            'Character: ' + self.name
            + ', Rank ' + str(self.rank)
            + ', Level ' + str(self.level)
        )

