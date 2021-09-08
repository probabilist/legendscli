"""This module contains the ParticleGuruIPT class and supporting tools.

Attributes:
    ABBREVIATIONS (dict of str:str): Abbreviations used by the
        ParticleGuruIPT class.
    PROBABILITIES (list of str): The names of stats that represent
        probabilities.
    PATH (str): The full, absolute path of this module.

"""

from types import MappingProxyType
from tabulate import tabulate
from os.path import abspath, dirname
from json import load, dump
from math import log
from legendscli.utils.functions import printProgressBar, roundSigFig
from legendscli.utils.printable import Printable
from legendscli.tools.particleguru import ParticleGuru, Filter, Stat

ABBREVIATIONS = {
    'Accelerated Coagulation': 'Coag',
    'Amplify Force': 'Amp',
    'Nexus Field': 'Nexus',
    'Temporal Flux': 'Flux',
    'Undo Damage': 'Undo',
    'CritChance': 'CC',
    'CritDamage': 'CD',
    'GlancingChance': 'GC',
    'GlancingDamage': 'GD'
}

PROBABILITIES = ['CritChance', 'CritDamage', 'GlancingChance',
    'GlancingDamage', 'Resolve', 'survSelaCover', 'survSelaNoCover',
    'survSela'
]

PATH = abspath(dirname(__file__))

def abbr(statName):
    """Returns the given stat name's abbreviation from `ABBREIVATION` or
    the first letter of the stat name if it does not appear.

    Args:
        statName (str): The stat name to abbreviate.

    """
    return ABBREVIATIONS.get(statName, statName[0])

def equippedOnDisplay(equippedOn):
    """Builds and returns a display string for a particle's `equippedOn`
    attribute.

    Returns:
        str: The display string.

    """
    if equippedOn is None:
        display = 'None'
    else:
        char, slot = equippedOn
        display = char.name + ' ' + str(slot)
    return display

def partDisplay(particle, locked=False, sort=True, location=False):
    """Builds and returns a display string for the given particle that
    includes its laboratory ID, type, rarity, level, and stats. The ID
    is preceded by an asterisk if the particle is locked.

    Args:
        particle (Particle): The particle to display.
        locked (bool): Set to True to display the particle as locked.
        sort (bool): Set to False to show stat abbreviations in the
            order that they appear on the particle.

    Returns:
        str: The display string.

    """
    if particle is None:
        return 'None'
    lockStr = '*' if locked else ''
    disp = '[' + lockStr + str(particle.inPool[1]) + '] '
    disp += ABBREVIATIONS[particle.type_]
    disp += ' ' + particle.rarity[0] + str(particle.level)
    statAbbrs = [abbr(statName) for statName in particle.statList]
    if sort:
        statAbbrs.sort()
    disp += ' (' + '/'.join(statAbbrs) + ')'
    if location:
        disp += ' ' + equippedOnDisplay(particle.equippedOn)
    return disp

def printSlot(char, slot, locked=False):
    """Prints a message to the console showing the character name, slot,
    and particle equipped.

    Args:
        char (Character): The character to display.
        slot (int): The slot to display.
        locked (bool): Set to true to display the particle as locked.

    """
    part = char.particles[slot]
    print(
        char.name + ' ' + str(slot) + ': ' + partDisplay(part, locked)
    )

def roundStat(num):
    """Rounds the given number to 2 decimal places, unless the number is
    less than 10, in which case, it rounds it to 4 significant figures.

    Args:
        num (float): The number to round.

    Returns:
        float: The rounded number.

    """
    return roundSigFig(num, 4) if num < 10 else round(num, 2)

