"""This module contains custom utility functions used to parse the data
files and create the constants needed in the `legendscli` package.

Attributes:

    ROOT (str): The full, absolute path of the legendscli package.

"""

from json import load
from os.path import abspath, dirname
from os import getcwd
from pathlib import Path
from distutils.dir_util import copy_tree
from legendscli.utils.functions import readData

__all__ = [
    'ROOT', 'getItems', 'getSummonPool', 'getPartStats', 'getPowerFunc',
    'getSkillIDs', 'getAssets'
]

ROOT = abspath(dirname(__file__))

def getItems():
    """Parses `GSItem.json` as a dictionary. Restructures that
    dictionary so it is more useful to the `legendscli` package. Then
    returns the restructured dictionary.

    Returns:
        dict: The restructured dictionary.

    """
    unwantedCategories = ['Token', 'PlayerAvatar', 'Emote']
    unwantedCurrency = [
        'Credits', 'Dilithium', 'Tritanium', 'Player XP', 'PvP Stamina',
        'Alliance Stamina', 'EventPoint', 'PvP Chest Points'
    ]
    unwantedItem = [
        'Shards Advanced', 'Shards Elite', 'Shards Credit', 'Shards Biomimetic',
        'Shards Protomatter', 'Shards_Worf', 'Shards_McCoy', 'SeasonPoint'
    ]
    unwanted = unwantedCurrency + unwantedItem
    itemGlossary = {
        'Biomimetic Gel':       'Bio-Mimetic Gel',
        'Advanced Bio-Gel':     'Very Rare Bio-Gel',
        'Elite Bio-Gel':        'Epic Bio-Gel',
        'Proto Command 01':     'Command Protomatter',
        'Proto Engineer 01':    'Engineer Protomatter',
        'Proto Security 01':    'Security Protomatter',
        'Proto Science 01':     'Science Protomatter',
        'Proto Medical 01':     'Medical Protomatter',
        'Medal':                'PvP Medal',
        'Shards Basic':         'Orb'
    }
    plurals = {
        'Power Cell':   'Power Cells',
        'PvP Medal':    'PvP Medals',
        'Orb':          'Orbs',
        'Antiproton':   'Antiprotons',
        'Antineutron':  'Antineutrons'
    }
    GSItem = readData('GSItem', ROOT)
    def modify(name, data):
        newData = data.copy()
        if data['icon'][:4] == 'Gear':
            if data['rarity'] == 'Common':
                newData['category'] = 'GearLevelingMat'
            else:
                newData['category'] = 'GearRankingMat'
        newName = itemGlossary.get(name, name)
        newNamePlural = plurals.get(newName, newName)
        newData['inGameName'] = newName
        newData['inGameNamePlural'] = newNamePlural
        return newData
    GSItem = {
        name: modify(name, data) for name, data in GSItem.items()
        if name not in unwanted and data['category'] not in unwantedCategories
    }
    items = {}
    for name, data in GSItem.items():
        category = data['category']
        if category not in items:
            items[category] = {}
        items[category][name] = data
    return items

def getSummonPool(summonable):
    """Builds and returns a dictionary giving probabilities associated
    to the different available summon pools.

    Args:
        summonable (dict): A dictionary of characters with the same
            structure as 'GSCharacter.json', but only containing
            summonable characters.

    Returns:
        dict of str:(dict of str:float): A dictionary mapping pool names
            (either 'Crew' or a role) to a dictionary mapping character
            names in that summon pool to the probability of receiving
            them on a single summon.

    """

    poolNames = [
        'Crew', 'Command', 'Science', 'Engineering', 'Security', 'Medical'
    ]
    summonPool = {}
    for poolName in poolNames:
        rarityProbs = {
            'Common': 0.35, 'Rare': 0.3, 'VeryRare': 0.2, 'Epic': 0.1,
            'Legendary': 0.05
        }
        probs = {
            charName: 0 for charName, data in summonable.items()
            if poolName == 'Crew' or data['Role'] == poolName
        }
        counts = {rarity: 0 for rarity in rarityProbs}
        for charName in probs:
            counts[summonable[charName]['Rarity']] += 1
        for rarity in rarityProbs:
            if counts[rarity] == 0:
                rarityProbs['Common'] += rarityProbs[rarity]
                rarityProbs[rarity] = 0
        for charName in probs:
            rarity = summonable[charName]['Rarity']
            probs[charName] = rarityProbs[rarity]/counts[rarity]
        summonPool[poolName] = probs
    return summonPool

