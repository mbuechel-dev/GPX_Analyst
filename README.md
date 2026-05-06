# compare-gpx

Compare two GPX tracks that are supposed to follow the same route and visualize where they deviate.

One file is treated as the **source of truth** (reference). Every point of the second file (comparison) is measured against the nearest segment of the reference polyline. The result is an interactive HTML map and a static deviation plot.

---

## Installation

```bash
pip install -e .
```

Requires Python 3.9+. Dependencies (`gpxpy`, `numpy`, `matplotlib`, `folium`, `branca`) are installed automatically.

---

## Usage

### Command line

```bash
compare-gpx reference.gpx comparison.gpx -o ./output
```

```
Parsing reference:  reference.gpx
  -> 4821 points
Parsing comparison: comparison.gpx
  -> 3104 points
Computing deviations ...

Results
  Max deviation         42.3 m
  Mean deviation         6.1 m
  Median deviation       4.8 m
  Std deviation          5.9 m
  Within  5 m              62 %
  Within 10 m              81 %
  Within 25 m              97 %

Saving output to C:\...\output ...
  Interactive map : output\comparison_map.html
  Deviation plot  : output\comparison_plot.png
```

**Options**

| Flag | Default | Description |
|------|---------|-------------|
| `-o / --output-dir DIR` | `.` (current directory) | Folder to write output files into |
| `--max-scale METRES` | 95th percentile | Ceiling of the colour scale on both outputs |

### Python API

```python
from compare_gpx import parse_gpx, compare_tracks, visualize

reference  = parse_gpx("reference.gpx")
comparison = parse_gpx("comparison.gpx")
result     = compare_tracks(reference, comparison)

# Both outputs at once
map_path, plot_path = visualize(result, output_dir="./output")

# Or individually
from compare_gpx import visualize_map, visualize_plot

visualize_map(result, "map.html")
visualize_plot(result, "plot.png")

# Access stats programmatically
print(f"Max deviation:    {result.max_deviation:.1f} m")
print(f"Mean deviation:   {result.mean_deviation:.1f} m")
print(f"Within 10 m:      {result.within_threshold(10)*100:.0f} %")
```

---

## Outputs

### `comparison_map.html`

An interactive [Folium](https://python-visualization.github.io/folium/) map:

- **Dashed blue line** — reference track
- **Colour-coded line** — comparison track, coloured green → yellow → red by deviation magnitude
- **Colour bar legend** in the bottom-left corner with the deviation scale in metres
- **Statistics panel** in the top-right corner showing max/mean/median/std and threshold percentages
- **Layer control** to toggle the reference and comparison tracks independently
- Tooltips on every comparison segment showing the local deviation on hover

Open the file in any browser — no internet connection required.

### `comparison_plot.png`

A static matplotlib chart of deviation (metres) vs. cumulative distance along the comparison track (km):

- Continuously colour-coded line (green → red)
- Shaded threshold zones: green (< 5 m), yellow (5–15 m), red (> 15 m)
- Summary statistics annotation at the top of the chart

---

## How deviation is calculated

For every point $P_i$ in the comparison track the algorithm finds its shortest distance to the reference **polyline** (not just the nearest point):

$$d_i = \min_j \left\| P_i - \left( A_j + \text{clip}(t,\,0,\,1)\cdot(B_j - A_j) \right) \right\|, \quad t = \frac{(P_i - A_j)\cdot(B_j - A_j)}{\|B_j - A_j\|^2}$$

Coordinates are first projected to approximate metres using an equirectangular projection centred on the tracks' centroid, accurate to < 0.5 % for extents up to ~200 km. Computation is batched so large tracks (tens of thousands of points) run without exhausting memory.

---

## Project structure

```
compareGPXtracks/
├── compare_gpx/
│   ├── __init__.py     # public API re-exports
│   ├── parser.py       # parse_gpx() → List[TrackPoint]
│   ├── comparator.py   # compare_tracks() → ComparisonResult
│   ├── visualizer.py   # visualize_map(), visualize_plot(), visualize()
│   ├── cli.py          # argparse entry point
│   └── __main__.py     # enables `python -m compare_gpx`
├── requirements.txt
└── pyproject.toml
```
