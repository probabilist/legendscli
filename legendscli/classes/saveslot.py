from types import MappingProxyType
from re import findall
from datetime import datetime, timezone
import webbrowser
from os.path import abspath, dirname
from json import load, loads, dump
from pyperclip import paste
from base64 import encode, b64decode
from zlib import decompress
from copy import deepcopy
from legendscli.utils.printable import Printable
from legendscli.constants import ITEMS
from legendscli.functions import decryptSaveFile
from legendscli.classes.particle import Particle
from legendscli.classes.collections import Laboratory
from legendscli.classes.gearpiece import GearPiece
from legendscli.classes.collections import Armory
from legendscli.classes.character import Character
from legendscli.classes.collections import Roster

PATH = abspath(dirname(__file__))

class SaveSlot(Printable):
    """A SaveSlot object represents one of the three in-game save slot.

    Attributes:
        saveDict (dict): A dictionary of save slot information, with the
            original formatting provided by the save file.
        laboratory (Laboratory): The laboratory of particles stored in
            the save slot.
        armory (Armory): The armory of gear pieces stored in the save
            slot.
        roster (Roster): The roster of characters stored in the save
            slot.

    """

    def __init__(self):
        """Creates an empty save slot.

        """
        Printable.__init__(self)
        self.collapse = ['saveDict', 'laboratory', 'armory', 'roster']
        self._saveDict = None
        self._startDate = None
        self._fullInventory = {}
        self.roster = None
        self.armory = None
        self.laboratory = None
        self._savedPartConfig = None

    @property
    def saveDict(self):
        """dict: A dictionary of save slot information, with the
        original formatting provided by the save file.
        """
        if self._saveDict is None:
            return None
        else:
            return MappingProxyType(self._saveDict)

    @property
    def startDate(self):
        """datetime: The date and time the save slot was created."""
        return self._startDate

    @property
    def fullInventory(self):
        """dict: A copy of `legendscli.constant.ITEMS` with a `quantity`
        field added to each item. Fetching this property returns a deep
        copy of the underlying data, so modifying its value has no
        persistent effect.
        """
        return deepcopy(self._fullInventory)

    @property
    def inventory(self):
        """dict: A simplified version of the `fullInventory` property.
        """
        inv = {}
        for category, itemGroup in self._fullInventory.items():
            inv[category] = {}
            for name, data in itemGroup.items():
                displayName = data['inGameNamePlural']
                inv[category][displayName] = data['quantity']
        return inv

    @property
    def diffPartConfig(self):
        """dict of int:((Character, int), (Character, int)): A
        dictionary mapping the ID of each particle that has moved to a
        tuple of 2-tuples. The first is the original `equippedOn`
        attribute of the particle. The second is its current value.
        """
        diff = {}
        for partID, location in self.readPartConfig().items():
            part = self.laboratory.items[partID]
            if part.equippedOn == location:
                continue
            diff[partID] = (location, part.equippedOn)
        return diff

    @property
    def incompleteMissions(self):
        """dict of str:float: A dictionary mapping the names of
        incomplete missions to the proportion completion. Mission names
        are formatted as '[episode]-[mission]-[difficulty'.
        """
        difficulties = {
            'Easy': 'Normal',
            'Hard': 'Advanced',
            'Doom': 'Expert'
        }
        incompleteMissions = {}
        for dataDiff, inGameDiff in difficulties.items():
            for ep in range(1,8):
                for miss in range(1,7):
                    dataKey = 'episode ' + str(ep) + ' mission ' + str(miss)
                    if dataKey not in self.saveDict['missions']:
                        percent = 0
                    else:
                        data = self.saveDict['missions'][dataKey]
                        try:
                            percent = data[dataDiff]['complete_pct']
                        except KeyError:
                            percent = 0
                    if percent < 100:
                        key = str(ep) + '-' + str(miss) + ' ' + inGameDiff
                        incompleteMissions[key] = percent/100
        return incompleteMissions


    def build(self):
        """Sets the `startDate` property, the creates and fills the
        laboratory, arsenal, and roster objects from the information in
        the `saveDict` attribute.

        This method should not need to be run directly. It is run
        automatically by whatever method is used to extract the save
        slot.

        Raises:
            ValueError: If `saveDict` is None.

        """
        if self.saveDict is None:
            raise ValueError(
                'need to first extract the save slot'
            )
        if 'createts' in self.saveDict:
            self._startDate = datetime.fromtimestamp(
                self.saveDict['createts'], timezone.utc
            )
        items = self.saveDict['items']
        self._fullInventory = deepcopy(ITEMS)
        for category, itemGroup in self._fullInventory.items():
            for name, data in itemGroup.items():
                data['quantity'] = items.get(name, 0)
        self.laboratory = Laboratory()
        for idNum, data in self.saveDict['accessories'].items():
            idNum = int(idNum)
            L = findall('[A-Z][^A-Z]*', data['accessoryid'])
            type_ = L[0] + ' ' + L[1].strip('_')
            rarity = ('VeryRare' if L[2] == 'Very' else L[2])
            part = Particle(type_, level=data['level'], rarity=rarity)
            for statName in data['stats'].values():
                part.addStat(statName, silent=True)
            self.laboratory.addItem(part, idNum=idNum, safe=False)
        self.armory = Armory()
        for idNum, data in self.saveDict['gears'].items():
            idNum = int(idNum)
            name, role = data['gearid'].split(' 2256 ')
            gearPiece = GearPiece(name, role, data['level'])
            self.armory.addItem(gearPiece, idNum=idNum, safe=False)
        self.roster = Roster()
        for charName, data in self.saveDict['units'].items():
            char = Character(charName, data['rank'], xp=data['xp'])
            for skill in char.skills:
                skill.level = data['skills'][skill.skillID]
            for gearID in data['gears'].values():
                if gearID != 0:
                    char.addGear(self.armory.items[gearID])
            for slot, particleID in data['accessories'].items():
                if particleID != 0:
                    slot = int(slot[1])
                    char.addParticle(self.laboratory.items[particleID], slot)
            self.roster.addItem(char, update=False)
        self.roster.makeStats()        

    def extractFromFile(self, slot=0):
        """Extracts the save slot dictionary from the decrypted save
        file and stores it in the `saveDict` attribute, sets the
        `startDate` attribute, then creates the object pools.

        Args:
            slot (int): The slot (0, 1, or 2) that will be extracted.

        """
        self._saveDict = decryptSaveFile()[str(slot) + ' data']
        self.build()

    def extractFromDatacoreJson(self):
        """To use this method, first run the `getDatacoreJson` method,
        which will download a json file of the player's profile. Move
        the downloaded file to the current working directory and rename
        it 'profile.json'. Once this is done, this method will extract
        the save slot dictionary from the downloaded file and store it
        in the `saveDict` attribute, then create the object pools.

        Note that building from datacore produces a save dictionary with
        very few items, compared to building from file. It still has the
        characters, gear pieces, particles, and missions, and if the
        datacore profile was created with the 'full' option, it will
        have the inventory. But everything else is missing, including,
        among many other things, the start date of the save slot and the
        pvp logs.

        """
        with open('profile.json') as f:
            self._saveDict = load(f)
        self.build()

    def extractFromClipboard(self):
        """To use this method, first click the in-game Support button to
        generate a support email. Change the "To:" field and send the
        email to yourself. Then, on the same computer on which you are
        calling this method, copy everything in the email after "data:"
        to the clipboard. Finally, call this method and it will build
        your save slot from the clipboard contents.

        """
        b64data = paste().encode('utf-16')
        compressedData = b64decode(b64data)
        data = decompress(compressedData, -15)
        self._saveDict = loads(data.decode('ascii'))
        self.build()

    def exportSaveDict(self, fileName='saveslot'):
        """Writes the dictionary in the `saveSlot` attribute to a json
        file in the current working directory.

        Args:
            fileName (str): The name, without extension, to give to the
                json file.

        Raises:
            ValueError: If `saveDict` is None.

        """
        if self.saveDict is None:
            raise ValueError(
                'need to first build the save slot dictionary'
            )
        with open(fileName + '.json', 'w') as f:
            dump(self._saveDict, f, indent=4, sort_keys=True)

    def getPartConfig(self):
        """A particle configuration is a mapping connecting a particle's
        ID to the character and slot in which it is equipped. This
        method computes and returns the current particle configuration.

        Returns:
            dict of int:(Character, int): The current particle
                configuration.

        """
        partConfig = {}
        for partID, part in self.laboratory.items.items():
            partConfig[partID] = part.equippedOn
        return partConfig

    def partConfigToJsonDict(self, partConfig):
        """Converts a particle configuration to a dictionary more
        suitable to json serialization. It replaces the particle ID with
        a string representation of the ID, and replaces the character
        with the character's name.

        Args:
            partConfig (dict of int:(Character, int)): A particle
                configuration like that returned by `getPartConfig`.

        Returns:
            dict of str:(str, int): The converted dictionary.

        """
        jsonDict = {}
        for partID, location in partConfig.items():
            if location is not None:
                char, slot = location
                location = (char.name, slot)
            jsonDict[str(partID)] = location
        return jsonDict

    def writePartConfig(self, partConfig):
        """Converts the given particle configuration to a
        json-compatible dictionary, then writes it to a file named
        'pconfigdata.json' in the same location as this module file.

        Args:
            partConfig (dict of int:(Character, int)): A particle
                configuration like that returned by `getPartConfig`.

        """
        jsonDict = self.partConfigToJsonDict(partConfig)
        with open(PATH + '/pconfigdata.json', 'w') as f:
            dump(jsonDict, f, indent=4)

    def savePartConfig(self):
        """Saves the current particle configuration. Subsequent uses of
        this method will overwrite previous uses.

        """
        self.writePartConfig(self.getPartConfig())

    def setPartConfig(self, partConfig):
        """Adjust particle locations to match the given particle
        configuration.

        Args:
            partConfig (dict of int:(Character, int)): A particle
                configuration like that returned by `getPartConfig`.

        """
        for partID, location in partConfig.items():
            part = self.laboratory.items[partID]
            if part.equippedOn == location:
                continue
            if location is None:
                oldChar, oldSlot = part.equippedOn
                oldChar.removeParticle(oldSlot)
            else:
                newChar, newSlot = location
                newChar.addParticle(part, newSlot)

    def jsonDictToPartConfig(self, jsonDict):
        """Builds and returns a particle configuration from a dictionary
        like that returned by 'partConfigToJsonDict'.

        Args:
            jsonDict (dict of str:(str, int)): The dictionary to build
                from.

        Returns:
            dict of int:(Character, int): The reconstructed particle
                configuration.

        """
        partConfig = {}
        for partID, location in jsonDict.items():
            if location is not None:
                charName, slot = location
                location = (self.roster.get(charName), slot)
            partConfig[int(partID)] = location
        return partConfig

    def readPartConfig(self):
        """Reads the json-compatible dictionary from 'pconfigdata.json'
        in the same location as this module file, then builds a particle
        configuration from it.

        Returns:
            dict of int:(Character, int): The reconstructed particle
                configuration.

        """
        with open(PATH + '/pconfigdata.json') as f:
            jsonDict = load(f)
        partConfig = self.jsonDictToPartConfig(jsonDict)
        return partConfig

    def loadPartConfig(self):
        """Restores the particle configuration stored by the last call
        to the `savePartConfig` method.

        """
        self.setPartConfig(self.readPartConfig())