def getPartStats(rarities):
    """Parse two different data files to produce a dictionary that maps
    stat names to the values of those stats that appear on particles of
    different rarities and levels.

    Args:
        rarities (iter of str): Should be an iterable of rarities in the
            game, in order from lowest to highest. Rarity names should
            match those used in 'GSAccessoryStatGrowth'.

    Returns:
        dict of str:(dict of str:(list of float)): A dictionary mapping
            stat names to a dictionary mapping rarity names to a list
            whose indices denote the 0-based level of the particle and
            whose values denote the value of the given stat on a
            particle of the given rarity and level.

    """
    statGen = readData('GSAccessoryStatGeneration', ROOT)
    partStats = {
            statName: {rarity: [0] * 5 for rarity in rarities}
            for statName in statGen
        }
    statGrowth = readData('GSAccessoryStatGrowth', ROOT)
    for v in statGrowth.values():
        statName = v['Stat']
        level = v['Level']
        rarity = v['Rarity']
        statVal = v['StatIncrease']
        partStats[statName][rarity][level - 1] = statVal
    return partStats

def getPartUpgrading(rarities):
    """Parses a data file to produce a dictionary that encodes the
    latinum and power cell cost of upgrading particles, as well as the
    number of power cells received for selling them.

    Args:
        rarities (iter of str): Should be an iterable of rarities in the
            game, in order from lowest to highest. Rarity names should
            match those used in 'GSAccessoryStatGrowth'.

    Returns:
        dict of str:(dict of int:(dict of str:int)): A dictionary
            mapping a particle's rarity to a dictionary mapping a
            particle's level to a dictionary mapping three different
            stat names to their values.

    """
    upgrading = readData('GSAccessoryUpgrading', ROOT)
    partUpgrading = {
        rarity: {level: {} for level in range(1,6)} for rarity in rarities
    }
    for data in upgrading.values():
        level = data['Level']
        rarity = data['Rarity']
        partUpgrading[rarity][level]['latinumCost'] = (
            data['PriceUpgrade']['AllItems']['Latinum']
        ) if level != 1 else None
        partUpgrading[rarity][level]['powerCellCost'] = (
            data['PriceUpgrade']['AllItems']['Power Cell']
        ) if level != 1 else None
        partUpgrading[rarity][level]['powerCellSell'] = (
            data['RewardSell']['AllItems']['Power Cell']
        )
    return partUpgrading

def getPowerFunc(baseStats):
    """Constructs the parameters needed to compute power as a function
    of stats.

    Args:
        baseStats (dict): Should be a dictionary representation of
            'GSBaseStat.json'.

    Returns:
        tuple: A 2-tuple. The first value is the power gradient, a
            dictionary mapping stat names to the amount that a
            character's power would increase if that stat were to
            increase by 1. The second value is the power root, the
            theoretical power of a character whose every stat is 0.

    """
    grad = {}
    for statName in baseStats:
        m = baseStats[statName]['MinValue']
        M = baseStats[statName]['MaxValue']
        grad[statName] = 10 / (M - m)
    root = 0
    for statName in baseStats:
        root -= (
            grad[statName] * baseStats[statName]['MinValue']
        )
    return grad, root

def getSkillIDs(chars):
    """Gathers and returns the skill IDs for all skills of all
    characters in `chars`.

    Args:
        chars (dict): Should be a subdictionary representation of
            'GSCharacter.json'.
        disabled (bool): If set to true, will gather skill IDs for
            disabled characters as well.

    Returns:
        list of str: A list of skill IDs.

    """
    skillIDs = []
    for v in chars.values():
        skillIDs.extend(v['SkillIDs'])
    return skillIDs

def exportData():
    """Copies the `data` folder from inside the `legendscli` package to
    a folder named `data-current` in the current directory. The `data`
    folder contains the deserialized game assets used by the
    `legendscli` package.

    """
    if Path(getcwd() + '/data-current').is_dir():
        raise IOError("a folder named 'data-current' already exists")
    copy_tree(ROOT + '/data', getcwd() + '/data-current')

def restoreData():
    """Replaces the `data` folder inside the `legendscli` package with a
    folder in the current working directory named `data-old`.

    """
    copy_tree(getcwd() + '/data-old', ROOT + '/data')

def updateData():
    """Copies the 'data' folder that is inside the legendscli package to
    a new folder named 'data-old' in the current working directory. Then
    replaces the `data` folder inside the `legendscli` package with a
    folder in the current working directory named `data-new`.

    """
    if Path(getcwd() + '/data-old').is_dir():
        raise IOError("a folder named 'data-old' already exists")
    copy_tree(ROOT + '/data', getcwd() + '/data-old')
    copy_tree(getcwd() + '/data-new', ROOT + '/data')




