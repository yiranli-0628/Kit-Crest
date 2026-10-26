# Export a complete team identity from a saved preset, without Jupyter Notebook/Labs
from pathlib import Path
import argparse
from drawing import read_project, save_artwork

folder = Path(__file__).resolve().parent
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--preset', type=Path, default=folder / 'Presets/demo.json')
parser.add_argument('--out', type=Path, default=folder / 'Exports')
args = parser.parse_args()
# Paths supplied as arguments are relative to current terminal directory.
design, match = read_project(args.preset)
save_artwork(design, match, args.out)
print(f"Exported {design['team']} to {args.out.resolve()}")
