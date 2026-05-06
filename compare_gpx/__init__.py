"""GPX track comparison and deviation visualization."""

__version__ = "0.1.0"

from .parser import parse_gpx
from .comparator import compare_tracks, ComparisonResult
from .visualizer import visualize, visualize_map, visualize_plot
