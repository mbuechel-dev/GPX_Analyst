"""GPX track comparison and deviation visualization — subpackage of gpx_analyst."""

__version__ = "0.2.0"

from gpx_analyst.core.parser import parse_gpx, TrackPoint
from .comparator import compare_tracks, ComparisonResult
from .visualizer import visualize, visualize_map, visualize_plot
