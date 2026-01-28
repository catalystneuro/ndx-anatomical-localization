import numpy as np

from hdmf.common import DynamicTable
from pynwb.image import Image
from pynwb.ophys import ImagingPlane
from hdmf.utils import get_docval, AllowPositional

from pynwb import get_class, register_class, docval

TempSpace = get_class("Space", "ndx-anatomical-localization")
TempAllenCCFv3Space = get_class("AllenCCFv3Space", "ndx-anatomical-localization")
TempAnatomicalCoordinatesTable = get_class("AnatomicalCoordinatesTable", "ndx-anatomical-localization")
Localization = get_class("Localization", "ndx-anatomical-localization")
TempAnatomicalCoordinatesImage = get_class("AnatomicalCoordinatesImage", "ndx-anatomical-localization")

PREDEFINED_SPACES = {
    "CCFv3": {
        "name": "space",
        "space_name": "CCFv3",
        "origin": "In the middle of the anterior commissure",
        "units": "um",
        "orientation": "RAS",
    }
}


@register_class("Space", "ndx-anatomical-localization")
class Space(TempSpace):

    @docval(
        {"name": "name", "type": str, "doc": "name of the NWB object"},
        {"name": "space_name", "type": str, "doc": "name of the space"},
        {
            "name": "origin",
            "type": str,
            "doc": "A description of where (0,0,0) is in the space. For example, 'bregma' is a common origin for mice.",
        },
        {
            "name": "units",
            "type": str,
            "doc": "The units of measurement for the x,y,z coordinates. For example, 'mm' for millimeters.",
        },
        {
            "name": "orientation",
            "type": str,
            "doc": (
                """A 3-letter string indicating the positive direction along each axis, where the 1st letter
          is for x, 2nd for y, and 3rd for z. Each letter can be: A (Anterior), P (Posterior), L (Left),
          R (Right), S (Superior/Dorsal), or I (Inferior/Ventral). The three letters must cover all three
          anatomical dimensions (one from A/P, one from L/R, one from S/I). For example, 'RAS' means
          positive x is Right, positive y is Anterior, positive z is Superior.

          Notes:
          - These three dimensions are also commonly referred to as AP, ML, and DV.
          - This convention specifies positive directions (sometimes written as 'RAS+'), not origin
            location - use the 'origin' field to describe where (0,0,0) is located."""
            ),
        },
        {
            "name": "extent",
            "type": "array_data",
            "doc": "The spatial extent (bounding box dimensions) as [x, y, z]. Optional.",
            "default": None,
            "allow_none": True,
        },
        allow_positional=AllowPositional.ERROR,
    )
    def __init__(self, name, space_name, origin, units, orientation, extent=None):
        assert len(orientation) == 3, "orientation must be a string of length 3"
        valid_values = ["A", "P", "L", "R", "S", "I"]
        for x in orientation:
            assert x in valid_values, "orientation must be a string of 'A', 'P', 'L', 'R', 'S', 'I'"

        map = {"A": "AP", "P": "AP", "L": "LR", "R": "LR", "S": "SI", "I": "SI"}
        new_var = [map[var] for var in orientation]
        assert len(set(new_var)) == 3, "orientation must be unique dimensions (AP, LR, SI)"

        if extent is not None:
            extent = np.asarray(extent, dtype=np.float64)
            if extent.shape != (3,):
                raise ValueError("extent must be an array of shape (3,)")
            if np.any(extent <= 0):
                raise ValueError("extent values must be positive")

        super().__init__(
            name=name, space_name=space_name, origin=origin, units=units, orientation=orientation, extent=extent
        )


@register_class("AllenCCFv3Space", "ndx-anatomical-localization")
class AllenCCFv3Space(TempAllenCCFv3Space):
    """
    The Allen Mouse Brain Common Coordinate Framework version 3 (2020).

    This canonical space represents the CCFv3 atlas with fixed orientation and origin.
    Uses PIR orientation (positive x=Posterior, positive y=Inferior, positive z=Right)
    with 10 micrometer resolution. The origin (0,0,0) is at the Anterior-Superior-Left (ASL)
    corner of the 3D image volume.

    The atlas extent is 13200 x 8000 x 11400 micrometers (AP x DV x ML).
    """

    @docval(
        {"name": "name", "type": str, "doc": "name of the NWB object", "default": "AllenCCFv3"},
        allow_positional=AllowPositional.ERROR,
    )
    def __init__(self, name="AllenCCFv3"):
        super().__init__(
            name=name,
            space_name="AllenCCFv3",
            origin="Anterior-Superior-Left (ASL) corner of the 3D image volume",
            units="um",
            orientation="PIR",
            extent=np.array([13200.0, 8000.0, 11400.0]),
        )


