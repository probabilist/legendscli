# legendscli (Legends Command Line Interface)

A Python package for Star Trek: Legends.

This package uses text assets from Star Trek: Legends. For extracting/updating these text assets, see https://github.com/probabilist/legends-assets.

## Installation instructions

This package is developed and tested in Python 3.7.11. Unless you already use Python, you will probably need to install it. For example, may Mac came with Python 2.7 pre-installed. This package will not run on Python 2.7.

There are many ways to install Python, so google around for one that works for you. Once you get Python installed, follow the below instructions.

(Note: This package makes use of the insertion-order preservation nature of `dict` objects. This is an official part of Python 3.7 and an unofficial part of Python 3.6. The package will probably work in 3.6 or higher, but not in anything lower.)

1. Create a new folder somewhere. For the sake of the example, let's say your new folder is 'Documents/StarTrek'.

2. Copy the 'legendscli' folder and the 'requirements.txt' text file from this repository into your new folder, 'Documents/StarTrek'.

3. Open a command prompt at 'Documents/StarTrek'. There are many ways to do this. On a Mac, you can open Finder, navigate to 'Documents', right click on 'StarTrek', and select 'Services > New Terminal at Folder'.

4. At the command prompt, enter
```
% pip install -r requirements.txt
```
This will install the packages needed to run the `legendscli` package.

5. (optional) At the command prompt, enter
```
% python -m pydoc -b
```
This will open a browser page with Python documentation. Find the "**legendscli** (package)" link and click it. You can now explore all the package documentation.

6. At the command prompt, enter
```
% python
```
This will open the `Python` interpreter in interactive mode. Your command prompt ought to change to the Python prompt `>>>`.

7. At the Python prompt, enter
```
>>> from legendscli import *
```
You are now ready to explore the functionality of the `legendscli` package.

Note: Depending on how you installed Python, you may need to replace `pip` and `python` with `pip3` and `python3`.

## A brief tour

### Getting started

Let's build a roster of maxed characters to explore:
```
>>> r = Roster(maxed=True)
```
This creates a `Roster` object with all summonable characters at max rank and max level, and with maxed gear. To view them all in a spreadsheet:
```
>>> v = tools.RosterViewer(r)
>>> v.printCSV('roster')
```
This will create a CSV file named "roster.csv" in the current working directory that shows all the characters in the roster.

If we want to build a roster of our own characters, we can do that too. If you are on a Mac that's new enough to run Apple Arcade, open Star Trek: Legends on the Mac and let it load until you see the Artemis. Then type:
```
>>> mySave = SaveSlot()
>>> mySave.extractFromFile()
```
You now have access to all the data in your save slot. If you are not on a Mac, there is an `extractFromClipboard` method you can use instead.

We can now view our characters in a spreadsheet like before:
```
>>> viewer = tools.RosterViewer(mySave.roster)
>>> viewer.printCSV('myRoster')
```
Our character spreadsheet is now in "myRoster.csv" in the current working directory.

### Custom stats

The spreadsheet we just created has all the usual stats from the game. But the `legends` package can produce custom stats as well. Some of them are available right now, without doing anything else.
```
>>> print(mySave.roster)
<Roster object>
Attributes:
{'idFromName': <dict object>,
 'items': <dict object>,
 'length': 64,
 'onChange': <legends.utils.eventhandler.EventHandler object at 0x1044df1d0>,
 'power': 145583.39317481456,
 'summonRatesAll': {'Command': 1.0,
                    'Crew': 5.045454545454545,
                    'Engineering': 3.133333333333333,
                    'Medical': 0.0,
                    'Science': 7.6,
                    'Security': 1.7999999999999998},
 'summonRatesNonCommon': {'Command': 1.0,
                          'Crew': 2.420454545454546,
                          'Engineering': 1.3333333333333333,
                          'Medical': 0.0,
                          'Science': 2.0,
                          'Security': 0.0},
 'xp': 43113650}
```
Notice the summon rates attributes. These represent the average number of tokens received for every 150 orbs, as a function of which summon pool we choose to use. Here, I get the most tokens per 150 orbs by using the Science pool. However, if I don't care about Common tokens, I should still use the Crew pool.

As a side note, most of the objects in the `legends` package can be printed to the console like this, so feel free to explore.

### Calculator objects

