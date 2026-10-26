# Kit & Crest Studio

### A small design workbench for a fictional football team

Choose a name, two colours, a crest shape and a shirt pattern. Preview the identity, compare three patterns, place the crest on a match card and export the complete artwork. The final version adds controls for the whole design and reusable presets, while keeping the drawing rules visible in ordinary Python.

## Open the studio

Open a terminal in this folder. Use Python 3.11 or 3.12.

```bash
python -m venv .venv
```

Activate with `.venv\Scripts\activate` on Windows or `source .venv/bin/activate` on macOS/Linux, then install the packages:

```bash
python -m pip install -r requirements.txt
```

**For a quick export without a notebook:**

```bash
python render_design.py
```

This writes the demo design into `Exports/`. Open `team_sheet.png`, `pattern_comparison.png` and `matchday_card.png` to see it. The example exports are already supplied.

**For interactive editing:**

```bash
python -m jupyterlab
```

Open `kit_workshop.ipynb`, (instead of jupyterlab, jupyter notebook can be used as well) you choose the Python kernel and run all cells in order. The notebook starts with static examples and then displays the controls. It must run from this project folder so it can import `drawing.py` and find `Presets/`.

## Choose → preview → save → reopen

The name, colour pickers, crest and pattern dropdowns update a design-sheet preview. The opponent, two scores and clock text update the match card. Editing a control changes only the preview. Blank labels use neutral defaults such as “My Team” or “Opponent”. Scores are whole numbers from 0 to 99.

Click **Save artwork + preset** when ready. All matching PNG/SVG artwork is written together to `Exports/`, with full settings in `Exports/project.json`. The same settings are saved as `Presets/reviewed_team.json`. Choose that file in the preset menu and click **Load preset** to reopen it after restarting. Loading fills the controls without altering exported artwork.

A later save replaces those exports and `reviewed_team.json`. Copy or rename a preset before saving another design you want to retain. `Presets/demo.json` and `Presets/alternate.json` are supplied examples. The alternate preset uses a round crest, hoops, a teal palette and longer team labels.

You can also render a preset to a different folder:

```bash
python render_design.py --preset Presets/alternate.json --out Exports/alternate
```

Command-line paths are relative to the terminal directory. The default paths are relative to the script. The terminal command exports immediately; notebook previews do not.

## How the artwork is made

**The notebook is the workbench.** Its early cells demonstrate individual drawing stages. The final cell creates ipywidgets controls and connects them with `observe()`. `selected_settings()` collects current values into two dictionaries. `update_preview()` renders new images into memory; `save_selected()` is the explicit file-writing step. `load_selected()` reads one preset and fills the controls, postponing redraw until all values are set.

**`drawing.py` contains the drawing rules.** `make_crest()` starts with an RGBA canvas whose outside pixels are transparent. A polygon gives the shield option; an ellipse gives the round option. Initials come from the first letters of up to three name words, and a diamond is drawn as a simple emblem. No club logo or generated image is downloaded.

`make_shirt()` defines one outline and a grayscale mask. White mask pixels keep the drawing, while black pixels hide everything outside the shirt. Horizontal rectangles form hoops, vertical rectangles form stripes, and a polygon forms the sash. The collar and small crest are added consistently. `make_pattern_sheet()` calls this same function three times so the comparison varies only the pattern.

`make_team_sheet()` arranges the crest, selected shirt and colour swatches on a presentation sheet. `fit_text()` measures labels, reduces the font size to fit their available width, and uses dots only when even the smallest font is insufficient. This fitting now applies to the team sheet and pattern heading as well as match-card names. Full text remains in the preset even if the visible label is shortened.

`make_match_card()` reuses the generated home crest and palette. The opponent gets a neutral initials disc. Score and clock are manual labels: the clock does not tick, and no sports data is fetched. `crest_svg()` writes the same crest geometry as XML vector shapes and editable text. ElementTree escapes names containing characters such as `&`.

`build_artwork()` gathers all images from one settings pair. `save_artwork()` exports that set and its settings, ensuring the crest, shirts and match card agree. `read_project()` reads JSON and checks the supported choices. `render_design.py` is the short terminal entry point using those same functions.

## The export set

| File | Purpose |
| --- | --- |
| `crest.png` | 420 × 500 transparent crest |
| `crest.svg` | Scalable crest with editable shapes and text |
| `shirt_front.png` | 660 × 700 transparent selected shirt |
| `shirt_hoops.png`, `shirt_stripes.png`, `shirt_sash.png` | Three transparent alternatives |
| `team_sheet.png` | 1440 × 1000 design presentation |
| `pattern_comparison.png` | 1620 × 900 comparison sheet |
| `matchday_card.png` | 1600 × 900 fictional match graphic |
| `project.json` | Exact design and match settings for reopening |
| `design_notes.txt` | Readable settings and output explanation |
