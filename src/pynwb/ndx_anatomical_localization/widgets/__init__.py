# This module is imported by nwbwidgets when
# nwbwidgets.load_extension_widgets_into_spec([ndx_anatomical_localization])
# is called. Otherwise, the module is not imported unless explicitly imported.

from .. import TetrodeSeries
from .tetrode_series_widget import TetrodeSeriesWidget

vis_spec = {
    TetrodeSeries: TetrodeSeriesWidget,
}
