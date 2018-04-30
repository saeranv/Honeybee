"""Radiance BSDF Material.

http://radsite.lbl.gov/radiance/refer/ray.html#Glass
"""
import os
from materialbase import RadianceMaterial


# TODO(): Add function file, transform and additional diffuse reflectance front and back
# and additional diffuse transmittance
class BSDF(RadianceMaterial):
    """Radiance BSDF material.

    Attributes:
        xmlfile: Path to an xml file. Data will not be cached in memory.
        up_orientation: (x, y ,z) vector that sets the hemisphere that the
            BSDF material faces.  For materials that are symmetrical about
            the HBSrf plane (like non-angled venitian blinds), this can be
            any vector that is not perfectly normal to the HBSrf. For
            asymmetrical materials like angled veneitan blinds, this variable
            should be coordinated with the direction the HBSrfs are facing.
            The default is set to (0.01, 0.01, 1.00), which should hopefully
            not be perpendicular to any typical HBSrf.
        thickness: Optional number to set the thickness of the BSDF material.
            (default: 0).
        modifier: Material modifier (Default: "void").
    """

    def __init__(self, xmlfile, up_orientation=None, thickness=None, modifier="void",
                 name=None):
        """Create BSDF material."""
        assert os.path.isfile(xmlfile), 'Invalid path: {}'.format(xmlfile)
        assert xmlfile.lower().endswith('.xml'), 'Invalid xml file: {}'.format(xmlfile)

        self.xmlfile = os.path.normpath(xmlfile)

        name = name or '.'.join(os.path.split(self.xmlfile)[-1].split('.')[:-1])

        RadianceMaterial.__init__(self, name, type="BSDF", modifier=modifier)

        try:
            x, y, z = up_orientation or (0.01, 0.01, 1.00)
        except TypeError as e:
            try:
                # Dynamo!
                x, y, z = up_orientation.X, up_orientation.Y, up_orientation.Z
            except AttributeError:
                # raise the original error
                raise TypeError(str(e))

        self.up_orientation = float(x), float(y), float(z)

        self.thickness = thickness or 0

        with open(self.xmlfile, 'rb') as inf:
            for count, line in enumerate(inf):
                if line.strip().startswith('<AngleBasisName>'):
                    self._angle_basis = line.replace('<AngleBasisName>', '') \
                        .replace('</AngleBasisName>', '').replace('LBNL/', '').strip()
                    break

                assert count < 100, 'Failed to find AngleBasisName in first 100 lines.'

    @classmethod
    def from_string(cls, material_string, modifier=None):
        """Create a Radiance material from a string.

        If the material has a modifier the modifier material should also be part of the
        string or should be provided using modifier argument.
        """

        modifier, name, base_material_data = cls._analyze_string_input(
            cls.__name__, material_string, modifier)

        assert base_material_data[0] == '6' and base_material_data[6] == '.', \
            'BSDF currently does not support function file and transform. ' \
            'You can use Custom material to create this BSDF material.'

        assert base_material_data[8] == '0', \
            'BSDF currently does not support additional transmissions or reflections. ' \
            'You can use Custom material to create this BSDF material.'

        thickness, xmlfile, upx, upy, upz = base_material_data[1:6]

        return cls(xmlfile, (upx, upy, upz), thickness, modifier, name)

    @property
    def isGlassMaterial(self):
        """Indicate if this object has glass Material.

        This property will be used to separate the glass surfaces in a separate
        file than the opaque surfaces.
        """
        return True

    @property
    def angle_basis(self):
        """XML file angle basis.

        Klems full, Klems half, Klems Quarter or tensor tree
        """
        return self._angle_basis

    def to_rad_string(self, minimal=False):
        """Return full radiance definition."""
        base_string = self.head_line(minimal) + "6 %.3f %s %.3f %.3f %.3f .\n0\n0\n"

        mat_def = base_string % (float(self.thickness),
                                 os.path.normpath(self.xmlfile),
                                 self.up_orientation[0],
                                 self.up_orientation[1],
                                 self.up_orientation[2])

        return mat_def.replace("\n", " ") if minimal else mat_def


if __name__ == "__main__":
    # some test code
    material = BSDF(
        r"C:/Users/Administrator/Documents/GitHub/honeybee/tests/room/xmls/clear.xml")
    print(material)