class GuruIPT(Printable):
    """Particle Guru Interactive Prompt Tool.

    A wrapper around a ParticleGuru instance for use at a Python
    interactive prompt.

    Attributes:
        chars (list of str): A list of character names to work with,
            listed in priority order.

    """

    def __init__(self, saveSlot):
        """Instantiates an IPT. Creates a ParticleGuru engine associated
        with the given save slot, and embeds it in the IPT. If
        calculators such as effective stat calculators and Sela stat
        calculators are used, every character in the save slot should be
        registered. Unexpected behavior can result if some are
        registered and some are not.

        Args:
            saveSlot (SaveSlot): The save slot to use.

        """
        Printable.__init__(self)
        saveSlot.savePartConfig()
        self._guru = ParticleGuru(saveSlot)
        self.chars = []
        self.addFilter(
            'Leg 5 only',
            lambda particle: (
                particle.rarity == 'Legendary'
                and particle.level == 5
            )
        )
        self._statMenu = {}
        testCharID, testChar = next(iter(
            self._guru.saveSlot.roster.items.items()
        ))
        for statName in testChar.totalStats:
            def func(char, name=statName):
                return char.totalStats[name]
            self._statMenu[statName] = Stat(
                statName, func, statName in PROBABILITIES
            )
        if testChar.registeredESC is not None:
            for statName in testChar.effStats:
                def func(char, name=statName):
                    return char.effStats[name]
                self._statMenu[statName] = Stat(
                    statName, func, statName in PROBABILITIES
                )
        if testChar.registeredSSC is not None:
            for statName in testChar.selaStats:
                def func(char, name=statName):
                    return char.selaStats[name]
                self._statMenu[statName] = Stat(
                    statName, func, statName in PROBABILITIES
                )
            def func(char):
                cover = char.selaStats['survSelaCover']
                noCover = char.selaStats['survSelaNoCover']
                return (cover + noCover)/2
            self._statMenu['survSela'] = Stat(
                'survSela', func, statName in PROBABILITIES
            )

    @property
    def saveSlot(self):
        """SaveSlot: The save slot associated with the embedded guru."""
        return self._guru.saveSlot

    @property
    def filters(self):
        """dict of str:str: A dictionary mapping character names to the
        names of the filters associated with that character.
        """
        return MappingProxyType({
            charName: tuple(filt.name for filt in self._guru.filters[charName])
            for charName in self._guru.filters
        })

    @property
    def statMenu(self):
        """tuple of str: The names of stats available to use. There is a
        custom stat named 'survSela', which is the average of
        'survSelaCover' and 'survSelaNoCover'.
        """
        return tuple(self._statMenu.keys())

    @property
    def stats(self):
        """dict of str:(tuple of str): A dictionary mapping character
        names to the names of the stats associated with that character.
        """
        return MappingProxyType({
            charName: tuple(stat.name for stat in self._guru.stats[charName])
            for charName in self._guru.stats
        })

    @property
    def roster(self):
        """Roster: The roster associated with the embedded guru."""
        return self._guru.saveSlot.roster

    @property
    def laboratory(self):
        """Laboratory: The laboratory associated with the embedded guru.
        """
        return self._guru.saveSlot.laboratory

    @property
    def locked(self):
        """list of int: The particle IDs of the locked particles."""
        return self._guru.locked

    @property
    def count(self):
        """The number of particles that pass the global filters."""
        return self._guru.count

    def addFilter(self, name, func, charName='global'):
        """Adds a filter.

        Args:
            name (str): The name of the filter to add.
            func (func): The filter function. Should map a particle to a
                Boolean.
            charName (str): The name of the character to which the
                filter will apply. If not provided, the filter will be
                global.

        """
        self._guru.filters[charName].append(Filter(name, func))

    def clearFilters(self, charName='global'):
        """Removes all filters associated with the given character. If
        no character is provided, removes all global filters.

        Args:
            charName (str): The name of the character whose filters to
                remove.

        """
        self._guru.filters[charName] = []

    def addStats(self, *statNames, char='default'):
        """Adds the given stats from the stat menu to the given
        character's list of stats. If no character is provided, the
        stats are added to the default stats.

        Args:
            statNames (str): A list of names from the stat menu.
            char (str): The name of the character to add stats to.

        """
        if char not in self._guru.stats:
            self._guru.stats[char] = []
        self._guru.stats[char].extend(
            [self._statMenu[statName] for statName in statNames]
        )

    def copyStats(self, fromChar, *toChars):
        """Copies stats from one character to others.

        Args:
            fromChar (str): The name of the character to copy from.
            toChars (list of str): The names of the characters to copy
                to.

        """
        statNames = self.stats[fromChar]
        for charName in toChars:
            self.addStats(*statNames, char=charName)

    def clearStats(self, charName='default'):
        """Removes all stats associated with the given character. If no
        character is provided, removes all default stats.

        Args:
            charName (str): The name of the character whose stats to
                remove.

        """
        self._guru.stats[charName] = []

    def changeStat(self, index, statName, char='default'):
        """Changes one of the stats for the given character.

        Args:
            index (int): The 0-based index of the stat to change.
            statName (str): The name of the stat to change it to.
            char (str): The name of the character whose stat to change.
                If not provided, a default stat will be changed.

        """
        self._guru.stats[char][index] = self._statMenu[statName]

    def removeStat(self, statName, char='default'):
        """Removes the given stat from the given character. If not
        character is provided, removes the stat from the default list.

        Args:
            statName (str): The name of the stat to remove.
            char (str): The name of the character whose stat to remove.

        """
        self._guru.stats[char].remove(self._statMenu[statName])

    def insertStat(self, index, statName, char='default'):
        """Inserts the given stat to the stats of the given character at
        the given index.

        Args:
            index (int): The index of the stat before which to insert.
            statName (str): The name of the stat to insert.
            char (str): The name of the character whose stats are being
                modified.

        """
        self._guru.stats[char].insert(index, self._statMenu[statName])

    def addRoster(self):
        """Adds all characters from the roster to the `chars` list,
        skipping characters that are already on the list.

        """
        for char in self.roster.items.values():
            if char.name not in self.chars:
                self.chars.append(char.name)

    def printStats(self, charName):
        """Prints a message to the console showing the stats associated
        with the given character in the embedded guru. The stat values
        are labeled with stat names and separated by commas.

        """
        stats = self._guru.getStats(charName)
        print(', '.join([
            statName + ': ' + str(roundStat(statVal))
            for statName, statVal in stats.items()
        ]))

    def equip(self, arg1=None, arg2=None, showOnly=False):
        """Equips the top suggested particles onto the given number of
        characters, starting with the first character in the `chars`
        attribute.

        Args:
            arg1 (str or int): Can be the name of a character to equip
                particles on. Can also be an index of a character in the
                `chars` attribute. If not provided, all characters will
                be equipped.
            arg2 (int): If `arg1` is an int and `arg2` is provided, all
                characters in `chars[arg1:arg2]` will be equipped. If
                `arg1` is an int and `arg2` is not provided, all
                characters in `chars[:arg1]` will be equipped.
            showOnly (bool): If True, the suggestion process is skipped
                so that all that occurs is a display of the character's
                equipped particles.

        """
        if arg1 is None:
            arg1 = 0
            arg2 = len(self.chars)
        elif type(arg1) == type(''):
            arg1 = self.chars.index(arg1)
            arg2 = arg1 + 1
        else:
            if arg2 is None:
                arg2 = arg1
                arg1 = 0
        for charName in self.chars[arg1:arg2]:
            char = self.roster.get(charName)
            charID = char.inPool[1]
            for slot in range(2):
                # skip locked particles
                part = char.particles[slot]
                partID = part.inPool[1] if part else None
                locked = part is not None and partID in self.locked
                if not showOnly and not locked:

                    # get, equip, and lock the top suggestion
                    partID, impact = (next(iter(
                        self._guru.suggest(
                            charID, slot, callback=printProgressBar
                        ).items()
                    )))
                    part = self.laboratory.items[partID]
                    char.addParticle(part, slot)
                    self.locked.append(partID)

                # print the character, slot, and particle equipped
                printSlot(char, slot, partID in self.locked)

            # print the character's stats
            self.printStats(charName)
            print('-' * 40)

    def show(self, arg1=None, arg2=None):
        """A shortcut for `self.equip(arg1, arg2, showOnly=True)`."""
        self.equip(arg1, arg2, True)

    def suggest(self, charName, slot, allParts=False, logodds=False):
        """Shows the guru's suggestions for the given character and
        slot.

        Args:
            charName (str): The character to pass to the guru.
            slot (int): The slot to pass to the guru.
            allParts (bool): If False, dominated particles are omitted.
            logodds (bool): If True, probabilities are displayed as
                log-odds.

        """
        # get character
        char = self.roster.get(charName)
        charID = char.inPool[1]

        # temporarily unlock equipped particle in given slot
        origPart = char.particles[slot]
        relock = False
        if origPart is not None:
            origPartID = origPart.inPool[1]
            if origPartID in self.locked:
                self.locked.remove(origPartID)
                relock = True

        # get particle impacts
        impacts = self._guru.suggest(
            charID, slot, allParts, printProgressBar
        )

        # relock equipped particle
        if relock:
            self.locked.append(origPartID)

        # build and print table to display particles and their impacts
        table = []
        for partID, impact in impacts.items():
            part = self.laboratory.items[partID]
            if logodds:
                for statName in impact.stats:
                    if self._statMenu[statName].probability:
                        p = impact.stats[statName]
                        impact.stats[statName] = log(p/(1 - p))
            row = [partDisplay(part)] + list(
                roundStat(val) for val in impact.stats.values()
            )
            table.append(row)
        header = ['Particle'] + list(impact.stats.keys())
        print(tabulate(table, headers=header))

    def seePartDisplay(self, *partIDs):
        """Returns a list of strings to print to the console when
        showing particle information and location. Stats are not
        alphabetized, but rather shown in the order they appear on the
        particle. The location that is shown is the location in the
        embedded `saveSlot` object, which may differ from the in-game
        location if the guru has moved particles. To see the location
        of the particle at the time the guru instance was created (which
        should match the in-game position), use the `changes` method.

        Args:
            partIDs (list of int): The IDs of the particles whose
                information to display.

        Returns:
            list of str: The lines to print.

        """
        disp = []
        for partID in partIDs:
            part = self.laboratory.items[partID]
            disp.append(
                partDisplay(part, partID in self.locked, False, True)
            )
        return disp

    def seePart(self, *partIDs):
        """Prints to the console the changes returned by the
        `seePartDisplay` method.

        """
        for line in self.seePartDisplay(*partIDs):
            print(line)

    def move(self, partID, charName, slot, force=False):
        """Moves the given particle to the given slot on the given
        character.

        Args:
            partID (int): The ID of the particle to move.
            charName (str): The name of the character to move it to.
            slot (int): The slot to move it to.
            force (bool): If True, both the particle being moved and the
                particle in the destination slot are unlocked
                automatically, and the method ends by locking the moved
                particle.

        Raises:
            ValueError: If either the given particle or the particle in
                the given slot is locked.

        """
        char = self.roster.get(charName)
        part = char.particles[slot]
        equippedPartID = part.inPool[1] if part else None
        if force:
            for idNum in (equippedPartID, partID):
                try:
                    self.locked.remove(idNum)
                except ValueError:
                    pass
        if partID in self.locked or equippedPartID in self.locked:
            raise ValueError('cannot move locked particle')
        char.addParticle(self.laboratory.items[partID], slot)
        if force:
            self.locked.append(partID)

    def getChanges(self):
        """Builds and returns a dictionary showing changes in the
        particle configuration. Currently unequipped particles are
        omitted. Particles are sorted by character, in the order they
        appear in the `chars` attribute.

        Returns:
            dict of int:(tuple of (Character, int)): A dictionary
                mapping a particle ID to a 2-tuple. The first item is
                the original `equippedOn` attribute of the particle. The
                second item is the current `equippedOn` attribute of the
                particle.

        """
        changes = {
            partID: (from_, to)
            for partID, (from_, to) in self.saveSlot.diffPartConfig.items()
            if to is not None
        }
        charNames = self.chars
        def getIndex(char):
            try:
                return charNames.index(char.name)
            except ValueError:
                return len(charNames)
        changes = dict(sorted(
            changes.items(),
            key=lambda item: (getIndex(item[1][1][0]), item[1][1][1])
        ))
        return changes       

    def changesDisplay(self):
        """Returns a list of strings to print to the console when
        showing changes to the particle configuration. Particle stats
        are listed in the order they appear on the particle. Each item
        in the list is a line on the console.

        Returns:
            list of str: The lines to print.

        """
        changes = self.getChanges()
        disp = []
        for partID, (from_, to) in changes.items():
            part = self.laboratory.items[partID]
            disp.append(
                partDisplay(part, sort=False)
                + ' from ' + equippedOnDisplay(from_)
                + ' to ' + equippedOnDisplay(to)
            )
        return disp

    def changes(self):
        """Prints to the console the changes returned by the
        `changesDisplay` method.

        """
        for line in self.changesDisplay():
            print(line)

    def save(self):
        """Saves the `chars`, `stats`, and `locked` attributes to a json
        file in the same location as this module. Subsequent uses of
        this method will overwrite previous uses.

        """
        partConfig = self.saveSlot.getPartConfig()
        jsonDict = self.saveSlot.partConfigToJsonDict(partConfig)
        data = {
            'chars': self.chars,
            'stats': dict(self.stats),
            'locked': self.locked,
            'partConfig': jsonDict
        }
        with open(PATH + '/gurudata.json', 'w') as f:
            dump(data, f, indent=4)

    def load(self):
        """Restores the data saved by the last use of the `save` method,
        overwriting the current data.

        """
        with open(PATH + '/gurudata.json') as f:
            data = load(f)
        self.chars = data['chars']
        self._guru.stats = {'default': []}
        for charName, statNames in data['stats'].items():
            self.addStats(*statNames, char=charName)
        self._guru.locked = data['locked']
        jsonDict = data['partConfig']
        partConfig = self.saveSlot.jsonDictToPartConfig(jsonDict)
        self.saveSlot.setPartConfig(partConfig)


