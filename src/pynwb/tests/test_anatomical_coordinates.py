"""Unit and integration tests for the new neurodata type."""

from pynwb import NWBHDF5IO
from pynwb.base import Images
from pynwb.image import GrayscaleImage
from pynwb.testing.mock.file import mock_NWBFile
from pynwb.testing.mock.ecephys import mock_ElectrodeTable
from pynwb.testing.mock.ophys import mock_ImagingPlane
import numpy as np
import numpy.testing as npt

from ndx_anatomical_localization import (
    AnatomicalCoordinatesImage,
    AnatomicalCoordinatesTable,
    Space,
    AllenCCFv3Space,
    Localization,
    Landmarks,
    AffineTransformation,
    BrainRegionMasks,
    AtlasRegistration,
)


def test_create_custom_space():
    Space(
        name="MySpace",
        space_name="MySpace",
        origin="bregma",
        units="um",
        orientation="RAS",
    )


def test_create_anatomical_coordinates_table():

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
        method="method",
        space=space,
    )
    [table.add_row(x=1.0, y=2.0, z=3.0, brain_region="CA1", localized_entity=x) for x in range(5)]

    localization.add_anatomical_coordinates_tables([table])

    with NWBHDF5IO("test.nwb", "w") as io:
        io.write(nwbfile)

    with NWBHDF5IO("test.nwb", "r", load_namespaces=True) as io:
        read_nwbfile = io.read()
        read_electrodes_table = read_nwbfile.electrodes
        read_localization = read_nwbfile.lab_meta_data["localization"]

        read_coordinates_table = read_localization.anatomical_coordinates_tables["MyAnatomicalLocalization"]

        assert read_coordinates_table.method == "method"
        assert read_coordinates_table.description == "Anatomical coordinates table"
        assert read_coordinates_table.localized_entity.table is read_electrodes_table
        assert isinstance(read_coordinates_table.space, AllenCCFv3Space)
        assert read_coordinates_table.space.space_name == "AllenCCFv3"
        npt.assert_array_equal(read_coordinates_table["x"].data[:], np.array([1.0, 1.0, 1.0, 1.0, 1.0]))
        npt.assert_array_equal(read_coordinates_table["y"].data[:], np.array([2.0, 2.0, 2.0, 2.0, 2.0]))
        npt.assert_array_equal(read_coordinates_table["z"].data[:], np.array([3.0, 3.0, 3.0, 3.0, 3.0]))
        expected_regions = np.array(["CA1", "CA1", "CA1", "CA1", "CA1"])
        npt.assert_array_equal(read_coordinates_table["brain_region"].data[:], expected_regions)
        npt.assert_array_equal(read_coordinates_table["localized_entity"].data[:], np.array([0, 1, 2, 3, 4]))


def test_create_allen_ccfv3_space():
    """Test creating AllenCCFv3Space directly."""
    space = AllenCCFv3Space()

    assert space.name == "AllenCCFv3"
    assert space.space_name == "AllenCCFv3"
    assert space.orientation == "PIR"
    assert space.units == "um"
    assert space.origin == "Anterior-Superior-Left (ASL) corner of the 3D image volume"
    expected_extent = np.array([13200.0, 8000.0, 11400.0])
    npt.assert_array_equal(space.extent, expected_extent)


def test_create_allen_ccfv3_space_custom_name():
    """Test creating AllenCCFv3Space with custom name."""
    space = AllenCCFv3Space(name="my_ccf_space")

    assert space.name == "my_ccf_space"
    assert space.space_name == "AllenCCFv3"
    assert space.orientation == "PIR"


