"""This module contains the `SelaStatCalc` class.

"""

from types import MappingProxyType
from itertools import combinations
from legendscli.utils.functions import fixedSum, powerset
from legendscli.utils.eventhandler import EventHandler
from legendscli.classes.character import Character
from legendscli.classes.particle import Particle
from legendscli.classes.awayteam import AwayTeam

__all__ = ['SelaStatCalc']

class SelaStatCalc():
    """A calculator for stats related to surviving Sela's first attack.

    Attributes:
        onChange (EventHandler): When the settings change, this event
            handler sends the SelaStatCalc object to subscribers.
        pauseTeamUpdates (bool): Set to True to prevent team stats from
            being recalculated whenever a team member changes.

    """

    # a hard-coded factorial function to reduce calculations
    _factorial = {0: 1, 1: 1, 2: 2, 3: 6, 4: 24}

    def __init__(self, roster=None):
        """Creates a Sela stat calculator with a default `sela`
        property. The default is a Rank 9, Level 99 Sela with no gear
        and two Level 5, Legendary Nexus Field particles with tech, crit
        chance, and crit damage.

        Args:
            roster (Roster): If provided, all characters in the roster
                are registered with the effective stat calculator.

        """
        self._sela = Character('Sela')
        self._sela.addParticle(Particle(
            'Nexus Field',
            'Tech', 'CritChance', 'CritDamage'
        ))
        self._sela.onChange.subscribe(self.onSelaChange)

        self._nextID = 1    # characters and away teams register so
                            # their stats are stored for quick
                            # retrieval; they are given an ID when
                            # registering

        self._registrants = {}  # a dictionary of registered characters
                                # by ID
        self.onChange = EventHandler()

        self._survSelaCover = {}
        self._survSelaNoCover = {}
        self._survSelaCrit = {}
        self._survSelaTwoHits = {}

        self._awayTeams = {}    # a dictionary of registered away teams
                                # by ID

        self._survivalProbs = {}
        self._numSurvivors = {}
        self.pauseTeamUpdates = False
        if roster is not None:
            roster.addSelaStatCalc(self)

    @property
    def sela(self):
        """Character: The enemy Sela to use in the calculations. When
        this property changes, all stats are recalculated and
        subscribers are notified of the change. Raises a value error if
        set to anything other than a Character object with name, 'Sela'.
        """
        return self._sela

    @sela.setter
    def sela(self, value):
        if not isinstance(value, Character) or value.name != 'Sela':
            raise ValueError(
                "must set attribute to a `Character` object whose `name` "
                + "attribute is 'Sela'"
            )
        self._sela = value
        self._sela.onChange.subscribe(self.onSelaChange)
        self.onSelaChange()

    @property
    def survSelaCover(self):
        """dict of int:float: A dictionary mapping character IDs to the
        probability they survive Sela's Surprise Attack when they are
        behind cover.
        """
        return MappingProxyType(self._survSelaCover)

    @property
    def survSelaNoCover(self):
        """dict of int:float: A dictionary mapping character IDs to the
        probability they survive Sela's Surprise Attack when they are
        not behind cover.
        """
        return MappingProxyType(self._survSelaNoCover)

    @property
    def survSelaCrit(self):
        """dict of int:bool: A dictionary mapping character IDs to a
        boolean that indicates whether they can survive a single
        critical hit from Sela's Surprise Attack.
        """
        return MappingProxyType(self._survSelaCrit)

    @property
    def survSelaTwoHits(self):
        """dict of int:bool: A dictionary mapping character IDs to a
        boolean that indicates whether they can survive a single
        two normal hits from Sela's Surprise Attack.
        """
        return MappingProxyType(self._survSelaTwoHits)

    @property
    def survivalProbs(self):
        """dict of int:(dict of (tuple of str):(dict of (tuple of str):
        float)): A dictionary mapping away team IDs to a dictionary
        mapping 2-tuples of character names to a dictionary mapping
        tuples of character names of length at most four to
        probabilities.

        More specifically, `survivalProbs[teamID][tuple1][tuple2]` is
        the probability that, when the away team with the given `teamID`
        faces Sela's Surprise Attack with the characters in `tuple1`
        behind cover, the result is that only the characters in `tuple2`
        survive.
        """
        return MappingProxyType(self._survivalProbs)

    @property
    def numSurvivors(self):
        """dict of int:(dict of (tuple of str):float): A dictionary
        mapping away team IDs to a dictionary mapping 2-tuples of
        character names to weighted expectation of the number of
        survivors of Sela's Surprise Attack.

        More specifically, `numSurvivors[teamID][tuple]` is the expected
        value of the sum of the weights of the survivors when the team
        with the given `teamID` faces Sela's Surprise Attack with the
        characters in `tuple` behind cover.
        """
        return MappingProxyType(self._numSurvivors)

    def onSelaChange(self, char=None):
        """This method is called when the `sela` property changes. It
        can be called directly by the Sela stat calculator, in which
        case no `char` argument is provided; or it can be called by the
        Character object that is referred to by the `sela` property, in
        which case that Character object is passed to the `char`
        argument.

        When the method is called, all stats are recalculated and
        subscribers are notified of the change.

        Args:
            char (Character): The Character object referred to by the
                `sela` property, when this method is called by that
                object's `onChange` event handler.

        """
        for charID in self._registrants:
            self.makeCharStats(charID)
        for teamID in self._awayTeams:
            self.makeTeamStats(teamID)
        self.onChange.notify(self)

    def registerChar(self, char, safe=True):
        """Adds the character to the list of registrants, builds the
        character's Sela stats, subscribes to its `onChange` event
        handler, sets its `registeredSSC` attribute, and has the
        character subscribe to the calling SSC's `onCharChange` event
        handler.

        Args:
            char (Character): The character registering with the Sela
                stat calculator.
            safe (bool): Set to False to avoid checking for duplicates.

        Raises:
            ValueError: If character is already registered.

        """
        if safe and char in self._registrants.values():
            raise ValueError('character already registered')
        self._registrants[self._nextID] = char
        self.makeCharStats(self._nextID)
        char.onChange.subscribe(self.onCharChange)
        char.registeredSSC = (self, self._nextID)
        self.onChange.subscribe(char.onSSCChange)
        self._nextID += 1

    def registerTeam(self, team, safe=True):
        """Adds the away team to the list of away teams, builds the away
        team's Sela stats, subscribes to its `onChange` event handler, 
        sets its `registeredSSC` attribute, and has the away team
        subscribe to the calling SSC's `onTeamChange` event handler.

        Args:
            team (AwayTeam): The away team registering with the Sela
                stat calculator.
            safe (bool): Set to False to avoid checking for duplicates.

        Raises:
            ValueError: If away team is already registered.

        """
        if safe and team in self._awayTeams.values():
            raise ValueError('away team already registered')
        self._awayTeams[self._nextID] = team
        self.makeTeamStats(self._nextID)
        team.onChange.subscribe(self.onTeamChange)
        team.registeredSSC = (self, self._nextID)
        self.onChange.subscribe(team.onSSCChange)
        self._nextID += 1

    def onCharChange(self, char):
        """This method is called when a registered character changes. It
        calls for the Sela stats of that character to be recalculated.

        Args:
            char (Character): The character that changed.

        """
        self.makeCharStats(char.SSCid)

    def onTeamChange(self, event):
        """This method is called when a registered away team changes. It
        calls for the Sela stats of that away team to be recalculated.

        Args:
            team (AwayTeam): The away team that changed.

        """
        if not self.pauseTeamUpdates:
            self.makeTeamStats(event.pool.SSCid)

    def makeCharStats(self, charID):
        """Rebuilds the stats of the character with the given ID and
        stores them for retrieval by the respective properties. Rebuilds
        the following stats: 'survSelaCover', 'survSelaNoCover',
        'survSelaCrit', and 'survSelaTwoHits'.

        Args:
            charID (int): The ID of the character, used internally by
                the Sela stat calculator.

        """
        self._survSelaCover[charID] = self.surviveProb(charID, cover=True)
        self._survSelaNoCover[charID] = self.surviveProb(charID)
        self._survSelaCrit[charID] = self.surviveHits(charID)
        self._survSelaTwoHits[charID] = self.surviveHits(charID, 0, 2)

    def makeTeamStats(self, teamID):
        """Rebuilds the stats of the away team with the given ID and
        stores them for retrieval by the respective properties. Rebuilds
        the following stats: 'survivalProbs' and 'numSurvivors'. Sets
        stats to `None` if the away team is not full.

        Args:
            teamID (int): The ID of the away team, used internally by
                the Sela stat calculator.

        """
        team = self._awayTeams[teamID]
        teamNames = [char.name for char in team.items.values()]
        if team.length < 4:
            self._survivalProbs[teamID] = None
            self._numSurvivors[teamID] = None
            return
        self._survivalProbs[teamID] = MappingProxyType({
            cover: MappingProxyType(self.teamResults(teamID, cover))
            for cover in combinations(teamNames, 2)
        })
        self._numSurvivors[teamID] = MappingProxyType({
            cover: self.teamSurvivors(teamID, cover)
            for cover in combinations(teamNames, 2)
        })

    def surviveHits(self, charID, numCrit=1, numNormal=0, numGlance=0):
        """Check if the character can survive multiple hits from Sela's
        Surprise Attack.

        Args:
            charID (int): The ID of the character, used internally by
                the Sela stat calculator. If not provided, returns
                False. A value of None can be regarded as a ghost
                character that dies when Sela uses Surprise Attack, even
                if they are not hit by it.
            numCrit (int): The number of crit hits the character
                receives.
            numNormal (int): The number of normal hits the character
                receives.
            numGlance (int): The number of glancing hits the character
                receives.

        Returns:
            bool: True if the character survives.

        """
        char = self._registrants[charID]
        sela = self.sela

        health = char.health
        shield = char.particleEffects.get('shield', 0)
        tech = char.tech
        gd = char.gd

        healthLike = health + shield * tech

        selaCD = self.sela.cd
        selaTech = self.sela.tech

        dmgWhenCrit = max(
            0.65 * selaTech * selaCD - 0.38 * tech,
            1
        )
        dmgWhenNormal = max(
            0.65 * selaTech - 0.38 * tech,
            1
        )
        dmgWhenGlance = max(
            0.65 * selaTech * (1 - gd) - 0.38 * tech,
            1
        )
        dmgTotal = (
            numCrit * dmgWhenCrit 
            + numNormal * dmgWhenNormal
            + numGlance * dmgWhenGlance
        )

        return healthLike > dmgTotal

    def surviveProb(self, charID, numHits=None, cover=False):
        """Computes and returns the conditional probability that the
        character survives Sela's Surprise Attack, given that Sela
        targeted the character the given number of times.

        Args:
            charID (int): The ID of the character, used internally by
                the Sela stat calculator.
            numHits (int): The number of times Sela targets the
                character. If not provided, the probability is computed
                without conditioning on the number of hits.
            cover (bool): Set to True if the character is behind cover.

        Returns:
            float: The resulting probability.

        """
        if numHits is None:
            # Let
            #
            #   N = the number of times the character is hit,
            #   S = "The character survives."
            #
            # Then
            #
            #   P(S) = P(N = 0)P(S | N = 0) + P(N = 1)P(S | N = 1)
            #            + P(N = 2)P(S | N = 2) + P(N = 3)P(S | N = 3)
            #            + P(N = 4)P(S | N = 4)
            #        = P(N = 0) + P(N = 1)P(S | N = 1)
            #            + P(N = 2)P(S | N = 2) + P(N = 3)P(S | N = 3)
            #            + P(N = 4)P(S | N = 4),
            #
            # and
            #
            #   P(N = k) = \binom{4}{k} (1/4)^k (3/4)^{4-k}.
            #
            # Computing each separately, we get
            #
            #   P(N = 0) = (3/4)^4 = 81/256,
            #   P(N = 1) = 4(1/4)(3/4)^3 = (3/4)^3 = 27/64,
            #   P(N = 2) = 6(1/4)^2(3/4)^2 = 6(9)/(4^4) = 27/(2(4^3))
            #            = 27/128,
            #   P(N = 3) = 4(1/4)^3(3/4) = 3/(4^3) = 3/64,
            #   P(N = 4) = (1/4)^4 = 1/256.

            return (
                81/256
                +  (27/64) * self.surviveProb(charID, 1, cover)
                + (27/128) * self.surviveProb(charID, 2, cover)
                +   (3/64) * self.surviveProb(charID, 3, cover)
                +  (1/256) * self.surviveProb(charID, 4, cover)
            )
        if numHits == 0 or (numHits == 1 and cover == True):
            return 1
        numHits -= 1 if cover else 0

        # Let
        #
        #   N   = the number of times the character is hit,
        #   N_c = the number of those hits that are critical,
        #   N_n = the number of those hits that are normal,
        #   N_g = the number of those hits that glance.
        #
        # Note that N_c + N_n + N_g = N. Let
        #
        #   S = "The character survives."
        #
        # Let H = (N_c, N_n, N_g) and, for fixed k, let
        # 
        #   B = {b in {0,...,k}^3: b_0 + b_1 + b_2 = k}.
        # 
        # Then
        #
        #   P(S | N = k) = \sum_{b in B}
        #                    P(H = b | N = k)P(S | H = b, N = k)
        #                = \sum_{b in B}
        #                    P(H = b | N = k)P(S | H = b)
        # 
        # Notice that P(S | H = b) is either 0 or 1. Thus, if
        # Q(.) = P(.| N = k), then 
        # 
        #   P(S | N = k) = \sum_{b in B: (H = b) => S} Q(H = b)
        #
        # Let
        #
        #   r_c = the probability the first hit is a crit,
        #   r_n = the probability the first hit is normal,
        #   r_g = the probability the first hit glances.
        #
        # Then
        #
        #   Q(H = b) = (k!/(b_0!b_1!b_2!)) r_c^{b_0}r_n^{b_1}r_g^{b_2}.

        f = SelaStatCalc._factorial
        k = numHits

        charGC = self._registrants[charID].gc
        selaCC = self.sela.cc

        r_g = charGC
        r_c = (1 - r_g) * selaCC
        r_n = 1 - r_g - r_c

        prob = 0
        for b in fixedSum(k + 1, 3, k):
            if self.surviveHits(charID, *b):
                prob += (
                    ( f[k]/(f[b[0]] * f[b[1]] * f[b[2]]) )
                    * (r_c ** b[0]) * (r_n ** b[1]) * (r_g ** b[2])
                )
        return prob

    def teamResults(self, teamID, cover):
        """For each subset of the away team, computes the probability
        that the characters in this subset are the only survivors of
        Sela's Surprise Attack. The probabilities are returned as a
        dictionary. Cover is set with the `cover` argument.

        Args:
            teamID (int): The ID of the team facing Sela's Surprise
                Attack.
            cover (tuple of str): A 2-tuple of the names of the
                characters that are behind cover.

        Returns:
            dict of (tuple of str):float: A dictionary mapping subsets
                of the set of names of characters on the away team to
                the probability they are the only survivors of Sela's
                Surprise attack.
        """
        # 
        # Let S be a subset of the away team and
        # 
        #   C_S = "The members of S are the only survivors."
        # 
        # We want P(C_S). Number the away team members from 0 to 3. Let
        # 
        #   A_j = "The j-th character survives.",
        # 
        # and
        # 
        #   J = {j: the j-th character is in S}.
        # 
        # Then
        # 
        #   C_S = \bigcap_{j in J} A_j \cap \bigcap_{j in J^c} A_j^c.
        # 
        # Let
        #
        #   T_i = the number of the character that Sela targets
        #           with her i-th shot (0 <= i <= 3),
        #   N_j = the number of times the j-th character is targeted by
        #           Sela,
        #   T = (T_0, ..., T_3),
        #   N = (N_0, ..., N_3).
        #
        # Note that A_0, ..., A_3 are conditionally independent given T.
        # Thus,
        #
        #   P(C_S) = E[P(C_S | T)]
        #          = E[ \prod_{j in J} P(A_j | T)
        #                 * \prod_{j in J^c} P(A_j^c | T) ].
        #
        # Since P(A_j | T) and P(A_j^c | T) are functions of N_j, we
        # have
        #
        #   P(A_j | T)   = P(A_j | N_j),
        #   P(A_j^c | T) = P(A_j^c | N_j).
        #
        # This gives
        #
        #   P(C_S) = E[ \prod_{j in J} P(A_j | N_j)
        #               * \prod_{j in J^c} P(A_j^c | N_j) ]
        #          = \sum_{b in B} P(N = b)
        #               * \prod_{j in J}   P(A_j | N_j = b_j)
        #               * \prod_{j in J^c} P(A_j^c | N_j = b_j)
        #
        # where
        #
        #   B = {b in {0, ..., 4}^4: b_0 + ... + b_3 = 4}.
        #
        # We use the `surviveProb` method to compute P(A_j | N_j = b_j)
        # and P(A_j^c | N_j = b_j). The final piece is
        #
        #   P(N = b) = (4!/(b_0!b_1!b_2!b_3!)) ((1/4)^4)
        # 
        # Let r_b = P(N = b) and Q(S) = P(C_S). Then
        #
        #   r_b = 3/(2(4^2)b_0!b_1!b_2!b_3!)
        #       = (3/32)/(b_0!b_1!b_2!b_3!)
        #
        # and
        #
        #   Q(S) = \sum_{b in B} r_b
        #             * \prod_{j in J}   P(A_j | N_j = b_j)
        #             * \prod_{j in J^c} P(A_j^c | N_j = b_j)
        #
        # This method will return a dictionary mapping S to Q(S).

        f = SelaStatCalc._factorial
        chars = self._awayTeams[teamID].items.values()
        charNames = [char.name for char in chars]
        charIDs = [char.SSCid for char in chars]
        Q = {}
        for S in powerset(charNames):
            J = [charNames.index(name) for name in S]
            Q[S] = 0
            for b in fixedSum(5, 4, 4):
                r_b = (3/32)/(f[b[0]] * f[b[1]] * f[b[2]] * f[b[3]])
                prod = 1
                for j in range(4):
                    if j in J:
                        prod *= self.surviveProb(
                            charIDs[j], b[j], charNames[j] in cover
                        )
                    else:
                        prod *= 1 - self.surviveProb(
                            charIDs[j], b[j], charNames[j] in cover
                        )
                Q[S] += r_b * prod
        return Q

    def teamSurvivors(self, teamID, cover):
        """Computes the expected number of survivors of Sela's Surprise
        Attack, weighted by the weights assigned in the away team
        object. Cover is set with the `cover` argument.

        Args:
            teamID (int): The ID of the team facing Sela's Surprise
                Attack.
            cover (tuple of str): A 2-tuple of the names of the
                characters that are behind cover.

        Returns:
            float: The expected value of the sum of the weights of the

                survivors of Sela's Surprise Attack.        
        """
        # Let
        # 
        #   X = the total weights of surviving characters,
        #   w_j = the j-th weight (0 <= j <= 3),
        #   A_j = "The j-th character survives."
        # 
        # Then
        #
        #   X = \sum_{j=0}^3 w_j 1_{A_j},
        # 
        # and
        #
        #   E[X] = \sum_{j=0}^3 w_j P(A_j).

        team = self._awayTeams[teamID]
        chars = team.items.values()
        EX = 0
        for char in chars:
            EX += team.weights[char.name] * (
                char.selaStats['survSelaCover']
                if char.name in cover else
                char.selaStats['survSelaNoCover']
            )
        return EX
