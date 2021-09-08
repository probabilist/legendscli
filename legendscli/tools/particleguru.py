"""This module contains the ParticleGuru and related classes.

ParticleGuru is an optimization engine that suggests particles to equip.

"""

class Filter():
    """A Wrapper around a function mapping a particle to a Boolean.

    Attributes:
        name (str): The name of the filter.

    """

    def __init__(self, name, func):
        """Creates a filter with the given name and function.

        Args:
            name (str): The name to assign to the filter.
            func (func): Should be a function mapping a particle to a
                Boolean that is False if the particle is to be filtered
                out.

        """
        self.name = name
        self._func = func

    def __call__(self, particle):
        """Calls the wrapped function."""
        return self._func(particle)

class Stat():
    """Wrapper around a function mapping a character to an int or float.

    Attributes:
        name (str): The name of the stat.
        probability (bool): True if the stat represents a probability.

    """

    def __init__(self, name, func, prob=False):
        """Creates a stat with the given name and function.

        Args:
            name (str): The name to assign to the stat.
            func (func): Should be a function mapping a character to an
                int or float that is the value of the stat for that
                character.

        """
        self.name = name
        self._func = func
        self.probability = prob

    def __call__(self, char):
        """Calls the wrapped function."""
        return self._func(char)

class ParticleImpact():
    """Used in measuring the impact of a particle on a character.

    Comparison methods are implemented. They should only be used between
    impacts whose `stats` dictionaries have the same keys in the same
    order. Using them otherwise can produce unexpected behavior.

    Attributes:
        particle (Particle): The particle making the impact.
        char (Character): The character it impacts.
        slot (int): The slot where it is equipped.
        stats (dict of str:(float or int)): The stats measuring the
            impact. A dictionary mapping stat names to values, ordered
            from most important to least important.

    """

    def __init__(self):
        self.particle = None
        self.char = None
        self.slot = None
        self.stats = {}

    def __lt__(self, other):
        return list(self.stats.values()) < list(other.stats.values())

    def __le__(self, other):
        return list(self.stats.values()) <= list(other.stats.values())

    def __gt__(self, other):
        return list(self.stats.values()) > list(other.stats.values())

    def __ge__(self, other):
        return list(self.stats.values()) >= list(other.stats.values())

    def __eq__(self, other):
        return list(self.stats.values()) == list(other.stats.values())

    def __ne__(self, other):
        return list(self.stats.values()) != list(other.stats.values())

    def dominates(self, other):
        """Returns true if the calling impact is not equal to the other
        impact, and each of its stats is greater than or equal to the
        corresponding stat of the other.

        """
        if self == other:
            return False
        for statName in self.stats:
            if self.stats[statName] < other.stats[statName]:
                return False
        return True