def test_allen_ccfv3_space_write_read():
    """Test that AllenCCFv3Space type is preserved through write/read cycle."""
    nwbfile = mock_NWBFile()
    localization = Localization()
    nwbfile.add_lab_meta_data([localization])

    electrodes_table = mock_ElectrodeTable(nwbfile=nwbfile)

    space = AllenCCFv3Space()
    localization.add_spaces([space])

    table = AnatomicalCoordinatesTable(
        name="CCFLocalization",
        target=electrodes_table,
        description="CCF coordinates",
        method="manual annotation",
        space=space,
    )
    table.add_row(x=100.0, y=200.0, z=300.0, brain_region="VISp", localized_entity=0)

    localization.add_anatomical_coordinates_tables([table])

    with NWBHDF5IO("test_ccf.nwb", "w") as io:
        io.write(nwbfile)

    with NWBHDF5IO("test_ccf.nwb", "r", load_namespaces=True) as io:
        read_nwbfile = io.read()
        read_localization = read_nwbfile.lab_meta_data["localization"]
        read_table = read_localization.anatomical_coordinates_tables["CCFLocalization"]

        # Verify that the space is still an AllenCCFv3Space instance
        assert isinstance(read_table.space, AllenCCFv3Space)
        assert read_table.space.space_name == "AllenCCFv3"
        assert read_table.space.orientation == "PIR"
        assert read_table.space.origin == "Anterior-Superior-Left (ASL) corner of the 3D image volume"
        npt.assert_array_equal(read_table.space.extent, np.array([13200.0, 8000.0, 11400.0]))


def test_anatomical_coordinates_image_with_allen_ccfv3_space():
    nwbfile = mock_NWBFile()

    localization = Localization()
    nwbfile.add_lab_meta_data([localization])

    imaging_name = "ImagingPlaneCCFv3SpaceTest"
    imaging_plane = mock_ImagingPlane(nwbfile=nwbfile, name=imaging_name)

    space = AllenCCFv3Space()
    localization.add_spaces([space])

    image_coordinates = AnatomicalCoordinatesImage(
        name="MyAnatomicalLocalization",
        imaging_plane=imaging_plane,
        method="method",
        space=space,
        x=np.ones((5, 5)),
        y=np.ones((5, 5)) * 2.0,
        z=np.ones((5, 5)) * 3.0,
        brain_region=np.array([["CA1"] * 5] * 5),
    )

    localization.add_anatomical_coordinates_images([image_coordinates])

    with NWBHDF5IO("test_image_ccf.nwb", "w") as io:
        io.write(nwbfile)

    with NWBHDF5IO("test_image_ccf.nwb", "r", load_namespaces=True) as io:
        read_nwbfile = io.read()
        read_imaging_plane = read_nwbfile.imaging_planes[imaging_name]
        read_localization = read_nwbfile.lab_meta_data["localization"]

        read_coordinates_image = read_localization.anatomical_coordinates_images["MyAnatomicalLocalization"]

        assert read_coordinates_image.method == "method"
        assert read_coordinates_image.imaging_plane is read_imaging_plane
        assert isinstance(read_coordinates_image.space, AllenCCFv3Space)
        npt.assert_array_equal(
            read_coordinates_image.x[:],
            np.ones((5, 5)),
        )
        npt.assert_array_equal(
            read_coordinates_image.y[:],
            np.ones((5, 5)) * 2.0,
        )
        npt.assert_array_equal(
            read_coordinates_image.z[:],
            np.ones((5, 5)) * 3.0,
        )
        npt.assert_array_equal(read_coordinates_image.brain_region[:], np.array([["CA1"] * 5] * 5))


def test_create_anatomical_coordinates_image_w_imaging_plane():

    nwbfile = mock_NWBFile()

    localization = Localization()
    nwbfile.add_lab_meta_data([localization])

    imaging_plane_name = "ImagingPlane"
    imaging_plane = mock_ImagingPlane(nwbfile=nwbfile, name=imaging_plane_name)

    space = Space(
        name="MySpace",
        space_name="MySpace",
        origin="bregma",
        units="um",
        orientation="RAS",
    )
    localization.add_spaces([space])

    image_coordinates = AnatomicalCoordinatesImage(
        name="MyAnatomicalLocalization",
        imaging_plane=imaging_plane,
        method="method",
        space=space,
        x=np.ones((5, 5)),
        y=np.ones((5, 5)) * 2.0,
        z=np.ones((5, 5)) * 3.0,
        brain_region=np.array([["CA1"] * 5] * 5),
    )

    localization.add_anatomical_coordinates_images([image_coordinates])

    with NWBHDF5IO("test_image.nwb", "w") as io:
        io.write(nwbfile)

    with NWBHDF5IO("test_image.nwb", "r", load_namespaces=True) as io:
        read_nwbfile = io.read()
        read_imaging_plane = read_nwbfile.imaging_planes["ImagingPlane"]
        read_localization = read_nwbfile.lab_meta_data["localization"]

        read_coordinates_image = read_localization.anatomical_coordinates_images["MyAnatomicalLocalization"]

        assert read_coordinates_image.method == "method"
        assert read_coordinates_image.imaging_plane is read_imaging_plane
        assert read_coordinates_image.space.origin == "bregma"
        npt.assert_array_equal(
            read_coordinates_image.x[:],
            np.ones((5, 5)),
        )
        npt.assert_array_equal(
            read_coordinates_image.y[:],
            np.ones((5, 5)) * 2.0,
        )
        npt.assert_array_equal(
            read_coordinates_image.z[:],
            np.ones((5, 5)) * 3.0,
        )
        npt.assert_array_equal(read_coordinates_image.brain_region[:], np.array([["CA1"] * 5] * 5))