@register_class("AnatomicalCoordinatesTable", "ndx-anatomical-localization")
class AnatomicalCoordinatesTable(TempAnatomicalCoordinatesTable):

    @docval(
        {"name": "space", "type": (Space, "AllenCCFv3Space"), "doc": "space of the table"},
        {"name": "method", "type": str, "doc": "method of the table"},
        {
            "name": "target",
            "type": DynamicTable,
            "doc": 'target table. ignored if a "localized_entity" column is provided in "columns"',
            "default": None,
        },
        *get_docval(DynamicTable.__init__),
        allow_positional=AllowPositional.ERROR,
    )
    def __init__(self, **kwargs):
        columns = kwargs.get("columns")
        target = kwargs.pop("target")
        if not columns or "localized_entity" not in [c.name for c in columns]:
            # set target table of "localized_entity" column only if not already in "columns"
            if target is None:
                raise ValueError(
                    '"target" (the target table that contains the objects that have these coordinates) '
                    "must be provided in AnatomicalCoordinatesTable.__init__ "
                    'if the "localized_entity" column is not in "columns".'
                )
            kwargs["target_tables"] = {"localized_entity": target}

        super().__init__(**kwargs)


@register_class("AnatomicalCoordinatesImage", "ndx-anatomical-localization")
class AnatomicalCoordinatesImage(TempAnatomicalCoordinatesImage):

    @docval(
        {"name": "name", "type": str, "doc": "name of the NWB object"},
        {"name": "description", "type": str, "doc": "description of the NWB object", "default": None},
        {"name": "space", "type": (Space, "AllenCCFv3Space"), "doc": "space of the image"},
        {"name": "method", "type": str, "doc": "method of the image"},
        {"name": "image", "type": Image, "doc": "The image associated with the coordinates", "default": None},
        {
            "name": "imaging_plane",
            "type": ImagingPlane,
            "doc": "The imaging plane associated with the coordinates",
            "default": None,
        },
        {
            "name": "x",
            "type": ("array_data", "data"),
            "doc": "2D array containing X coordinates for each pixel (width x height)",
        },
        {
            "name": "y",
            "type": ("array_data", "data"),
            "doc": "2D array containing Y coordinates for each pixel (width x height)",
        },
        {
            "name": "z",
            "type": ("array_data", "data"),
            "doc": "2D array containing Z coordinates for each pixel (width x height)",
        },
        {
            "name": "brain_region",
            "type": ("array_data", "data"),
            "doc": "2D array of brain region names for each pixel",
            "default": None,
        },
        {
            "name": "brain_region_id",
            "type": ("array_data", "data"),
            "doc": "2D array of brain region IDs for each pixel (corresponding to atlas ontology)",
            "default": None,
        },
        allow_positional=AllowPositional.ERROR,
    )
    def __init__(self, **kwargs):
        image = kwargs.get("image")
        imaging_plane = kwargs.get("imaging_plane")

        x = kwargs["x"]
        y = kwargs["y"]
        z = kwargs["z"]
        if image is not None and imaging_plane is not None:
            raise ValueError(
                'Only one of "image" or "imaging_plane" can be provided in AnatomicalCoordinatesImage.__init__ '
            )
        if image is None and imaging_plane is None:
            raise ValueError('"image" or "imaging_plane" must be provided in AnatomicalCoordinatesImage.__init__ ')
        if image is not None:
            # verify that x, y, z have the same shape as the image data
            if x.shape != image.data.shape or y.shape != image.data.shape or z.shape != image.data.shape:
                raise ValueError(
                    f'"x", "y", and "z" must have the same shape as the image data. '
                    f"x.shape: {x.shape}, y.shape: {y.shape}, z.shape: {z.shape}, "
                    f"image.data.shape: {image.data.shape}"
                )
        super().__init__(**kwargs)

    def get_coordinates(self, i=None, j=None):
        """Get the anatomical coordinates at a specific pixel or for the entire image.

        Args:
            i (int, optional): The row index of the pixel. Defaults to None.
            j (int, optional): The column index of the pixel. Defaults to None.
        Returns:
            tuple or np.ndarray: The anatomical coordinates at the specified pixel (i, j) as a tuple,
            or the entire coordinate arrays stacked along the last axis if i and j are not provided.
        """

        import numpy as np

        if i is not None and j is not None:
            return (self.x[i, j], self.y[i, j], self.z[i, j])
        else:
            return np.stack([self.x[:], self.y[:], self.z[:]], axis=-1)
