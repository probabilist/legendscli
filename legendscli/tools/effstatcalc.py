"""This module contains the `EffStatCalc` class.

"""

from types import MappingProxyType
from legendscli.utils.printable import Printable
from legendscli.utils.eventhandler import EventHandler

class EffStatCalc(Printable):
    """An Effective Stat Calculator for stats that denote averages.

    Computes effective attack and tech damage, which represent the
    average damage done by a character. Also computes effective health,
    which is the amount of damage, on average, a character can sustain.
    Effective health depends on the enemy's stats as well. Assumptions
    about the enemies stats are stored in the attributes of the
    instance.

    Attributes:
        onChange (EventHandler): When the settings change, this event
            handler sends the EffStatCalc object to subscribers.

    """

    def __init__(self, roster=None):
        """Creates an effective stat calculator with default settings.
        The default settings are hard coded. The defaults for `attDmg`,
        `techDmg`, and `techChance` were approximated by assuming you'd
        receive 0.71 hits from Sela's Surprise Attack, 0.25 hits from
        T'Pol's boot, and 1 hit from Riker's AOE. All three enemies are
        assumed to be maxed with optimal offensive particles and no
        gear. And the number 0.71 is computed assuming you are behind
        cover half the time. Character stats used in computing these
        defaults come from version 1.0.11 of the game.

        Args:
            roster (Roster): If provided, all characters in the roster
                are registered with the effective stat calculator.

        """
        Printable.__init__(self)
        self.collapse = ['effTechDmg', 'effAttDmg', 'effHealth']
        self.onChange = EventHandler()
        self._nextID = 1    # characters register so their stats are
                            # stored for quick retrieval; they are given
                            # an ID when registering
        self._registrants = {}  # a dictionary of registrants by ID
        self._attDmg = 4143
        self._techDmg = 1383
        self._techChance = 0.362
        self._cloak = False
        self._undoDmgRounds = 1.25
        self._firstRound = True
        self._effHealth = {}
        self._effAttDmg = {}
        self._effTechDmg = {}
        if roster is not None:
            roster.addEffStatCalc(self)

    @property
    def attDmg(self):
        """float: The average attack damage delivered by attack hits
        that do not glance. When this property changes, all effective
        stats are recalculated and subscribers are notified of the
        change.
        """
        return self._attDmg

    @attDmg.setter
    def attDmg(self, value):
        self._attDmg = value
        self.refreshAll()
        self.onChange.notify(self)

    @property
    def techDmg(self):
        """float: The average tech damage delivered by attack hits that
        do not glance. When this property changes, all effective stats
        are recalculated and subscribers are notified of the change.
        """
        return self._techDmg

    @techDmg.setter
    def techDmg(self, value):
        self._techDmg = value
        self.refreshAll()
        self.onChange.notify(self)

    @property
    def techChance(self):
        """float: The proportion of all hits that deliver tech damage.
        When this property changes, all effective stats are recalculated
        and subscribers are notified of the change.
        """
        return self._techChance

    @techChance.setter
    def techChance(self, value):
        self._techChance = value
        self.refreshAll()
        self.onChange.notify(self)

    @property
    def cloak(self):
        """bool: Set to True to compute effective health under the
        assumption the character is cloaked. When this property changes,
        all effective stats are recalculated and subscribers are
        notified of the change.
        """
        return self._cloak

    @cloak.setter
    def cloak(self, value):
        self._cloak = value
        self.refreshAll()
        self.onChange.notify(self)

    @property
    def undoDmgRounds(self):
        """float: The expected number of regenerations triggered by any
        Undo Damage particles that might be equipped. Should be a number
        between 0 and 2. When this property changes, all effective stats
        are recalculated and subscribers are notified of the change.
        """
        return self._undoDmgRounds

    @undoDmgRounds.setter
    def undoDmgRounds(self, value):
        self._undoDmgRounds = value
        self.refreshAll()
        self.onChange.notify(self)

    @property
    def firstRound(self):
        """bool: Set to true to take into account any Amplify Force
        particles that may be equipped.
        """
        return self._firstRound

    @firstRound.setter
    def firstRound(self, value):
        self._firstRound = value
        self.refreshAll()
        self.onChange.notify(self)

    @property
    def effHealth(self):
        """dict of int:float: A dictionary mapping character IDs to
        their effective health.

        Effective health takes into account nexus shields, defense, tech
        defense, and glancing damage. (Tech damage is not reduced by
        defense; rather it is reduced by 38% of the target's tech stat.)
        Effective health is characterized as follows. A character whose
        health equals the effective health and who has no nexus shields,
        0 defense, 0 tech defense, and 0% glancing chance would survive,
        on average, the same number of hits as the given character.
        """
        return MappingProxyType(self._effHealth)

    @property
    def effAttDmg(self):
        """dict of int:float: A dictionary mapping character IDs to
        their effective attack damage, which takes into account attack,
        crit chance, and crit damage.
        """
        return MappingProxyType(self._effAttDmg)

    @property
    def effTechDmg(self):
        """dict of int:float: A dictionary mapping character IDs to
        their effective tech damage, which takes into account tech, crit
        chance, and crit damage.
        """
        return MappingProxyType(self._effTechDmg)

    def register(self, char, safe=True):
        """Adds the character to the list of registrants, builds its
        effective stats, and subscribes to its `onChange` event handler.
        Then sets the character's `registeredESC` attribute and has the
        character subscribe to the calling ESC's `onChange` event
        handler.

        Args:
            char (Character): The character registering with the
                effective stat calculator.
            safe (bool): Set to False to avoid checking for duplicates.

        Raises:
            ValueError: If character is already registered.

        """
        if safe and char in self._registrants.values():
            raise ValueError('character already registered')
        self._registrants[self._nextID] = char
        self.makeStats(self._nextID)
        char.onChange.subscribe(self.onCharChange)
        char.registeredESC = (self, self._nextID)
        self.onChange.subscribe(char.onESCChange)
        self._nextID += 1

    def makeEffHealth(self, charID):
        """Computes the effective health of the registered character
        with the given ID and stores it for retrieval by the `effHealth`
        property.

        Args:
            charID (int): The ID of the character, used internally by
                the effective stat calculator.

        Returns:
            float: The effective health of the character.

        """
        char = self._registrants[charID]
        health = char.health
        tech = char.tech
        defense = char.defense
        techDef = 0.38 * tech
        if self.cloak:
            gc = 1
        else:
            gc = char.gc
        gd = char.gd

        shield = char.particleEffects.get('shield', 0)
        regen = char.particleEffects.get('regen', 0)

        healthLike = (
            health
            + shield * tech
            + self.undoDmgRounds * regen * health
        )
        dmg = (
            self.techChance * self.techDmg
            + (1 - self.techChance) * self.attDmg
        )
        reducedAttDmg = (
            (1 - gc) * max(self.attDmg - defense, 1)
            + gc * max((1 - gd) * self.attDmg - defense, 1)
        )
        reducedTechDmg = (
            (1 - gc) * max(self.techDmg - techDef, 1)
            + gc * max((1 - gd) * self.techDmg - techDef, 1)
        )
        reducedDmg = (
            self.techChance * reducedTechDmg
            + (1 - self.techChance) * reducedAttDmg
        )
        numHits = healthLike / reducedDmg

        self._effHealth[charID] = numHits * dmg

    def makeEffAttDmg(self, charID):
        """Computes the effective attack damage of the registered
        character with the given ID and stores it for retrieval by the
        `effAttDmg` property.

        Args:
            charID (int): The ID of the character, used internally by
                the effective stat calculator.

        """
        char = self._registrants[charID]
        attack = char.attack
        if self.firstRound:
            attack *= 1 + char.particleEffects.get('attBonus', 0)
        cc = char.cc
        cd = char.cd

        self._effAttDmg[charID] = attack * (cc * cd + (1 - cc))

    def makeEffTechDmg(self, charID):
        """Computes the effective tech damage of the registered
        character with the given ID and stores it for retrieval by the
        `effTechDmg` property.

        Effective tech damage takes into account attack, crit chance,
        and crit damage.

        Args:
            charID (int): The ID of the character, used internally by
                the effective stat calculator.

        """
        char = self._registrants[charID]
        tech = char.tech
        cc = char.cc
        cd = char.cd

        self._effTechDmg[charID] = tech * (cc * cd + (1 - cc))

    def onCharChange(self, char):
        """This method is called when the `totalStats` property of a
        registered character changes. It calls for the effective stats
        of that character to be recalculated.

        Args:
            char (Character): The character whose total stats changed.

        """
        self.makeStats(char.ESCid)

    def makeStats(self, charID):
        """Rebuilds the effective health, attack, and tech damage of the
        character with the given ID.

        Args:
            charID (int): The ID of the character, used internally by
                the effective stat calculator.

        """
        self.makeEffHealth(charID)
        self.makeEffAttDmg(charID)
        self.makeEffTechDmg(charID)

    def refreshAll(self):
        """Rebuilds the effective health, attack, and tech damage of all
        registered characters.
 
        """
        for charID in self._registrants:
            self.makeStats(charID)