def test_create_anatomical_coordinates_image_w_image():

    nwbfile = mock_NWBFile()

    localization = Localization()
    nwbfile.add_lab_meta_data([localization])

    if "ophys" not in nwbfile.processing:
        nwbfile.create_processing_module("ophys", "ophys")

    nwbfile.processing["ophys"].add(Images(name="SummaryImages", description="Summary images container"))
    image_collection = nwbfile.processing["ophys"].data_interfaces["SummaryImages"]
    image_collection.add_image(GrayscaleImage(name="MyImage", data=np.ones((5, 5)), description="An example image"))

    space = Space(
        name="MySpace",
        space_name="MySpace",
        origin="bregma",
        units="um",
        orientation="RAS",
    )
    localization.add_spaces([space])

    image_coordinates = AnatomicalCoordinatesImage(
        name="MyAnatomicalLocalization",
        image=image_collection["MyImage"],
        method="method",
        space=space,
        x=np.ones((5, 5)),
        y=np.ones((5, 5)) * 2.0,
        z=np.ones((5, 5)) * 3.0,
        brain_region=np.array([["CA1"] * 5] * 5),
    )

    localization.add_anatomical_coordinates_images([image_coordinates])

    with NWBHDF5IO("test_image.nwb", "w") as io:
        io.write(nwbfile)

    with NWBHDF5IO("test_image.nwb", "r", load_namespaces=True) as io:
        read_nwbfile = io.read()
        read_summary_image = read_nwbfile.processing["ophys"]["SummaryImages"]["MyImage"]
        read_localization = read_nwbfile.lab_meta_data["localization"]

        read_coordinates_image = read_localization.anatomical_coordinates_images["MyAnatomicalLocalization"]

        assert read_coordinates_image.method == "method"
        assert read_coordinates_image.image is read_summary_image
        assert read_coordinates_image.space.origin == "bregma"
        npt.assert_array_equal(
            read_coordinates_image.x[:],
            np.ones((5, 5)),
        )
        npt.assert_array_equal(
            read_coordinates_image.y[:],
            np.ones((5, 5)) * 2.0,
        )
        npt.assert_array_equal(
            read_coordinates_image.z[:],
            np.ones((5, 5)) * 3.0,
        )
        npt.assert_array_equal(read_coordinates_image.brain_region[:], np.array([["CA1"] * 5] * 5))


def test_create_anatomical_coordinates_image_failing_no_image_or_plane():
    """
    No image or imaging_plane provided should raise ValueError
    """

    nwbfile = mock_NWBFile()

    localization = Localization()
    nwbfile.add_lab_meta_data([localization])

    space = Space(
        name="MySpace",
        space_name="MySpace",
        origin="bregma",
        units="um",
        orientation="RAS",
    )
    localization.add_spaces([space])
    try:
        _ = AnatomicalCoordinatesImage(
            name="MyAnatomicalLocalization",
            method="method",
            space=space,
            x=np.ones((5, 5)),
            y=np.ones((5, 5)) * 2.0,
            z=np.ones((5, 5)) * 3.0,
            brain_region=np.array([["CA1"] * 5] * 5),
        )
    except ValueError as e:
        assert str(e) == '"image" or "imaging_plane" must be provided in AnatomicalCoordinatesImage.__init__ '


