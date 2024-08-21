from hdmf.common import DynamicTable
from hdmf.utils import get_docval, AllowPositional

from pynwb import get_class, register_class, docval, register_map

TempSpace = get_class("Space", "ndx-anatomical-localization")
TempAnatomicalCoordinatesTable = get_class("AnatomicalCoordinatesTable", "ndx-anatomical-localization")
Localization = get_class("Localization", "ndx-anatomical-localization")

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
        {"name": "name", "type": str, "doc": "name of the space"},
        {"name": "space_name", "type": str, "doc": "name of the space"},
        {"name": "origin", "type": str, "doc": "origin of the space"},
        {"name": "units", "type": str, "doc": "units of the space"},
        {"name": "orientation", "type": str, "doc": "orientation of the space"},
        allow_positional=AllowPositional.ERROR,
    )
    def __init__(self, name, space_name, origin, units, orientation):
        assert len(orientation) == 3, "orientation must be a string of length 3"
        valid_values = ["A", "P", "L", "R", "S", "I"]
        for x in orientation:
            assert x in valid_values, "orientation must be a string of 'A', 'P', 'L', 'R', 'S', 'I'"

        map = {"A": "AP", "P": "AP", "L": "LR", "R": "LR", "S": "SI", "I": "SI"}
        new_var = [map[var] for var in orientation]
        assert len(set(new_var)) == 3, "orientation must be unique dimensions (AP, LR, SI)"

        super().__init__(name=name, space_name=space_name, origin=origin, units=units, orientation=orientation)

    @classmethod
    def get_predefined_space(cls, space_name):
        if space_name in PREDEFINED_SPACES:
            return cls(**PREDEFINED_SPACES[space_name])
        else:
            raise ValueError(f"Space {space_name} is not predefined")


@register_class("AnatomicalCoordinatesTable", "ndx-anatomical-localization")
class AnatomicalCoordinatesTable(TempAnatomicalCoordinatesTable):

    @docval(
        {"name": "space", "type": Space, "doc": "space of the table"},
        {"name": "method", "type": str, "doc": "method of the table"},
        {"name": "target", "type": DynamicTable,
         "doc": 'target table. ignored if a "localized_entity" column is provided in "columns"', "default": None},
        *get_docval(DynamicTable.__init__),
        allow_positional=AllowPositional.ERROR,
    )
    def __init__(self, **kwargs):
        columns = kwargs.get("columns")
        target = kwargs.pop("target")
        if not columns or "localized_entity" not in [c.name for c in columns]:
            # set the target table of the "localized_entity" column only if the "localized_entity" column is not in "columns"
            if target is None:
                raise ValueError(
                    '"target" (the target table that contains the objects that have these coordinates) '
                    'must be provided in AnatomicalCoordinatesTable.__init__ '
                    'if the "localized_entity" column is not in "columns".')
            kwargs["target_tables"] = {"localized_entity": target}

        super().__init__(**kwargs)
