"""Unit and integration tests for the new neurodata type."""
from pynwb import NWBHDF5IO
from pynwb.testing.mock.file import mock_NWBFile
from pynwb.testing.mock.ecephys import mock_ElectrodeTable

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
    [table.add_row(x=1.0, y=2.0, z=3.0, brain_region="CA1", target_object=x) for x in range(5)]

    localization.add_anatomical_coordinates_tables([table])

    with NWBHDF5IO("test.nwb", "w") as io:
        io.write(nwbfile)

    with NWBHDF5IO("test.nwb", "r", load_namespaces=True) as io:
        read_nwbfile = io.read()

        assert read_nwbfile.lab_meta_data["localization"]["MyAnatomicalLocalization"].space.space_name == "CCFv3"