class ParticleGuru():
    """An engine that recommends particles to equip.

    Args:
        saveSlot (SaveSlot): The SaveSlot object associated with the
            particle guru.
        locked (list of int): A list of particle IDs from the associated
            save slot.
        filters (dict of str:(list of Filter)): A dictionary mapping
            character names to lists of filters. Has a 'global' key that
            is applied for all characters.
        stats (dict of str:(list of Stat)): A dictionary mapping
            character names to lists of stats. Has a 'default' key that
            is used when a character name does not appear in the
            dictionary.

    """

    def __init__(self, saveSlot):
        """Instantiates the particle guru.

        Args:
            saveslot (SaveSlot): The save slot to associate with the
                particle guru.

        """
        self.saveSlot = saveSlot
        self.locked = []
        self.filters = {'global': []}
        self.stats = {'default': []}

    @property
    def count(self):
        """The number of particles that pass the global filters."""
        parts = [
            part for part in self.saveSlot.laboratory.items.values()
            if (all(filt(part) for filt in self.filters['global']))
        ]
        return len(parts)

    def getStats(self, charName):
        """Looks up the list of stats corresponding to the given
        character, using the defaults if necessary. Then computes and
        returns a dictionary mapping stat names to their values for this
        character.

        Args:
            charName (str): The name of the character whose stats will
                be computed.

        Returns:
            dict of str:(int or float): The dictionary mapping stat
                names to their values.

        Raises:
            ValueError: If no stats are found.

        """
        statList = self.stats.get(charName, self.stats['default'])
        if len(statList) == 0:
            raise ValueError('no stats set')
        return {
            stat.name: stat(self.saveSlot.roster.get(charName))
            for stat in statList
        }

    def suggest(self, charID, slot, allParts=False, callback=None):
        """Recommends particles to equip on the given character in the
        given particle slot. Only unlocked particles that pass all the
        global filters and any filters associated with the character's
        name will be considered and returned for recommendation. Any
        unlocked particles already equipped on the character will be
        ignored.

        More specifically, this method does the following. Raises an
        error if the given slot contains a locked particle. Temporarily
        removes the particle from the given slot and locks the other
        particle. Tries on a copy of every unlocked particle in the save
        slot that passes the filters, records their impacts in a
        dictionary indexed by particle IDs, then puts back the
        character's original particles.

        The recorded impacts are sorted from greatest to least. If
        `allParts` is False, they are then filtered to remove particles
        that are dominated by another particle. Finally, the dictionary
        of impacts is returned.

        Args:
            charID (str): The ID of the character in the associated save
                slot.
            slot (int): The particle slot to consider.
            allParts (bool): If False, dominated particles are not
                returned.
            callback (func): A function for displaying a progress
                indicator. Should take two arguments. The first is the
                length of the iteration. The second is the current step
                in the iteration.

        Returns:
            dict of int:Impact: A dictionary mapping particle IDs to
                their impacts, sorted from greatest to least.

        Raises:
            ValueError: If the given slot contains a locked particle.

        """
        char = self.saveSlot.roster.items[charID]
        origParts = char.particles

        # pause SSC away team updates while moving particles
        if char.SSC is not None:
            char.SSC.pauseTeamUpdates = True

        # check for locked particle
        if (
            origParts[slot] is not None
            and origParts[slot].inPool[1] in self.locked
        ):
            raise ValueError('suggestion slot contains a locked particle')

        # remove original particle, lock other particle
        if origParts[slot] is not None:
            char.removeParticle(slot)
        otherPart = char.particles[1 - slot]
        unlock = False
        if otherPart is not None:
            otherPartID = otherPart.inPool[1]
            if otherPartID not in self.locked:
                self.locked.append(otherPartID)
                unlock = True

        # get filtered part IDs
        filters = self.filters['global'] + self.filters.get(char.name, [])
        partIDs = [
            partID for partID, part in self.saveSlot.laboratory.items.items()
            if (
                all(filt(part) for filt in filters)
                and partID not in self.locked
            )
        ]

        # get particle impacts
        impacts = {}
        steps = len(partIDs)
        step = 0
        for partID in partIDs:
            step += 1
            if callback is not None:
                callback(steps, step)
            part = self.saveSlot.laboratory.items[partID].copy()
            char.addParticle(part, slot)
            impacts[partID] = ParticleImpact()
            impacts[partID].particle = part
            impacts[partID].char = char
            impacts[partID].slot = slot
            impacts[partID].stats = self.getStats(char.name)
        char.removeParticle(slot)   # remove last copied particle

        # unlock other particle, put back original particle
        if unlock:
            self.locked.remove(otherPartID)
        if origParts[slot] is not None:
            char.addParticle(origParts[slot], slot)

        # unpause SSC away team updates
        if char.SSC is not None:
            char.SSC.pauseTeamUpdates = False

        # sort impacts
        impacts = dict(sorted(
            impacts.items(), key=lambda item:item[1], reverse=True
        ))

        # filter out dominated impacts
        if allParts:
            return impacts
        filteredImpacts = {}
        for partID, impact in impacts.items():
            if (filteredImpacts and any(
                prevImpact.dominates(impact)
                for prevImpact in filteredImpacts.values()
            )):
                continue
            filteredImpacts[partID] = impact
        return filteredImpacts