Other custom stats require special calculator objects. The first of these is the "effective stat calculator". This produces stats like effective attack damage and effective tech damage, which take into account crit chance and crit damage, and effective health, which takes into account things like nexus shields, defense, tech defense, and cloak.
```
>>> esc = tools.EffStatCalc(mySave.roster)
```
All our characters now have these three extra stats, and they will appear in the spreadsheet the next time we print it.

The effective stat calculator comes with default settings, but we can adjust them. For example, by default, our characters are not assumed to be cloaked. If we want to compute our effective health under the assumption that they are cloaked:
```
>>> esc.cloak = True
```

### Sela stat calculator

> **NOTE:** This tool is no longer relevant to the game, since Sela was nerfed in version 1.0.11 of Star Trek: Legends. I have updated this section and the next with the numbers that it produces now, post-nerf. These numbers show that the tool is effectively useless now, since there is little to no chance of dying to Sela's Surprise Attack now.

Another calculator is the Sela stat calculator, which computes things like the chance of surviving Sela's Surprise Attack.
```
>>> ssc = tools.SelaStatCalc(mySave.roster)
```
Our characters now have several stats related to facing an enemy Sela. Like the effective stats, they will appear in the spreadsheet the next time we print it. Or we can view the stats interactively. For example,
```
>>> picard = mySave.roster.get('Picard')
>>> picard.selaStats
mappingproxy({'survSelaCover': 0.9999675807119638,
              'survSelaNoCover': 0.9992945521153624,
              'survSelaCrit': True,
              'survSelaTwoHits': True})
```
My Picard has a 99.997% of surviving Sela's Surprise Attack when behind cover, and a 99.93% chance of surviving out of cover. He can survive a single critical hit from Surprise Attack, and can also survive two non-critical hits.

These stats depend, of course, on what we assume about the enemy Sela. By default, the Sela stat calculator assumes the enemy Sela is Rank 9, Level 99, with no gear and two maxed particles with tech, crit chance, and crit damage. But these settings can be adjusted. If the enemies we're facing are only Level 50, we can change that.
```
>>> ssc.sela.level = 50
>>> picard.selaStats
mappingproxy({'survSelaCover': 1.0,
              'survSelaNoCover': 1.0,
              'survSelaCrit': True,
              'survSelaTwoHits': True})
>>> ssc.sela.level = 99
```

### Away teams

The Sela stat calculator can also deal with away teams. To build an away team, let's first grab the characters from our roster.
```
>>> sela, tpol, geo, toma = mySave.roster.get(
        'Sela', 'TPol', 'Geordi', 'Tomalak')
```
Now we'll create an away team and add them to it.
```
>>> team = AwayTeam()
>>> team.add(sela, tpol, geo, toma)
```
Finally, we'll connect our away team to the Sela stat calculator.
```
>>> ssc.registerTeam(team)
```
Our away team now has a number of team-specific stats related to facing an enemy Sela. For example:
```
>>> team.selaNumSurvivors
mappingproxy({('Sela', 'TPol'): 3.9699480695743325,
              ('Sela', 'Geordi'): 3.8669220097728267,
              ('Sela', 'Tomalak'): 3.8679353592341528,
              ('TPol', 'Geordi'): 3.9474516634454777,
              ('TPol', 'Tomalak'): 3.9484650129068033,
              ('Geordi', 'Tomalak'): 3.8454389531052975})
```
What we see here is the average number of survivors of Sela's Surprise Attack, as a function of who we put behind cover. As we see, this is maximized by placing Sela and T'Pol  behind cover.

### Inventory

Player inventory is available in the `SaveSlot` object. To view your inventory, type
```
>>> mySave.inventory
```
The inventory contains latinum, power cells, alliance currency, bio-gel, protomatter, pvp medals, orbs, gear leveling mats, and gear ranking mats.

### Missions

The `SaveSlot` object can also give you a list of missions that are not yet 100% complete. Typing
```
>>> mySave.incompleteMissions
```
will bring up this list, which includes the mission names and the percent complete (formatted as a decimal).

### Particle guru

> **NOTE:** This part of the tour was written before the Sela nerf in version 1.0.11 of Star Trek: Legends. I have not updated it, so below you will see the particle guru being used to optimize the chances of surviving Sela's Surprise Attack. Post-nerf, there is no reason to use it that way. But the tool is still relevant and effective. You just have to tell it to optimize different stats--whichever ones you feel are most effective for your purposes.

