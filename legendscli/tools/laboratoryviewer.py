"""This module contains the `LaboratoryViewer` class.

"""

from types import MappingProxyType
from legendscli.utils.pool import PoolViewer

class LaboratoryViewer(PoolViewer):
    """A PoolViewer subclass for Laboratory objects.

    """

    def __init__(self, laboratory):
        """Creates a LaboratoryViewer object to view the given
        laboratory, then applies the default sorting, which is first by
        descending rarity, then by descending level.

        Args:
            laboratory (Laboratory): The laboratory to associate with
                the viewer.

        """
        PoolViewer.__init__(self, laboratory)
        self.sort('level', reverse=True)
        self.sort('tier', reverse=True)

    def makeDisplayStats(self, particle=None, safe=True):
        """(override) Makes a simplified dictionary of particle
        statistics, suitable for displaying in a spreadsheet, then
        stores it for retrieval by the `displayStats` property.

        Args:
            particle (Particle): Uses statistics from this particle. If
                no character is provided, the method is run on every
                particle in the associated laboratory.
            safe (bool): Set to False to skip checking for the given
                particle in the associated laboratory.

        Raises:
            ValueError: If the given particle is not in the associated
                laboratory.

        """
        if particle is None:
            for particle in self._pool.items.values():
                self.makeDisplayStats(particle, False)
            return
        if safe and particle not in self._pool.items.values():
            raise ValueError('particle not in laboratory')
        displayStats = {'id': particle.inPool[1]}
        attrs = ['type_', 'level', 'rarity', 'tier']
        displayStats.update({attr: getattr(particle, attr) for attr in attrs})
        for j in range(4):
            if j < len(particle.statList):
                displayStats['stat' + str(j)] = particle.statList[j]
            else:
                displayStats['stat' + str(j)] = ''
        if particle.equippedOn is None:
            displayStats['equippedOn'] = ''
            displayStats['slot'] = ''
        else:
            displayStats['equippedOn'] = particle.equippedOn[0].name
            displayStats['slot'] = particle.equippedOn[1]
        displayStats.update(particle.stats)
        self._displayStats[particle.inPool[1]] = displayStats

