# ndx-anatomical-localization Extension for NWB

Provide localization of objects (e.g. electrodes) against a reference image (e.g. CCF).

Often in neurophysiology, you have a set of electrodes or other objects that you want to localize against a reference image.
This extension provides a way to store the coordinates of these objects in a standardized way.
This is done using a table that stores the coordinates of the objects in a given space (e.g. CCFv3) and a reference to the object that is localized (e.g. an electrode table).
This method allows for the storage of multiple localizations in the same file that may correspond to different spaces or registration methods.

## Installation

```bash
pip install git+https://github.com/catalystneuro/ndx-anatomical-localization.git
```

## Usage

### Spaces
`Space` objects are used to define the coordinate system in which the objects are localized.
Each Space object has the following attributes:
  * `space_name`: The name of the space (e.g. "AllenCCFv3")
  * `origin`: The origin of the space (e.g. "bregma" or "Dorsal-left-posterior corner of the 3D image volume")
  * `units`: The units of the space (e.g. "um")
  * `orientation`: A 3-letter string using A (Anterior), P (Posterior), L (Left), R (Right), S (Superior), I (Inferior) for each of x, y, and z axes (e.g. "RAS" or "ASL").

You can define a custom space by creating a `Space` object with the desired attributes:

```python
from ndx_anatomical_localization import Space

space = Space(
    name="MySpace",
    space_name="MySpace",
    origin="bregma",
    units="um",
    orientation="RAS",
)
```

#### Allen Mouse Brain Common Coordinate Framework v3 (CCFv3)

The Allen Institute CCFv3 atlas is available as a canonical space class `AllenCCFv3Space` with fixed orientation and origin parameters:
- **Orientation**: ASL (x=Anterior-Posterior, y=Superior-Inferior/Dorsal-Ventral, z=Left-Right)
- **Units**: micrometers (um)
- **Resolution**: 10 micrometers isotropic
- **Origin**: Dorsal-left-posterior corner of the 3D image volume
- **Dimensions**: 1320 x 800 x 1140 voxels

You can create this canonical space directly:

```python
from ndx_anatomical_localization import AllenCCFv3Space

space = AllenCCFv3Space()
```

The `AllenCCFv3Space` instance can be programmatically identified using `isinstance(space, AllenCCFv3Space)`.

### AnatomicalCoordinatesTable
Once you have a `Space` object, you can create an `AnatomicalCoordinatesTable`.
The "localized_entity" attribute is a reference to the object that is localized (e.g. an electrode table).
x, y, and z columns store the coordinates of the objects in the given space and brain_region allows you to optionally also store the localized brain region.
You can also add custom columns to this table, for example to express certainty or quality of the localization.

### Localization
The `Localization` object is used to store the spaces and anatomical coordinates tables in the /general section of the NWB file.
Within `Localization`, you can create multiple `Space` and `AnatomicalCoordinatesTable` objects to store localizations of different entities or localizations of the same entity using different methods or spaces.

```python
from pynwb.testing.mock.file import mock_NWBFile
from pynwb.testing.mock.ecephys import mock_ElectrodeTable

from ndx_anatomical_localization import AnatomicalCoordinatesTable, AllenCCFv3Space, Localization


nwbfile = mock_NWBFile()

localization = Localization()
nwbfile.add_lab_meta_data([localization])

electrodes_table = mock_ElectrodeTable(nwbfile=nwbfile)

space = AllenCCFv3Space()
localization.add_spaces([space])

table = AnatomicalCoordinatesTable(
    name="MyAnatomicalLocalization",
    target=electrodes_table,
    description="Anatomical coordinates table",
    method="SHARP-Track 1.0",
    space=space,
)
[table.add_row(x=1.0, y=2.0, z=3.0, brain_region="CA1", localized_entity=x) for x in range(5)]

localization.add_anatomical_coordinates_tables([table])
```

---
This extension was created using [ndx-template](https://github.com/nwb-extensions/ndx-template).
