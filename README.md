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
  * `orientation`: A 3-letter string indicating the positive direction along each axis, where the 1st letter is for x, the 2nd for y, and the 3rd for z. Each letter can be one of: A (Anterior), P (Posterior), L (Left), R (Right), S (Superior/Dorsal), or I (Inferior/Ventral). The three letters must cover all three anatomical dimensions (one from A/P, one from L/R, one from S/I). For example:
    - "RAS" means positive x is Right, positive y is Anterior, positive z is Superior
    - "PIR" means positive x is Posterior, positive y is Inferior, positive z is Right

    **Notes**:
    - The three anatomical dimensions are also commonly referred to as AP (Anterior-Posterior), ML (Medial-Lateral), and DV (Dorsal-Ventral).
    - This convention specifies *positive directions*, not origin location. This is sometimes written as "RAS+" (with a plus sign) to make this explicit. Some tools (e.g., [BrainGlobe](https://brainglobe.info/documentation/setting-up/image-definition.html#orientation)) use a similar three-letter code to indicate where the origin is located instead - for example, "RAS" in that convention would mean the origin is at the Right-Anterior-Superior corner, which is equivalent to "LPI+" in the positive-direction convention. We use the positive-direction convention here; use the `origin` field to describe where (0,0,0) is located.

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
- **Orientation**: PIR (positive x=Posterior, positive y=Inferior, positive z=Right)
- **Units**: micrometers (um)
- **Resolution**: 10 micrometers isotropic
- **Origin**: Anterior-Superior-Left (ASL) corner of the 3D image volume
- **Dimensions**: 1320 x 800 x 1140 voxels

You can create this canonical space directly:

```python
from ndx_anatomical_localization import AllenCCFv3Space

space = AllenCCFv3Space()
```

The `AllenCCFv3Space` instance can be programmatically identified using `isinstance(space, AllenCCFv3Space)`.

#### Macaque Atlas Spaces

Three canonical macaque atlas spaces are also available as predefined classes. All use RAS orientation and millimeter units.

These atlases differ not only in origin but in the **alignment convention** that defines the orientation of the horizontal plane through the brain. This distinction matters because a point at the same (x, y, z) coordinate maps to a different physical location depending on which convention is used:

- **AC-PC alignment**: The horizontal plane passes through the anterior commissure (AC) and the posterior commissure (PC). This is defined by internal brain landmarks.
- **Horsley-Clarke alignment**: The horizontal plane is defined by the ear bars and the infraorbital ridge of the stereotaxic frame. This is defined by external skull landmarks. The Horsley-Clarke plane is typically tilted several degrees relative to the AC-PC plane.

Each predefined space class hardcodes the correct origin and alignment convention, so users don't need to specify these details manually.

**D99v2Space** (Reveley et al. 2017; Saleem et al. 2021): Origin at the anterior commissure, horizontal plane aligned to the AC-PC line.

```python
from ndx_anatomical_localization import D99v2Space

space = D99v2Space()
```

**NMTv2Space** (Jung et al. 2021): Origin at ear bar zero (intersection of the midsagittal plane and interaural line), horizontal plane aligned to the Horsley-Clarke stereotaxic convention.

```python
from ndx_anatomical_localization import NMTv2Space

space = NMTv2Space()
```

**NMTv2AsymmetricSpace** (Jung et al. 2021): Same origin and alignment as `NMTv2Space`, but preserves population-level hemispheric differences instead of enforcing symmetry. Note that the CHARM and SARM parcellations are only defined on the symmetric variant.

```python
from ndx_anatomical_localization import NMTv2AsymmetricSpace

space = NMTv2AsymmetricSpace()
```

**MEBRAINSSpace** (Balan et al. 2024): Origin at the anterior commissure, horizontal plane approximately aligned to the Horsley-Clarke convention.

```python
from ndx_anatomical_localization import MEBRAINSSpace

space = MEBRAINSSpace()
```

Each class can be programmatically identified using `isinstance()`, e.g. `isinstance(space, D99v2Space)`.

### AnatomicalCoordinatesTable
Once you have a `Space` object, you can create an `AnatomicalCoordinatesTable`.
The "localized_entity" attribute is a reference to the object that is localized (e.g. an electrode table).
x, y, and z columns store the coordinates of the objects in the given space and brain_region allows you to optionally also store the localized brain region.
You can also add custom columns to this table, for example to express certainty or quality of the localization.

### AnatomicalCoordinatesImage
For imaging data, you can use `AnatomicalCoordinatesImage` to store anatomical coordinates as 2D arrays that map pixels in an image to anatomical locations.
This is useful when you want to localize a field of view or register imaging data to a reference atlas.

Each `AnatomicalCoordinatesImage` requires:
- An `Image` object (required) — the reference image (e.g. mean or max projection) on which the coordinate map is based
- A `localized_entity` (optional) — a `OnePhotonSeries` or `TwoPhotonSeries` that this coordinate map applies to

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

---

### BrainRegionMasks
`BrainRegionMasks` is a `DynamicTable` that maps pixels in the original imaging space to brain region IDs.
Each row stores the `(x, y)` pixel coordinates and the corresponding `brain_region_id` from the atlas ontology.

#### When to use `BrainRegionMasks` vs `AnatomicalCoordinatesImage`

**Prefer `AnatomicalCoordinatesImage`** when you have full atlas coordinates for every pixel (x, y, z). 
This is the richer representation: it preserves all spatial information, lets downstream users choose any segmentation 
level of the atlas hierarchy. 

**Use `BrainRegionMasks`** when per-pixel atlas coordinates are unavailable.

```python
from ndx_anatomical_localization import BrainRegionMasks

masks = BrainRegionMasks(name="source_brain_region_id_masks", description="Pixel masks for primary visual cortex in source image space.")
masks.add_row(x=10, y=20, brain_region_id=385)
masks.add_row(x=11, y=20, brain_region_id=385)
masks.add_row(x=10, y=21, brain_region_id=385)

```


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

#### Example with image and localized_entity

```python
from pynwb.testing.mock.file import mock_NWBFile
from pynwb.testing.mock.ophys import mock_TwoPhotonSeries
from pynwb.base import Images
from pynwb.image import GrayscaleImage
import numpy as np

from ndx_anatomical_localization import AnatomicalCoordinatesImage, AllenCCFv3Space, Localization

nwbfile = mock_NWBFile()

localization = Localization()
nwbfile.add_lab_meta_data([localization])

# Create a reference image (e.g. mean projection of the FOV)
nwbfile.create_processing_module("ophys", "ophys")
nwbfile.processing["ophys"].add(Images(name="SummaryImages", description="Summary images"))
image_collection = nwbfile.processing["ophys"].data_interfaces["SummaryImages"]
image_collection.add_image(GrayscaleImage(name="MeanImage", data=np.ones((512, 512)), description="Mean projection"))

# The recording series this coordinate map applies to
two_photon_series = mock_TwoPhotonSeries(nwbfile=nwbfile, name="TwoPhotonSeries")

space = AllenCCFv3Space()
localization.add_spaces([space])

image_coordinates = AnatomicalCoordinatesImage(
    name="MyAnatomicalLocalization",
    image=image_collection["MeanImage"],
    localized_entity=two_photon_series,
    method="manual registration",
    space=space,
    x=np.ones((512, 512)),
    y=np.ones((512, 512)) * 2.0,
    z=np.ones((512, 512)) * 3.0,
    brain_region=np.full((512, 512), "VISp"),
)

localization.add_anatomical_coordinates_images([image_coordinates])
```

#### Example with BrainRegionMasks

```python
from pynwb.testing.mock.file import mock_NWBFile
from ndx_anatomical_localization import BrainRegionMasks, Localization
import numpy as np

nwbfile = mock_NWBFile()

localization = Localization()
nwbfile.add_lab_meta_data([localization])

masks = BrainRegionMasks(name="source_brain_region_id_masks", description="Pixel masks for primary visual cortex in source image space.")
masks.add_row(x=10, y=20, brain_region_id=385)
masks.add_row(x=11, y=20, brain_region_id=385)
masks.add_row(x=10, y=21, brain_region_id=385)

localization.add_brain_region_masks([masks])
```
---

### AtlasRegistration
`AtlasRegistration` is a `LabMetaData` container that documents the registration *provenance* — i.e., what images, 
transformations, and landmarks were used to register the imaging data to the atlas. 
It is separate from the localization results (coordinates, brain region masks) which live under `Localization`.

`AtlasRegistration` requires `source_image` and `registered_image` links and supports optional `atlas_projection`, 
`affine_transformation`, and `landmarks`.

#### AffineTransformation
`AffineTransformation` stores a 3×3 affine transformation matrix in homogeneous coordinates, supporting 2D operations: 
translation, rotation, scaling, and shearing.

```python
from ndx_anatomical_localization import AffineTransformation
import numpy as np

affine = AffineTransformation(
    name="affine_transformation",
    affine_matrix=np.array([[0.99, -0.14, 50.0],
                             [0.14,  0.99, 30.0],
                             [0.0,   0.0,   1.0]]),
)
```

#### Landmarks
`Landmarks` is a `DynamicTable` storing point correspondences between the source image space and the reference atlas. 
Required columns are `source_x` and `source_y`. Optional columns include `registered_x`/`registered_y` 
(transformed source coordinates), `reference_x`/`reference_y` (atlas coordinates), `landmark_labels`, and `confidence`.

```python
from ndx_anatomical_localization import Landmarks

landmarks = Landmarks(name="landmarks", description="Landmark correspondences between FOV and atlas")
landmarks.add_row(
    source_x=100.0, 
    source_y=200.0,
    reference_x=5500.0, 
    reference_y=3500.0,
    landmark_labels="bregma",
    confidence=0.97,
)
landmarks.add_row(
    source_x=150.0, 
    source_y=250.0,
    reference_x=6200.0, 
    reference_y=3100.0,
    landmark_labels="lambda",
    confidence=0.92,
)
```

#### Full AtlasRegistration example

`AtlasRegistration` has a fixed name `"atlas_registration"` in the NWB file. It is added directly to the NWBFile via `add_lab_meta_data`, not inside `Localization`.

```python
from pynwb.testing.mock.file import mock_NWBFile
from pynwb.base import Images
from pynwb.image import GrayscaleImage
import numpy as np

from ndx_anatomical_localization import (
    AtlasRegistration,
    AffineTransformation,
    Landmarks,
)

nwbfile = mock_NWBFile()

nwbfile.create_processing_module("ophys", "ophys")
nwbfile.processing["ophys"].add(Images(name="RegistrationImages", description="Images used in atlas registration"))
image_collection = nwbfile.processing["ophys"].data_interfaces["RegistrationImages"]
image_collection.add_image(GrayscaleImage(name="SourceFOV", data=np.ones((512, 512)), description="Mean projection of the FOV"))
image_collection.add_image(GrayscaleImage(name="RegisteredFOV", data=np.ones((512, 512)), description="FOV after affine registration to atlas"))
image_collection.add_image(GrayscaleImage(name="AtlasProjection", data=np.ones((512, 512)), description="Coronal atlas slice at the registration plane"))

affine = AffineTransformation(
    name="affine_transformation",
    affine_matrix=np.array([[0.99, -0.14, 50.0],
                             [0.14,  0.99, 30.0],
                             [0.0,   0.0,   1.0]]),
)

landmarks = Landmarks(name="landmarks", description="Landmark correspondences between FOV and atlas")
landmarks.add_row(source_x=100.0, source_y=200.0, reference_x=5500.0, reference_y=3500.0, landmark_labels="bregma", confidence=0.97)
landmarks.add_row(source_x=150.0, source_y=250.0, reference_x=6200.0, reference_y=3100.0, landmark_labels="lambda", confidence=0.92)

registration = AtlasRegistration(
    source_image=image_collection["SourceFOV"],
    registered_image=image_collection["RegisteredFOV"],
    atlas_projection=image_collection["AtlasProjection"],
    affine_transformation=affine,
    landmarks=landmarks,
)
nwbfile.add_lab_meta_data([registration])
```


---
This extension was created using [ndx-template](https://github.com/nwb-extensions/ndx-template).