def test_create_anatomical_coordinates_image_failing_shape_mismatch():
    """
    Mismatched shape between image and x,y,z should raise ValueError
    """

    nwbfile = mock_NWBFile()

    localization = Localization()
    nwbfile.add_lab_meta_data([localization])

    space = Space(
        name="MySpace",
        space_name="MySpace",
        origin="bregma",
        units="um",
        orientation="RAS",
    )
    localization.add_spaces([space])

    if "ophys" not in nwbfile.processing:
        nwbfile.create_processing_module("ophys", "ophys")

    nwbfile.processing["ophys"].add(Images(name="SummaryImages", description="Summary images container"))
    image_collection = nwbfile.processing["ophys"].data_interfaces["SummaryImages"]
    image_collection.add_image(GrayscaleImage(name="MyImage", data=np.ones((5, 5)), description="An example image"))
    x = np.ones((4, 5))
    y = np.ones((5, 5)) * 2.0
    z = np.ones((5, 5)) * 3.0
    try:
        _ = AnatomicalCoordinatesImage(
            name="MyAnatomicalLocalization",
            image=image_collection["MyImage"],
            method="method",
            space=space,
            x=np.ones((4, 5)),
            y=np.ones((5, 5)) * 2.0,
            z=np.ones((5, 5)) * 3.0,
            brain_region=np.array([["CA1"] * 5] * 5),
        )

    except ValueError as e:
        assert str(e) == (
            f'"x", "y", and "z" must have the same shape as the image data. '
            f"x.shape: {x.shape}, y.shape: {y.shape}, z.shape: {z.shape}, "
            f"image.data.shape: {image_collection['MyImage'].data.shape}"
        )


def test_create_anatomical_coordinates_image_failing_both_image_and_plane():
    """
    Both image and imaging_plane provided should raise ValueError
    """

    nwbfile = mock_NWBFile()

    localization = Localization()
    nwbfile.add_lab_meta_data([localization])

    imaging_plane = mock_ImagingPlane(nwbfile=nwbfile)

    space = Space(
        name="MySpace",
        space_name="MySpace",
        origin="bregma",
        units="um",
        orientation="RAS",
    )
    localization.add_spaces([space])
    try:
        _ = AnatomicalCoordinatesImage(
            name="MyAnatomicalLocalization",
            imaging_plane=imaging_plane,
            image=None,
            method="method",
            space=space,
            x=np.ones((5, 5)),
            y=np.ones((5, 5)) * 2.0,
            z=np.ones((5, 5)) * 3.0,
            brain_region=np.array([["CA1"] * 5] * 5),
        )
    except ValueError as e:
        assert (
            str(e) == 'Only one of "image" or "imaging_plane" can be provided in AnatomicalCoordinatesImage.__init__ '
        )


def test_get_coordinates():

    nwbfile = mock_NWBFile()

    localization = Localization()
    nwbfile.add_lab_meta_data([localization])

    imaging_plane = mock_ImagingPlane(nwbfile=nwbfile)

    space = Space(
        name="MySpace",
        space_name="MySpace",
        origin="bregma",
        units="um",
        orientation="RAS",
    )
    localization.add_spaces([space])

    x_data = np.array([[0, 1, 2], [3, 4, 5], [6, 7, 8]])
    y_data = np.array([[10, 11, 12], [13, 14, 15], [16, 17, 18]])
    z_data = np.array([[20, 21, 22], [23, 24, 25], [26, 27, 28]])

    coords = AnatomicalCoordinatesImage(
        name="TestCoordinates",
        imaging_plane=imaging_plane,
        method="test_method",
        space=space,
        x=x_data,
        y=y_data,
        z=z_data,
    )

    # Test retrieving coordinates for specific pixel
    i, j = 1, 2
    coord = coords.get_coordinates(i=i, j=j)
    expected_coord = (x_data[i, j], y_data[i, j], z_data[i, j])
    npt.assert_array_equal(coord, expected_coord)

    # Test retrieving all coordinates
    all_coords = coords.get_coordinates()
    expected_all_coords = np.stack([x_data, y_data, z_data], axis=-1)
    npt.assert_array_equal(all_coords, expected_all_coords)


# ---------------------------------------------------------------------------
# Landmarks
# ---------------------------------------------------------------------------


def test_create_landmarks():
    table = Landmarks(name="landmarks", description="test landmarks")
    table.add_row(source_x=10.0, source_y=20.0)
    table.add_row(source_x=30.0, source_y=40.0)
    assert len(table) == 2


def test_create_landmarks_with_optional_columns():
    table = Landmarks(name="landmarks", description="test landmarks with optional cols")
    table.add_row(source_x=10.0, source_y=20.0, registered_x=10.5, registered_y=20.5)
    table.add_row(source_x=30.0, source_y=40.0, registered_x=31.0, registered_y=41.0)
    assert len(table) == 2