Our save slot also contains all our particles.
```
>>> labView = tools.LaboratoryViewer(mySave.laboratory)
>>> labView.printCSV('myLab')
```
There should now be a spreadsheet, "myLab.csv", in the current working directory that shows all of our particles.

The process of deciding which characters should get which particles can be guided by the Particle Guru Interactive Prompt Tool.
```
>>> guru = tools.GuruIPT(mySave)
```
This creates a particle guru that will recommend particles for our characters. By default, the guru will only consider Legendary Level 5 particles, but this can be adjusted.

To start, we add the characters we want the guru to consider.
```
>>> guru.chars = ['Sela', 'TPol', 'Geordi', 'Tomalak']
```
Next, we need to tell the guru which stats are important to us.
```
>>> guru.addStats('survSelaNoCover', 'effTechDmg')
```
We have told the guru that the most important stat for us is the character's chance of surviving Sela's Surprise Attack when out of cover, and the second most important stat is our effective tech damage. These will be the stat priorities, by default, for all characters.

But that doesn't make sense for T'Pol and Tomalak, so we can customize those.
```
>>> guru.addStats('survSelaCover', 'effAttDmg', char='TPol')
>>> guru.addStats('survSelaNoCover', 'effHealth', char='Tomalak')
```
At any time, we can view the stats we've set.
```
>>> guru.stats
mappingproxy({'default': ('survSelaNoCover', 'effTechDmg'),
              'TPol': ('survSelaCover', 'effAttDmg'),
              'Tomalak': ('survSelaNoCover', 'effHealth')})
```
Now, before we do anything, let's look at the particles that are on the characters right now.
```
>>> guru.show()
Sela 0: [72] Nexus L5 (CC/CD/GD/T)
Sela 1: [303] Nexus L5 (CC/CD/GD/T)
survSelaNoCover: 0.6404, effTechDmg: 2626.14
----------------------------------------
TPol 0: [94] Nexus L5 (A/CC/CD/GD)
TPol 1: [464] Nexus L5 (A/CC/CD/GD)
survSelaCover: 0.8936, effAttDmg: 1129.42
----------------------------------------
Geordi 0: [357] Nexus L5 (CC/GD/H/T)
Geordi 1: [122] Nexus L5 (D/GC/GD/T)
survSelaNoCover: 0.6888, effTechDmg: 2385.87
----------------------------------------
Tomalak 0: [258] Nexus L5 (A/GD/H/T)
Tomalak 1: [393] Nexus L5 (CC/GC/GD/T)
survSelaNoCover: 0.8573, effHealth: 13124.63
----------------------------------------
```
The numbers in brackets are the particle IDs, used internally by Python (and the Star Trek: Legends save file) to identify the particles. Notice that Geordi has Defense on his Slot 1 particle. Let's see what the guru suggests instead.
```
>>> guru.suggest('Geordi', 1)
Particle                       survSelaNoCover    effTechDmg            
---------------------------  -----------------  ------------
[393] Nexus L5 (CC/GC/GD/T)             0.6888       2478.02
[84] Coag L5 (A/CC/CD/GC)               0.6859       2514.44
[161] Nexus L5 (A/CC/CD/GC)             0.6859       2514.44
[72] Nexus L5 (CC/CD/GD/T)              0.6379       2639.49
[100] Amp L5 (CC/CD/GD/T)               0.6379       2639.49
[303] Nexus L5 (CC/CD/GD/T)             0.6379       2639.49
```
The guru has found a particle that gives the same Sela survival chance, but better effective tech damage. It also shows us some other possibilities, with slightly lower Sela survivability, but higher effective tech damage.

