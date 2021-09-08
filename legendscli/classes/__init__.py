"""Classes representing game objects in Star Trek: Legends.

Namespaces:
    classes

Aliases:
    classes.Skill       = classes.skill.Skill
    classes.GearPiece   = classes.gearpiece.GearPiece
    classes.Particle    = classes.particle.Particle
    classes.Character   = classes.character.Character
    classes.Armory      = classes.collections.Armory
    classes.Laboratory  = classes.collections.Laboratory
    classes.Roster      = classes.collections.Roster
    classes.AwayTeam    = classes.awayteam.AwayTeam
    classes.SaveSlot    = classes.saveslot.SaveSlot

"""

from legendscli.classes.skill import Skill
from legendscli.classes.gearpiece import GearPiece
from legendscli.classes.particle import Particle
from legendscli.classes.character import Character
from legendscli.classes.collections import *
from legendscli.classes.awayteam import AwayTeam
from legendscli.classes.saveslot import SaveSlot