def test_landmarks_write_read():
    nwbfile = mock_NWBFile()
    nwbfile.create_processing_module("ophys", "ophys")
    nwbfile.processing["ophys"].add(Images(name="SummaryImages", description="summary images"))
    image_collection = nwbfile.processing["ophys"].data_interfaces["SummaryImages"]
    image_collection.add_image(GrayscaleImage(name="SourceImage", data=np.ones((5, 5)), description="source FOV"))
    image_collection.add_image(
        GrayscaleImage(name="RegisteredImage", data=np.ones((5, 5)), description="registered FOV")
    )

    landmarks = Landmarks(name="landmarks", description="landmark correspondences")
    landmarks.add_row(
        source_x=100.0, source_y=200.0, reference_x=5000.0, reference_y=3000.0,
        landmark_labels="bregma", confidence=0.95
    )
    landmarks.add_row(
        source_x=150.0, source_y=250.0, reference_x=6000.0, reference_y=4000.0,
        landmark_labels="lambda", confidence=0.90
    )

    registration = AtlasRegistration(
        source_image=image_collection["SourceImage"],
        registered_image=image_collection["RegisteredImage"],
        landmarks=landmarks,
    )
    nwbfile.add_lab_meta_data([registration])

    with NWBHDF5IO("test_landmarks.nwb", "w") as io:
        io.write(nwbfile)

    with NWBHDF5IO("test_landmarks.nwb", "r", load_namespaces=True) as io:
        read_nwbfile = io.read()
        read_registration = read_nwbfile.lab_meta_data["atlas_registration"]
        read_landmarks = read_registration.landmarks

        assert isinstance(read_landmarks, Landmarks)
        npt.assert_array_equal(read_landmarks["source_x"].data[:], np.array([100.0, 150.0], dtype=np.float32))
        npt.assert_array_equal(read_landmarks["source_y"].data[:], np.array([200.0, 250.0], dtype=np.float32))
        npt.assert_array_equal(read_landmarks["landmark_labels"].data[:], np.array(["bregma", "lambda"]))
        npt.assert_array_almost_equal(read_landmarks["confidence"].data[:], np.array([0.95, 0.90], dtype=np.float32))


# ---------------------------------------------------------------------------
# AffineTransformation
# ---------------------------------------------------------------------------


def test_create_affine_transformation():
    matrix = np.eye(3)
    affine = AffineTransformation(name="affine_transformation", affine_matrix=matrix)
    npt.assert_array_equal(affine.affine_matrix, matrix)


def test_affine_transformation_invalid_shape():
    try:
        AffineTransformation(name="affine_transformation", affine_matrix=np.eye(4))
    except ValueError as e:
        assert str(e) == "Affine matrix must be a 3x3 array. Provided shape: (4, 4)"


def test_affine_transformation_write_read():
    nwbfile = mock_NWBFile()
    nwbfile.create_processing_module("ophys", "ophys")
    nwbfile.processing["ophys"].add(Images(name="SummaryImages", description="summary images"))
    image_collection = nwbfile.processing["ophys"].data_interfaces["SummaryImages"]
    image_collection.add_image(GrayscaleImage(name="SourceImage", data=np.ones((5, 5)), description="source FOV"))
    image_collection.add_image(
        GrayscaleImage(name="RegisteredImage", data=np.ones((5, 5)), description="registered FOV")
    )

    matrix = np.array([[0.99, -0.14, 50.0], [0.14, 0.99, 30.0], [0.0, 0.0, 1.0]])
    affine = AffineTransformation(name="affine_transformation", affine_matrix=matrix)

    registration = AtlasRegistration(
        source_image=image_collection["SourceImage"],
        registered_image=image_collection["RegisteredImage"],
        affine_transformation=affine,
    )
    nwbfile.add_lab_meta_data([registration])

    with NWBHDF5IO("test_affine.nwb", "w") as io:
        io.write(nwbfile)

    with NWBHDF5IO("test_affine.nwb", "r", load_namespaces=True) as io:
        read_nwbfile = io.read()
        read_registration = read_nwbfile.lab_meta_data["atlas_registration"]
        read_affine = read_registration.affine_transformation

        assert isinstance(read_affine, AffineTransformation)
        npt.assert_array_almost_equal(read_affine.affine_matrix[:], matrix)


