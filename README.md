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
  * `space_name`: The name of the space (e.g. "CCFv3")
  * `origin`: The origin of the space (e.g. "bregma")
  * `units`: The units of the space (e.g. "um")
  * `orientation`: A 3-letter string. One of A, P, L, R, S, I for each of x, y, and z (e.g. "RAS").

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

The Allen Institute Common Coordinate Framework v3 is predefined and can be accessed using the `get_predefined_space` method, or you can define a custom space.
You can use the following syntax to use this space:

```python
from ndx_anatomical_localization import Space

space = Space.get_predefined_space("CCFv3")
```

### AnatomicalCoordinatesTable
Once you have a `Space` object, you can create an `AnatomicalCoordinatesTable`.
The "localized_entity" attribute is a reference to the object that is localized (e.g. an electrode table).
x, y, and z columns store the coordinates of the objects in the given space and brain_region allows you to optionally also store the localized brain region.
You can also add custom columns to this table, for example to express certainty or quality of the localization.

### AnatomicalCoordinatesImage
For imaging data, you can use `AnatomicalCoordinatesImage` to store anatomical coordinates as 2D arrays that map pixels in an image to anatomical locations.
This is useful when you want to localize a field of view or register imaging data to a reference atlas.

Each `AnatomicalCoordinatesImage` must be associated with either:
- An `ImagingPlane` object (for optical physiology experiments)
- An `Image` object (for static reference images)

The x, y, and z datasets store 2D arrays of coordinates for each pixel in the image, x[i, j], y[i, j], z[i, j] give the anatomical coordinates location for pixel (i, j).
The `get_coordinates()` function return the image with anatomical coordinates per pixel:

                       j=0             j=1             j=2
                    ──────────────────────────────────────────────
                  │               │               │               │
         i=0      │   x: 2.10     │   x: 2.11     │   x: 2.12     │
                  │   y: -3.40    │   y: -3.40    │   y: -3.40    │
                  │   z: 1.20     │   z: 1.20     │   z: 1.20     │
                  │               │               │               │
                  ├───────────────┼───────────────┼───────────────┤
                  │               │               │               │
         i=1      │   x: 2.10     │   x: 2.11     │   x: 2.12     │
                  │   y: -3.41    │   y: -3.41    │   y: -3.41    │
                  │   z: 1.20     │   z: 1.20     │   z: 1.20     │
                  │               │               │               │
                  ├───────────────┼───────────────┼───────────────┤
                  │               │               │               │
         i=2      │   x: 2.10     │   x: 2.11     │   x: 2.12     │
                  │   y: -3.42    │   y: -3.42    │   y: -3.42    │
                  │   z: 1.20     │   z: 1.20     │   z: 1.20     │
                  │               │               │               │
                   ───────────────────────────────────────────────

Each pixel stores its anatomical coordinates (x, y, z)


### Localization
The `Localization` object is used to store the spaces and anatomical coordinates tables in the /general section of the NWB file.
Within `Localization`, you can create multiple `Space` and `AnatomicalCoordinatesTable` objects to store localizations of different entities or localizations of the same entity using different methods or spaces.

```python
from pynwb.testing.mock.file import mock_NWBFile
from pynwb.testing.mock.ecephys import mock_ElectrodeTable

from ndx_anatomical_localization import AnatomicalCoordinatesTable, Space, Localization


nwbfile = mock_NWBFile()

localization = Localization()
nwbfile.add_lab_meta_data([localization])

electrodes_table = mock_ElectrodeTable(nwbfile=nwbfile)

space = Space.get_predefined_space("CCFv3")
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

#### Example with ImagingPlane

```python
from pynwb.testing.mock.file import mock_NWBFile
from pynwb.testing.mock.ophys import mock_ImagingPlane
import numpy as np

from ndx_anatomical_localization import AnatomicalCoordinatesImage, Space, Localization

nwbfile = mock_NWBFile()

localization = Localization()
nwbfile.add_lab_meta_data([localization])

imaging_plane = mock_ImagingPlane(nwbfile=nwbfile)

space = Space.get_predefined_space("CCFv3")
localization.add_spaces([space])

image_coordinates = AnatomicalCoordinatesImage(
    name="MyAnatomicalLocalization",
    imaging_plane=imaging_plane,
    method="manual registration",
    space=space,
    x=np.ones((5, 5)),
    y=np.ones((5, 5)) * 2.0,
    z=np.ones((5, 5)) * 3.0,
    brain_region=np.array([["CA1"] * 5] * 5),
)

localization.add_anatomical_coordinates_images([image_coordinates])
```

#### Example with Image

```python
from pynwb.testing.mock.file import mock_NWBFile
from pynwb.base import Images
from pynwb.image import GrayscaleImage
import numpy as np

from ndx_anatomical_localization import AnatomicalCoordinatesImage, Space, Localization

nwbfile = mock_NWBFile()

localization = Localization()
nwbfile.add_lab_meta_data([localization])

# Create an image to localize
if "ophys" not in nwbfile.processing:
    nwbfile.create_processing_module("ophys", "ophys")

nwbfile.processing["ophys"].add(Images(name="SummaryImages", description="Summary images container"))
image_collection = nwbfile.processing["ophys"].data_interfaces["SummaryImages"]
image_collection.add_image(GrayscaleImage(name="MyImage", data=np.ones((5, 5)), description="An example image"))

space = Space.get_predefined_space("CCFv3")
localization.add_spaces([space])

image_coordinates = AnatomicalCoordinatesImage(
    name="MyAnatomicalLocalization",
    image=image_collection["MyImage"],
    method="manual registration",
    space=space,
    x=np.ones((5, 5)),
    y=np.ones((5, 5)) * 2.0,
    z=np.ones((5, 5)) * 3.0,
    brain_region=np.array([["CA1"] * 5] * 5),
)

localization.add_anatomical_coordinates_images([image_coordinates])
```

---
This extension was created using [ndx-template](https://github.com/nwb-extensions/ndx-template).
