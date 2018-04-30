"""Radiance Glass Material.

http://radsite.lbl.gov/radiance/refer/ray.html#Glass
"""
import math
from materialbase import RadianceMaterial


class Glass(RadianceMaterial):
    """Radiance glass material."""

    def __init__(self, name, r_transmittance=0, g_transmittance=0, b_transmittance=0,
                 refraction=1.52, modifier="void"):
        """Create glass material.

        Attributes:
            name: Material name as a string. Do not use white space and special character
            r_transmittance: Transmittance for red. The value should be between 0 and 1
                (Default: 0).
            g_transmittance: Transmittance for green. The value should be between 0 and 1
                (Default: 0).
            b_transmittance: Transmittance for blue. The value should be between 0 and 1
                (Default: 0).
            refraction: Index of refraction. 1.52 for glass and 1.4 for ETFE
                (Default: 1.52).
            modifier: Material modifier (Default: "void").

        Usage:
            glassMaterial = Glass("generic glass", .65, .65, .65)
            print(glassMaterial)
        """
        RadianceMaterial.__init__(self, name, type="glass", modifier=modifier)
        self.r_transmittance = float(r_transmittance)
        """Transmittance for red. The value should be between 0 and 1 (Default: 0)."""
        self.g_transmittance = float(g_transmittance)
        """Transmittance for green. The value should be between 0 and 1 (Default: 0)."""
        self.b_transmittance = float(b_transmittance)
        """Transmittance for blue. The value should be between 0 and 1 (Default: 0)."""
        self.refractionIndex = float(refraction)
        """Index of refraction. 1.52 for glass and 1.4 for ETFE (Default: 1.52)."""

    @classmethod
    def from_json(cls, rec_json):
        """Make radiance material from json
        {
            "name": "", // Material Name
            "r_transmittance": float, // Transmittance for red
            "g_transmittance": float, // Transmittance for green
            "b_transmittance": float, // Transmittance for blue
            "refraction": float, // Index of refraction
            "modifier": "" // material modifier (Default: "void")
        }
        """
        return cls(name=rec_json["name"],
                   r_transmittance=rec_json["r_transmittance"],
                   g_transmittance=rec_json["g_transmittance"],
                   b_transmittance=rec_json["b_transmittance"],
                   refraction=rec_json["refraction"],
                   modifier=rec_json["modifier"])

    @classmethod
    def by_single_trans_value(cls, name, rgb_transmittance=0,
                              refraction=1.52, modifier="void"):
        """Create glass material with single transmittance value.

        Attributes:
            name: Material name as a string. Do not use white space and special
                character.
            rgb_transmittance: Transmittance for red, green and blue. The value should be
                between 0 and 1 (Default: 0).
            refraction: Index of refraction. 1.52 for glass and 1.4 for ETFE
                (Default: 1.52).
            modifier: Material modifier (Default: "void").

        Usage:
            glassMaterial = Glass.by_single_trans_value("generic glass", .65)
            print(glassMaterial)
        """
        return cls(
            name, r_transmittance=rgb_transmittance, g_transmittance=rgb_transmittance,
            b_transmittance=rgb_transmittance, refraction=1.52, modifier="void")

    @classmethod
    def from_string(cls, material_string, modifier=None):
        """Create a Radiance material from a string.

        If the material has a modifier the modifier material should also be part of the
        string or should be provided using modifier argument.
        """

        modifier, name, base_material_data = cls._analyze_string_input(
            cls.__name__.lower(), material_string, modifier)

        if len(base_material_data) == 6:
            r_transmittance, g_transmittance, b_transmittance = base_material_data[3:]
            refraction = 1.52
        else:
            r_transmittance, g_transmittance, b_transmittance, refraction = \
                base_material_data[3:]

        return cls(name, r_transmittance, g_transmittance, b_transmittance, refraction,
                   modifier)

    @property
    def isGlassMaterial(self):
        """Indicate if this object has glass Material.

        This property will be used to separate the glass surfaces in a separate
        file than the opaque surfaces.
        """
        return True

    @property
    def r_transmittance(self):
        """Red transmittance."""
        return self.__r

    @r_transmittance.setter
    def r_transmittance(self, value):
        assert 0 <= value <= 1, "Red transmittance should be between 0 and 1"
        self.__r = value

    @property
    def g_transmittance(self):
        """Green transmittance."""
        return self.__g

    @g_transmittance.setter
    def g_transmittance(self, value):
        assert 0 <= value <= 1, "Green transmittance should be between 0 and 1"
        self.__g = value

    @property
    def b_transmittance(self):
        """Blue transmittance."""
        return self.__b

    @b_transmittance.setter
    def b_transmittance(self, value):
        assert 0 <= value <= 1, "Blue transmittance should be between 0 and 1"
        self.__b = value

    @property
    def average_transmittance(self):
        """Calculate average transmittance."""
        return 0.265 * self.r_transmittance + \
            0.670 * self.g_transmittance + 0.065 * self.b_transmittance

    @staticmethod
    def get_transmissivity(transmittance):
        """Calculate transmissivity based on transmittance value.

        "Transmissivity is the amount of light not absorbed in one traversal of
        the material. Transmittance -- the value usually measured - is the total
        light transmitted through the pane including multiple reflections."
        """
        if transmittance == 0:
            return 0
        return (math.sqrt(0.8402528435 + 0.0072522239 * (transmittance ** 2)) -
                0.9166530661) / 0.0036261119 / transmittance

    def to_rad_string(self, minimal=False):
        """Return full radiance definition."""
        __base_string = self.head_line(minimal) + "0\n0\n4 %.3f %.3f %.3f %.3f"

        glass_definition = __base_string % (
            self.get_transmissivity(self.r_transmittance),
            self.get_transmissivity(self.g_transmittance),
            self.get_transmissivity(self.b_transmittance),
            self.refractionIndex
        )

        return glass_definition.replace("\n", " ") if minimal else glass_definition

    def to_json(self):
        """Translate radiance material to json
        {
            "type": "glass", // Material type
            "name": "", // Material Name
            "r_transmittance": float, // Transmittance for red
            "g_transmittance": float, // Transmittance for green
            "b_transmittance": float, // Transmittance for blue
            "refraction": float, // Index of refraction
            "modifier": "" // material modifier (Default: "void")
        }
        """
        return {
            "type": "glass",
            "name": self.name,
            "r_transmittance": self.r_transmittance,
            "g_transmittance": self.g_transmittance,
            "b_transmittance": self.b_transmittance,
            "refraction": self.refractionIndex,
            "modifier": "void"
        }


if __name__ == "__main__":
    # some test code
    glassMaterial = Glass.by_single_trans_value("generic glass", .65)
    print(glassMaterial)
    print(glassMaterial.to_rad_string(minimal=True))
