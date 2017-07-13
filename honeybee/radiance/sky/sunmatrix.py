from ._skyBase import RadianceSky
from .gendaylit import gendaylit

from ladybug.dt import DateTime
from ladybug.sunpath import Sunpath
from ladybug.wea import Wea

import os


class SunMatrix(RadianceSky):
    """Radiance sun matrix (analemma) created from weather file.

    Attributes:
        wea: An instance of ladybug Wea.
        north: An angle in degrees between 0-360 to indicate north direction
            (Default: 0).
        hoys: The list of hours for generating the sky matrix (Default: 0..8759)

    Usage:

        from honeybee.radiance.sky.sunmatrix import SunMatrix
        epwfile = r".\USA_CA_San.Francisco.Intl.AP.724940_TMY3.epw"
        sunmtx = SunMatrix.fromEpwFile(epwfile, north=20)
        analemma, sunlist, sunmtxfile = sunmtx.execute('c:/ladybug')
    """

    def __init__(self, wea, north=0, hoys=None):
        """Create sun matrix."""
        RadianceSky.__init__(self)
        self.wea = wea
        self.north = north
        self.hoys = hoys or range(8760)

    @classmethod
    def fromEpwFile(cls, epwFile, north=0, hoys=None):
        """Create sun matrix from an epw file."""
        return cls(Wea.fromEpwFile(epwFile), north, hoys)

    @property
    def isSunMatrix(self):
        """Return True."""
        return True

    @property
    def isClimateBased(self):
        """Return True if the sky is generated from values from weather file."""
        return True

    @property
    def wea(self):
        """An instance of ladybug Wea."""
        return self._wea

    @wea.setter
    def wea(self, w):
        assert hasattr(w, 'isWea'), \
            TypeError('wea must be a WEA object not a {}'.format(type(w)))
        self._wea = w

    @property
    def north(self):
        """An angle in degrees between 0-360 to indicate north direction (Default: 0)."""
        return self._north

    @north.setter
    def north(self, n):
        north = n or 0
        self._north = north

    @property
    def name(self):
        """Sky default name."""
        return "sunmtx_r{}_{}_{}_{}".format(
            self.wea.location.stationId,
            self.wea.location.latitude,
            self.wea.location.longitude,
            self.north
        )

    @property
    def analemmafile(self):
        """Analemma file."""
        return self.name + '.ann'

    @property
    def sunlistfile(self):
        """Sun list file."""
        return self.name + '.sun'

    @property
    def sunmtxfile(self):
        """Sun matrix file."""
        return self.name + '.mtx'

    def hoursMatch(self, hoursFile):
        """Check if hours in the hours file matches the hours of wea."""
        if not os.path.isfile(hoursFile):
            return False

        with open(hoursFile, 'r') as hrf:
            line = hrf.read()

        found = line == ','.join(str(h) for h in self.hoys) + '\n'

        if found:
            print('Reusing SunMatrix: {}.'.format(self.sunmtxfile))

        return found

    def execute(self, workingDir, reuse=True):
        """Generate sun matrix.

        Args:
            workingDir: Folder to execute and write the output.
            reuse: Reuse the matrix if already existed in the folder.

        Returns:
            Full path to analemma, sunlist and sunmatrix.
        """
        fp = os.path.join(workingDir, self.analemmafile)
        lfp = os.path.join(workingDir, self.sunlistfile)
        mfp = os.path.join(workingDir, self.sunmtxfile)
        hrf = os.path.join(workingDir, self.name + '.hrs')

        if reuse:
            if self.hoursMatch(hrf):
                for f in (fp, lfp, mfp):
                    if not os.path.isfile(f):
                        break
                else:
                    print('Found the sun matrix!')
                    return fp, lfp, mfp

        with open(hrf, 'wb') as outf:
            outf.write(','.join(str(h) for h in self.hoys) + '\n')

        wea = self.wea
        monthDateTime = (DateTime.fromHoy(idx) for idx in self.hoys)
        latitude, longitude = wea.location.latitude, -wea.location.longitude

        sp = Sunpath.fromLocation(wea.location, self.north)
        solarradiances = []
        sunValues = []
        sunUpHours = []  # collect hours that sun is up
        solarstring = \
            'void light solar{0} 0 0 3 {1} {1} {1} ' \
            'solar{0} source sun 0 0 4 {2:.6f} {3:.6f} {4:.6f} 0.533'

        # use gendaylit to calculate radiation values for each hour.
        print('Calculating sun positions and radiation values.')
        count = 0
        for timecount, timeStamp in enumerate(monthDateTime):
            month, day, hour = timeStamp.month, timeStamp.day, timeStamp.hour + 0.5
            dnr, dhr = int(wea.directNormalRadiation[timeStamp.intHOY]), \
                int(wea.diffuseHorizontalRadiation[timeStamp.intHOY])
            if dnr == 0:
                continue
            count += 1
            sun = sp.calculateSun(month, day, hour)
            if sun.altitude < 0:
                continue
            x, y, z = sun.sunVector
            solarradiance = int(gendaylit(sun.altitude, month, day, hour, dnr, dhr))
            curSunDefinition = solarstring.format(count, solarradiance, -x, -y, -z)
            solarradiances.append(solarradiance)
            sunValues.append(curSunDefinition)
            # keep the number of hour relative to hoys in this sun matrix
            sunUpHours.append(timecount)

        sunCount = len(sunUpHours)

        print('# Number of sun up hours: %d' % sunCount)
        print('Writing sun positions and radiation values to {}'.format(fp))
        # create solar discs.
        with open(fp, 'w') as annfile:
            annfile.write("\n".join(sunValues))
            annfile.write('\n')

        print('Writing list of suns to {}'.format(lfp))
        # create list of suns.
        with open(lfp, 'w') as sunlist:
            sunlist.write(
                "\n".join(("solar%s" % (idx + 1) for idx in xrange(sunCount)))
            )
            sunlist.write('\n')

        # Start creating header for the sun matrix.
        fileHeader = ['#?RADIANCE']
        fileHeader += ['Sun matrix created by Honeybee']
        fileHeader += ['LATLONG= %s %s' % (latitude, -longitude)]
        fileHeader += ['NROWS=%s' % sunCount]
        fileHeader += ['NCOLS=%s' % len(self.hoys)]
        fileHeader += ['NCOMP=3']
        fileHeader += ['FORMAT=ascii']

        print('Writing sun matrix to {}'.format(mfp))
        # Write the matrix to file.
        with open(mfp, 'w') as sunMtx:
            sunMtx.write('\n'.join(fileHeader) + '\n' + '\n')
            for idx, sunValue in enumerate(solarradiances):
                sunRadList = ['0 0 0'] * len(self.hoys)
                sunRadList[sunUpHours[idx]] = '{0} {0} {0}'.format(sunValue)
                sunMtx.write('\n'.join(sunRadList) + '\n\n')

            sunMtx.write('\n')

        return fp, lfp, mfp

    def toRadString(self, workingDir, writeHours=False):
        """Get the radiance command line as a string."""
        raise AttributeError(
            'SunMatrix does not have a single line command. Try execute method.'
        )

    def ToString(self):
        """Overwrite .NET ToString method."""
        return self.__repr__()

    def __repr__(self):
        """Sky representation."""
        return self.name
