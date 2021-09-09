# Change log

## Version 2.0.1

* Prevented a fatal error that would occur when the key, 'CloudKitAccountInfoCache', was not present in the save file.
* Minor edit to project description.

## Version 2.0

* The `legends` package is now the `legendscli` package. To view revision history prior to v2.0, see https://github.com/probabilist/legends.

## Version 1.3.1

* Updated 'README.md' to reflect the Sela nerf.
* Deleted the `getDatacoreJson` function from 'functions.py', which was used to download save data using a link to player's datacore profile. (This was actually partially deleted in v1.3, but didn't make it into the change log. Now it is fully deleted.)

## Version 1.3

* Moved asset extraction component to a separate repository: https://github.com/probabilist/legends-assets
* Edited comments in package code in preparation to change the name of the `legends` package to `legendscli` (Legends Command Line Interface).

## Version 1.2.6

* Added `PicardOld` to the `UPCOMING` list.
* Added an exception handler to the `incompleteMission` property getter of the `SaveSlot` class. This is intended to prevent a fatal exception that sometimes occurs when trying to view incomplete missions.
* Corrected an error that sometimes caused the roster to fail to print to CSV. The error was related to the fact that a character without particles would be instantiated without any particle effect stats, rather than with those stats present and equal to 0. A change was made in the constructor of the `Character` class to correct for this.
* Corrected a typo in an error message raised when setting a character's xp to an invalid value.

## Version 1.2.5

* Added `tabulate` to `requirements.txt`.
* Modified the `decryptSaveFile` function so it would not raise an error when encountering a missing save slot.
* Fixed typos in docstrings.

## Version 1.2.4

* Updated game data and package code to account for an incoming hotfix that added both Elnor and Troi to the summon pool.

## Version 1.2.3

* Updated data to reflect an unannounced hotfix:
    - The timing of the Chekov and Troi events has been swapped. (Previously, Chevok was scheduled to come up first; now Troi is scheduled to come up first.)
    - The Level 2 version of Troi's basic attack was changed from 125% damage to 150% damage.
* Changed the default settings in the `EffStatCalc` class to reflect changes in version 1.0.11 of the game.
* Added three new constants:
    - `ENABLED`: A dictionary of all characters in the game, even those not yet in the summon pool.
    - `PLAYABLE`: A dictionary that includes ENABLED as well as hidden characters that are presumably meant for a future update.
    - `UPCOMING`: A list of characters in PLAYABLE but not in ENABLED.
* Added an `allChars` boolean argument to the `summonaAll` method in the `Roster` class. If set to `True`, will summon all characters in `PLAYABLE`; otherwise will summon all characters in `ENABLED`.
* Added an `allChars` boolean argument to the `Roster` class constructor. If set to `True` when `maxed` is also set to `True`, will build a roster of maxed characters in `PLAYABLE`.
* The `Skill` class constructor now raises a more informative error message when the skill ID is not recognized.
* Edited a typo in the docstring for the `EffStatCalc` class.
* Minor change to the `getSkillIDs` function in `build.py`. Does not affect current usage.

## Version 1.2.2

* Updated game data for v1.0.11.
* Updated the `surviveHits` method in the `SelaStatCalc` class to account for in-game changes to Sela's Surprise Attack.

## Version 1.2.1

* Added a 'data-all' folder containing all extracted text assets to the project repository.

## Version 1.2

* Added an `incompleteMissions` property to the `SaveSlot` class.
* Updated the `README` file to illustrate using the `incompleteMissions` property.
* In preparation for future features, added a constant, `PART_UPGRADING`, which encodes the latinum and power cell cost of upgrading particles, as well as the number of power cells received for selling them.

## Version 1.1.4

* Fixed an error where Security and Medical summon pools were erroneously assigning 0 probability to Epic characters.
* Fixed errors in the `GuruIPT` methods, `suggest` and `move`, that would occur when a character had no particle equipped.

## Version 1.1.3

* Removed dependency on `UnityPy`.
* Revised version numbering to better reflect the major-minor-patch paradigm.

## Version 1.1.2

* Updated instructions in `constants.py` for extracting game data.
* Added a C# file, `Program.cs`, used for extracting game data.
* Added two new files to `legends/data` in preparation for new features.
* Minor visual bug fixes.

## Version 1.1.1

* Updated the README file to include detailed installation instructions.
* Added `requirements.txt` for use in installation.
* Added an `insertStat` method to `GuruIPT`.
* Disabled summon rates for `AwayTeam` objects. (They had inherited them from the `Roster` class, but they are not relevant for the `AwayTeam` subclass.)
* When dealing with over 1000 particles, `printProgressBar` would not completely clear itself after each display. That has been fixed.
* Renamed `legends.setup` to `legends.build`.
* Removed redundant code in `guruipt.partDisplay`.

## Version 1.1

* Added `GSItem.json` to data.
* Added a `getItems` function to `setup.py`.
* Added an `ITEMS` constant to `constants.py`.
* Added `inventory` and `fullInventory` properties to the `SaveSlot` class.
* Updated `README` to illustrate viewing the inventory.

## Version 1.0.2

* Fixed typos in comments that offer mathematical explanations for the workings of the Sela stat calculator.
* Added a function, `roundSigFig`, to `utils.functions` that rounds numbers according to significant figures.
* Added a boolean `probability` attribute to the `Stat` class in the `particleguru` module, to indicate if the stat is meant to represent a probability.
* Changes to `guruipt` module:
    - Added a constant, `PROBABILITIES`, that lists all stat names which represent probabilities.
    - Added a boolean `location` argument to `partDisplay` function, giving the option to include the particle's location in the returned display string.
    - Modified `roundStat` function to use significant figures for stat values less than 10.
    - Changes to `GuruIPT` class:
        + Modified constructor to set the `probability` attribute of the `Stat` objects in the embedded stat menu.
        + Added `changeStat` and `removeStat` methods.
        + Added a boolean `logodds` argument to the `suggest` method, giving the option to display probabilities as log-odds.
        + For greater compartmentalization, separated off part of the `seePart` method to a new method, `seePartDisplay`. Modified these methods to utilize the new `location` argument in the `partDisplay` function, and to allow a list of particle IDs as arguments.
        + Added a boolean `force` argument to the `move` method, giving the option to unlock, move, and relock particles with a single method call.
        + Fixed the `changesDisplay` method to display stats as they appear on the particle in-game, rather than in alphabetical order.
        + Fixed the docstring for the `changes` method.

## Version 1.0.1

* Enabled Tilly.
* Made `EffStatCalc` and `GuruIPT` printable.
* Added a `copyStats` method to `GuruIPT`.
* Fixed `equip` and `show` methods in `GuruIPT` to work as intended when a single integer argument is passed.
* Added a `seePart` method to `GuruIPT`.
* For greater compartmentalization, separated off part of the `changes` method in `GuruIPT` to a new method, `changesDisplay`.
* Fixed the docstring for `GuruIPT.stats`.
