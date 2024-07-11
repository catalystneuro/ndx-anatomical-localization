"""Unit and integration tests for the example TetrodeSeries extension neurodata type.

TODO: Modify these tests to test your extension neurodata type.
"""

from pynwb.testing.mock.file import mock_NWBFile
from pynwb.testing.mock.ecephys import mock_ElectrodeTable

from ndx_anatomical_localization import AnatonicalCoordinatesTable, Space


def test_create_anatonical_coordinates_table():

    electrodes_table = mock_ElectrodeTable()

    table = AnatonicalCoordinatesTable(name="MyAnatonicalLocalization", target=electrodes_table, description="Anatonical coordinates table")
    [table.add_row(x=1.0, y=2.0, z=3.0, brain_region="CA1", target_object=x) for x in range(5)]


electrodes_table = mock_ElectrodeTable()

#space = Space(name="space", space_name="CCF", origin="origin", units="um", x="A", y="S", z="L")
space = Space.get_predefined_space("CCFv3")

table = AnatonicalCoordinatesTable(
    name="MyAnatonicalLocalization",
    target=electrodes_table,
    description="Anatonical coordinates table",
    method="method",
    space=space,
)
[table.add_row(x=1.0, y=2.0, z=3.0, brain_region="CA1", target_object=x) for x in range(5)]

print(table)

print(space)