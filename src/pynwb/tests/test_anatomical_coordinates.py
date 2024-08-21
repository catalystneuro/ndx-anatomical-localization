"""Unit and integration tests for the new neurodata type."""
from pynwb import NWBHDF5IO
from pynwb.testing.mock.file import mock_NWBFile
from pynwb.testing.mock.ecephys import mock_ElectrodeTable
import numpy as np
import numpy.testing as npt

from ndx_anatomical_localization import AnatomicalCoordinatesTable, Space, Localization


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
        npt.assert_array_equal(read_coordinates_table["brain_region"].data[:], np.array(["CA1", "CA1", "CA1", "CA1", "CA1"]))
        npt.assert_array_equal(read_coordinates_table["localized_entity"].data[:], np.array([0, 1, 2, 3, 4]))