# ---------------------------------------------------------------------------
# BrainRegionMasks
# ---------------------------------------------------------------------------


def test_create_brain_region_masks():
    masks = BrainRegionMasks(name="source_brain_region_id_masks", description="pixel masks")
    masks.add_row(x=10, y=20, brain_region_id=1)
    masks.add_row(x=11, y=20, brain_region_id=1)
    masks.add_row(x=10, y=21, brain_region_id=2)
    assert len(masks) == 3


def test_brain_region_masks_write_read():
    nwbfile = mock_NWBFile()
    localization = Localization()
    nwbfile.add_lab_meta_data([localization])

    space = AllenCCFv3Space()
    localization.add_spaces([space])

    src_masks = BrainRegionMasks(name="source_brain_region_id_masks", description="source pixel masks")
    src_masks.add_row(x=0, y=0, brain_region_id=1)
    src_masks.add_row(x=1, y=0, brain_region_id=2)

    reg_masks = BrainRegionMasks(name="registered_brain_region_id_masks", description="registered pixel masks")
    reg_masks.add_row(x=0, y=0, brain_region_id=1)
    reg_masks.add_row(x=1, y=0, brain_region_id=2)

    localization.add_brain_region_masks([src_masks, reg_masks])

    with NWBHDF5IO("test_masks.nwb", "w") as io:
        io.write(nwbfile)

    with NWBHDF5IO("test_masks.nwb", "r", load_namespaces=True) as io:
        read_nwbfile = io.read()
        read_localization = read_nwbfile.lab_meta_data["localization"]

        read_src = read_localization.brain_region_masks["source_brain_region_id_masks"]
        read_reg = read_localization.brain_region_masks["registered_brain_region_id_masks"]

        assert isinstance(read_src, BrainRegionMasks)
        assert isinstance(read_reg, BrainRegionMasks)
        npt.assert_array_equal(read_src["x"].data[:], np.array([0, 1], dtype=np.uint32))
        npt.assert_array_equal(read_src["brain_region_id"].data[:], np.array([1, 2], dtype=np.uint32))
        npt.assert_array_equal(read_reg["y"].data[:], np.array([0, 0], dtype=np.uint32))


# ---------------------------------------------------------------------------
# AtlasRegistration
# ---------------------------------------------------------------------------


def test_atlas_registration_missing_images():
    try:
        AtlasRegistration()
    except Exception as e:
        assert str(e) == "'source_image', 'registered_image' must be provided in AtlasRegistration.__init__"


def test_atlas_registration_missing_registered_image():
    """Creating AtlasRegistration without the required registered_image should raise an error."""
    source_img = GrayscaleImage(name="SourceImage", data=np.ones((5, 5)), description="source")

    try:
        AtlasRegistration(source_image=source_img)
    except Exception as e:
        assert str(e) == "'registered_image' must be provided in AtlasRegistration.__init__"


def test_atlas_registration_with_image_write_read():
    nwbfile = mock_NWBFile()
    localization = Localization()
    nwbfile.add_lab_meta_data([localization])

    nwbfile.create_processing_module("ophys", "ophys")
    nwbfile.processing["ophys"].add(Images(name="SummaryImages", description="summary"))
    image_collection = nwbfile.processing["ophys"].data_interfaces["SummaryImages"]
    image_collection.add_image(GrayscaleImage(name="SourceImage", data=np.ones((5, 5)), description="source FOV"))
    image_collection.add_image(
        GrayscaleImage(name="RegisteredImage", data=np.ones((5, 5)) * 2, description="registered FOV")
    )
    image_collection.add_image(GrayscaleImage(name="AtlasProjection", data=np.ones((5, 5)) * 3, description="atlas"))

    space = AllenCCFv3Space()
    localization.add_spaces([space])

    matrix = np.eye(3)
    affine = AffineTransformation(name="affine_transformation", affine_matrix=matrix)

    registration = AtlasRegistration(
        source_image=image_collection["SourceImage"],
        registered_image=image_collection["RegisteredImage"],
        atlas_projection=image_collection["AtlasProjection"],
        affine_transformation=affine,
    )
    nwbfile.add_lab_meta_data([registration])

    with NWBHDF5IO("test_atlas_registration.nwb", "w") as io:
        io.write(nwbfile)

    with NWBHDF5IO("test_atlas_registration.nwb", "r", load_namespaces=True) as io:
        read_nwbfile = io.read()
        read_src_image = read_nwbfile.processing["ophys"]["SummaryImages"]["SourceImage"]
        read_registration = read_nwbfile.lab_meta_data["atlas_registration"]

        assert isinstance(read_registration, AtlasRegistration)
        assert read_registration.source_image is read_src_image
        assert isinstance(read_registration.affine_transformation, AffineTransformation)
        npt.assert_array_almost_equal(read_registration.affine_transformation.affine_matrix[:], np.eye(3))


