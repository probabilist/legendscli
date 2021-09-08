"""This module contains the functions used in the `legendscli` package.

"""

from os import getcwd
from json import loads, dump
from pathlib import Path
from getpass import getuser
from shutil import copyfile
from plistlib import load
import webbrowser
from legendscli.utils.functions import AESdecrypt
from legendscli import constants
from legendscli.constants import (
    POWER_GRADIENT, POWER_AT_ORIGIN, PART_STAT_VALUES
)

__all__ = [
    'powerDelta', 'power', 'maxParticleStats', 'exportConstants',
    'saveFilePath', 'copySaveFile', 'decryptSaveFile', 'saveFileToJson'
]

def powerDelta(stats):
    """Computes the change in power as a function of the change in
    stats.

    Args:
        stats (dict of str:float): A dictionary mapping stat names to
            the change in those stats.

    Returns:
        float: The amount that a character's power would change if their
            stats changed by the given amounts.

    """
    delta = 0
    for statName, statVal in stats.items():
        delta += POWER_GRADIENT[statName] * statVal
    return delta

def power(stats):
    """Computes the power of a character with the given stats.

    Args:
        stats (dict of str:float): A dictionary mapping stat names to
            their values.

    Returns:
        float: The power of a character with the given stats.

    """
    return POWER_AT_ORIGIN + powerDelta(stats)

def maxParticleStats():
    """Computes the maximum possible stats on particles, which
    correspond to Level 5, Legendary particles.

    Returns:
        dict of str:(dict of str:float): A dictionary mapping stat names
            to a dictionary with two keys, 'maxValue' and 'power', whose
            values are the maximum possible value of that stat on a
            particle, and the corresponding change in power granted by
            that stat value.

    """
    maxStats = {}
    for statName, data in PART_STAT_VALUES.items():
        maxValue = data['Legendary'][4]
        maxStats[statName] = {
            'maxValue': maxValue,
            'power': powerDelta({statName: maxValue})
        }
    return maxStats

def exportConstants():
    """Exports the constants in the `legendscli.constants` module to
    json files. Places them in a folder named 'constants' in the current
    working directory.
 
    """
    Path(getcwd() + '/constants').mkdir(exist_ok=True)
    for name in dir(constants):
        if name[0] != '_':
            obj = getattr(constants, name)
            if not callable(obj):
                with open('constants/' + name + '.json', 'w') as f:
                    dump(obj, f, indent=4)

def saveFilePath():
    """Creates and return the complete path of the save file.

    Returns:
        str: The complete path of the save file.

    """
    return (
        '/Users/' + getuser() + '/Library/Containers/'
        + 'com.tiltingpoint.startrek/Data/Library/Preferences/'
        + 'com.tiltingpoint.startrek.plist'
    )

def copySaveFile(fileName='startrek'):
    """Places a copy of the original save file in the current working
    directory.

    Args:
        fileName (str): The name, without extension, to give to the
            copy.

    """
    copyfile(saveFilePath(), getcwd() + '/' + fileName + '.plist')

def decryptSaveFile():
    """Decrypts and parses the save file into a dictionary.

    Returns:
        dict: The decrypted save file as a dictionary.

    """
    with open(saveFilePath(), 'rb') as f:
        saveFile = load(f)
    del saveFile['CloudKitAccountInfoCache']
    for i in range(3):
        key = str(i) + ' data'
        if len(saveFile.get(key, '')) == 0:
            saveFile[key] = {}
            continue
        saveFile[key] = loads(AESdecrypt(
            saveFile[key],
            'K1FjcmVkc2Vhc29u',
            'LH75Qxpyf0prVvImu4gqxg=='
        ))
    return saveFile

def saveFileToJson(fileName='startrek'):
    """Creates a json file from the decrypted save file and stores it in
    the current working directory.

    Args:
        fileName (str): The name, without extension, to give to the
            json file.

    """
    with open(fileName + '.json', 'w') as f:
        dump(decryptSaveFile(), f, indent=4, sort_keys=True)
