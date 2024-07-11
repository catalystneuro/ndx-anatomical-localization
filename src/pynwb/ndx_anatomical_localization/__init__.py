import os
from pynwb import load_namespaces, get_class, register_class

try:
    from importlib.resources import files
except ImportError:
    # TODO: Remove when python 3.9 becomes the new minimum
    from importlib_resources import files

# # Get path to the namespace.yaml file with the expected location when installed not in editable mode
# __location_of_this_file = files(__name__)
# __spec_path = __location_of_this_file / "spec" / "ndx-anatomical-localization.namespace.yaml"

# # If that path does not exist, we are likely running in editable mode. Use the local path instead
# if not os.path.exists(__spec_path):
#     __spec_path = __location_of_this_file.parent.parent.parent / "spec" / "ndx-anatomical-localization.namespace.yaml"

__spec_path = "/Users/bendichter/dev/ndx-anatomical-localization/spec/ndx-anatomical-localization.namespace.yaml"

# Load the namespace
load_namespaces(str(__spec_path))

# TODO: Define your classes here to make them accessible at the package level.
# Either have PyNWB generate a class from the spec using `get_class` as shown
# below or write a custom class and register it using the class decorator
TempSpace = get_class("Space", "ndx-anatomical-localization")
TempAnatonicalCoordinatesTable = get_class("AnatonicalCoordinatesTable", "ndx-anatomical-localization")





@register_class("Space", "ndx-anatomical-localization")
class Space(TempSpace):
    def __init__(self, name, space_name, origin, units, x, y, z):
        valid_values = ["A", "P", "L", "R", "D", "V"]
        assert x in valid_values, "x must be one of 'A', 'P', 'L', 'R', 'D', 'V'"
        assert y in valid_values, "y must be one of 'A', 'P', 'L', 'R', 'D', 'V'"
        assert z in valid_values, "z must be one of 'A', 'P', 'L', 'R', 'D', 'V'"
        
        map = dict(A="AP", P="AP", L="LR", R="LR", D="DV", V="DV")
        new_var = [map[var] for var in (x,y,z)]
        assert len(set(new_var)) == 3, "x, y, and z must be unique dimensions (AP, LR, DV)"

        super().__init__(name=name, space_name=space_name, origin=origin, units=units, x=x, y=y, z=z)


@register_class("AnatonicalCoordinatesTable", "ndx-anatomical-localization")
class AnatonicalCoordinatesTable(TempAnatonicalCoordinatesTable):
    def __init__(self, name, target, description, space, method):
        super().__init__(name=name, description=description, space=space, method=method)
        self.target_object.table = target


# NOTE: `widgets/tetrode_series_widget.py` adds a "widget"
# attribute to the TetrodeSeries class. This attribute is used by NWBWidgets.
# Delete the `widgets` subpackage or the `tetrode_series_widget.py` module
# if you do not want to define a custom widget for your extension neurodata
# type.

# Remove these functions from the package
del load_namespaces, get_class, register_class