def test_atlas_registration_with_landmarks_write_read():
    nwbfile = mock_NWBFile()
    localization = Localization()
    nwbfile.add_lab_meta_data([localization])

    nwbfile.create_processing_module("ophys", "ophys")
    nwbfile.processing["ophys"].add(Images(name="SummaryImages", description="summary"))
    image_collection = nwbfile.processing["ophys"].data_interfaces["SummaryImages"]
    image_collection.add_image(GrayscaleImage(name="SourceImage", data=np.ones((5, 5)), description="source FOV"))
    image_collection.add_image(
        GrayscaleImage(name="RegisteredImage", data=np.ones((5, 5)) * 2, description="registered FOV")
    )

    landmarks = Landmarks(name="landmarks", description="registration landmarks")
    landmarks.add_row(source_x=50.0, source_y=100.0, reference_x=4000.0, reference_y=2000.0)

    src_masks = BrainRegionMasks(name="source_brain_region_id_masks", description="source masks")
    src_masks.add_row(x=0, y=0, brain_region_id=315)

    registration = AtlasRegistration(
        source_image=image_collection["SourceImage"],
        registered_image=image_collection["RegisteredImage"],
        landmarks=landmarks,
    )
    nwbfile.add_lab_meta_data([registration])
    localization.add_brain_region_masks([src_masks])

    with NWBHDF5IO("test_atlas_registration_plane.nwb", "w") as io:
        io.write(nwbfile)

    with NWBHDF5IO("test_atlas_registration_plane.nwb", "r", load_namespaces=True) as io:
        read_nwbfile = io.read()
        read_localization = read_nwbfile.lab_meta_data["localization"]
        read_registration = read_nwbfile.lab_meta_data["atlas_registration"]

        assert isinstance(read_registration, AtlasRegistration)
        assert isinstance(read_registration.landmarks, Landmarks)
        npt.assert_array_equal(
            read_registration.landmarks["source_x"].data[:],
            np.array([50.0], dtype=np.float32),
        )

        read_src = read_localization.brain_region_masks["source_brain_region_id_masks"]
        assert isinstance(read_src, BrainRegionMasks)
        npt.assert_array_equal(
            read_src["brain_region_id"].data[:],
            np.array([315], dtype=np.uint32),
        )


def test_brain_region_masks_directly_under_localization():
    """BrainRegionMasks can be stored under Localization without any AtlasRegistration."""
    nwbfile = mock_NWBFile()
    localization = Localization()
    nwbfile.add_lab_meta_data([localization])

    masks = BrainRegionMasks(name="VISp_masks", description="Visual cortex pixel masks")
    masks.add_row(x=10, y=20, brain_region_id=385)
    masks.add_row(x=11, y=20, brain_region_id=385)
    masks.add_row(x=10, y=21, brain_region_id=394)

    localization.add_brain_region_masks([masks])

    with NWBHDF5IO("test_brain_region_masks_direct.nwb", "w") as io:
        io.write(nwbfile)

    with NWBHDF5IO("test_brain_region_masks_direct.nwb", "r", load_namespaces=True) as io:
        read_nwbfile = io.read()
        read_localization = read_nwbfile.lab_meta_data["localization"]

        read_masks = read_localization.brain_region_masks["VISp_masks"]
        assert isinstance(read_masks, BrainRegionMasks)
        assert len(read_masks) == 3
        npt.assert_array_equal(read_masks["x"].data[:], np.array([10, 11, 10], dtype=np.uint32))
        npt.assert_array_equal(read_masks["y"].data[:], np.array([20, 20, 21], dtype=np.uint32))
        npt.assert_array_equal(
            read_masks["brain_region_id"].data[:],
            np.array([385, 385, 394], dtype=np.uint32),
        )
