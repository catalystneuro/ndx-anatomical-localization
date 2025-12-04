"""Unit and integration tests for the new neurodata type."""

from pynwb import NWBHDF5IO
from pynwb.base import Images
from pynwb.image import GrayscaleImage
from pynwb.testing.mock.file import mock_NWBFile
from pynwb.testing.mock.ecephys import mock_ElectrodeTable
from pynwb.testing.mock.ophys import mock_ImagingPlane
import numpy as np
import numpy.testing as npt

from ndx_anatomical_localization import AnatomicalCoordinatesImage, AnatomicalCoordinatesTable, Space, Localization


def test_create_custom_space():
    _ = Space(
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

    space = Space.get_predefined_space("CCFv3")
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
        assert read_coordinates_table.space.fields == Space.get_predefined_space("CCFv3").fields
        npt.assert_array_equal(read_coordinates_table["x"].data[:], np.array([1.0, 1.0, 1.0, 1.0, 1.0]))
        npt.assert_array_equal(read_coordinates_table["y"].data[:], np.array([2.0, 2.0, 2.0, 2.0, 2.0]))
        npt.assert_array_equal(read_coordinates_table["z"].data[:], np.array([3.0, 3.0, 3.0, 3.0, 3.0]))
        npt.assert_array_equal(
            read_coordinates_table["brain_region"].data[:], np.array(["CA1", "CA1", "CA1", "CA1", "CA1"])
        )
        npt.assert_array_equal(read_coordinates_table["localized_entity"].data[:], np.array([0, 1, 2, 3, 4]))


def test_create_anatomical_coordinates_image_w_imaging_plane():

    nwbfile = mock_NWBFile()

    localization = Localization()
    nwbfile.add_lab_meta_data([localization])

    imaging_plane = mock_ImagingPlane(nwbfile=nwbfile)

    space = Space.get_predefined_space("CCFv3")
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
        assert read_coordinates_image.space.fields == Space.get_predefined_space("CCFv3").fields
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

    space = Space.get_predefined_space("CCFv3")
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
        assert read_coordinates_image.space.fields == Space.get_predefined_space("CCFv3").fields
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

    space = Space.get_predefined_space("CCFv3")
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

    space = Space.get_predefined_space("CCFv3")
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

    space = Space.get_predefined_space("CCFv3")
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

    space = Space.get_predefined_space("CCFv3")
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