Let's equip the first particle, then lock it so that the guru won't suggest it for other characters later.
```
>>> guru.move(393, 'Geordi', 1)
>>> guru.locked.append(393)
>>> guru.show('Geordi')
Geordi 0: [357] Nexus L5 (CC/GD/H/T)
Geordi 1: [*393] Nexus L5 (CC/GC/GD/T)
survSelaNoCover: 0.6888, effTechDmg: 2478.02
----------------------------------------
```
Next, let's see if the guru can find something better for Slot 0.
```
>>> guru.suggest('Geordi', 0)
Particle                       survSelaNoCover    effTechDmg            
---------------------------  -----------------  ------------
[122] Nexus L5 (D/GC/GD/T)              0.7393       2385.87
[161] Nexus L5 (A/CC/CD/GC)             0.7327       2514.44
[72] Nexus L5 (CC/CD/GD/T)              0.6888       2639.49
[303] Nexus L5 (CC/CD/GD/T)             0.6888       2639.49
>>> guru.move(122, 'Geordi', 0)
>>> guru.locked.append(122)
>>> guru.show('Geordi')
Geordi 0: [*122] Nexus L5 (D/GC/GD/T)
Geordi 1: [*393] Nexus L5 (CC/GC/GD/T)
survSelaNoCover: 0.7393, effTechDmg: 2385.87
----------------------------------------
```
We don't have to do this manually for each slot, if we're willing to take the guru's top suggestion:
```
>>> guru.equip('TPol')
TPol 0: [*373] Nexus L5 (CC/GC/GD/H)                                    
TPol 1: [*179] Undo L5 (A/GC/GD/H)                                      
survSelaCover: 0.9297, effAttDmg: 936.71
----------------------------------------
```
Now let's take another look at our team.
```
>>> guru.show()
Sela 0: [72] Nexus L5 (CC/CD/GD/T)
Sela 1: [303] Nexus L5 (CC/CD/GD/T)
survSelaNoCover: 0.6404, effTechDmg: 2626.14
----------------------------------------
TPol 0: [*373] Nexus L5 (CC/GC/GD/H)
TPol 1: [*179] Undo L5 (A/GC/GD/H)
survSelaCover: 0.9297, effAttDmg: 936.71
----------------------------------------
Geordi 0: [*122] Nexus L5 (D/GC/GD/T)
Geordi 1: [*393] Nexus L5 (CC/GC/GD/T)
survSelaNoCover: 0.7393, effTechDmg: 2385.87
----------------------------------------
Tomalak 0: [258] Nexus L5 (A/GD/H/T)
Tomalak 1: None
survSelaNoCover: 0.6259, effHealth: 7657.3
----------------------------------------
```
Notice that we ended up giving Geordi one of Tomalak's particles, so he now only has one. We can equip Tomalak like we equipped T'Pol, or we can equip the whole team at once. When we equip the whole team at once, they are equipped from top to bottom, and locked particles will not be touched. So the guru will first equip Sela, will skip T'Pol and Geordi, and then equip Tomalak.
```
>>> guru.equip()
Sela 0: [*170] Nexus L5 (D/GC/GD/H)                                     
Sela 1: [*369] Amp L5 (CD/GC/GD/H)                                      
survSelaNoCover: 0.7355, effTechDmg: 1948.85
----------------------------------------
TPol 0: [*373] Nexus L5 (CC/GC/GD/H)
TPol 1: [*179] Undo L5 (A/GC/GD/H)
survSelaCover: 0.9297, effAttDmg: 936.71
----------------------------------------
Geordi 0: [*122] Nexus L5 (D/GC/GD/T)
Geordi 1: [*393] Nexus L5 (CC/GC/GD/T)
survSelaNoCover: 0.7393, effTechDmg: 2385.87
----------------------------------------
Tomalak 0: [*321] Nexus L5 (D/GC/GD/H)                                  
Tomalak 1: [*383] Nexus L5 (A/GC/H/T)                                   
survSelaNoCover: 0.8733, effHealth: 8901.22
----------------------------------------
```
Of course, these particle changes are only happening in Python. We still have to go into the game and make the changes. To help us, we can see the changes all at once:
```
>>> guru.changes()
[170] Nexus L5 (D/GC/GD/H) from None to Sela 0
[369] Amp L5 (CD/GC/GD/H) from Dukat 0 to Sela 1
[373] Nexus L5 (CC/GC/GD/H) from None to TPol 0
[179] Undo L5 (A/GC/GD/H) from None to TPol 1
[122] Nexus L5 (D/GC/GD/T) from Geordi 1 to Geordi 0
[393] Nexus L5 (CC/GC/GD/T) from Tomalak 1 to Geordi 1
[321] Nexus L5 (D/GC/GD/H) from None to Tomalak 0
[383] Nexus L5 (A/GC/H/T) from GenRomuSci01F 0 to Tomalak 1
```
If we want to take a break before moving all these particles, we can use `guru.save()`. This will save the characters, stats, locked particles, and particle configuration. At our next Python session, we can use `guru.load()` to restore this information.
