# Procedural kit, crest and match-card drawings using Pillow and SVG shapes.
from pathlib import Path
import json
import re
from PIL import Image, ImageDraw, ImageFont
from xml.etree.ElementTree import Element, SubElement, tostring

# One geometry for PNG and SVG keeps the two crest formats consistent.
shield = [(45, 55), (375, 55), (365, 300), (210, 455), (55, 300)]


def validate_settings(design, match):
    # These are input checks for editable presets, not a separate testing framework.
    for name in ['team', 'primary', 'secondary', 'crest', 'pattern']:
        if not isinstance(design.get(name), str) or not design[name].strip():
            raise ValueError(f'Design field {name} must contain text.')
    for name in ['primary', 'secondary']:
        if not re.fullmatch(r'#[0-9a-fA-F]{6}', design[name]):
            raise ValueError(f'{name} must use six-digit hex, such as #61213d.')
    if design['crest'] not in ['shield', 'round']:
        raise ValueError('Crest must be shield or round.')
    if design['pattern'] not in ['hoops', 'stripes', 'sash']:
        raise ValueError('Pattern must be hoops, stripes or sash.')
    for name in ['home_score', 'away_score']:
        if type(match.get(name)) is not int or not 0 <= match[name] <= 99:
            raise ValueError('Scores must be whole numbers from 0 to 99.')
    for name in ['opponent', 'clock']:
        if not isinstance(match.get(name), str) or not match[name].strip():
            raise ValueError(f'Match field {name} must contain text.')


def read_project(path):
    project = json.loads(Path(path).read_text(encoding='utf-8'))
    validate_settings(project['design'], project['match'])
    return project['design'], project['match']

def fit_text(pen, text, max_width, start_size):
    size = start_size
    font = ImageFont.load_default(size=size)
    while pen.textlength(text, font=font) > max_width and size > 14:
        size -= 1
        font = ImageFont.load_default(size=size)
    if pen.textlength(text, font=font) > max_width:
        while text and pen.textlength(text + "...", font=font) > max_width:
            text = text[:-1]
        text += "..."
    return text, font



def make_crest(design):
    initials = "".join(word[0] for word in design["team"].split())[:3].upper()
    # Draw a badge from a shape, initials and a diamond.
    # RGBA includes an alpha channel; alpha zero makes the starting canvas transparent.
    crest = Image.new("RGBA", (420, 500), (0, 0, 0, 0))
    pen = ImageDraw.Draw(crest)
    # Both branches use the same canvas, so either crest can fit on the shirt.
    if design["crest"] == "round":
        pen.ellipse((35, 65, 385, 415), fill=design["primary"],
                    outline=design["secondary"], width=12)
    else:
        shield = [(45, 55), (375, 55), (365, 300), (210, 455), (55, 300)]
        pen.polygon(shield, fill=design["primary"])
        # Repeat the first point to close the outline.
        pen.line(shield + [shield[0]], fill=design["secondary"], width=12)
    # The mm anchor centres the text around the supplied coordinate.
    pen.text((210, 175), initials, font=ImageFont.load_default(size=68),
             fill=design["secondary"], anchor="mm")
    pen.polygon([(210, 235), (260, 285), (210, 355), (160, 285)], fill=design["secondary"])
    return crest


def make_shirt(design, crest, pattern):
    # Define the geometry once; every pattern uses exactly the same shirt outline.
    outline = [(205, 75), (285, 45), (375, 45), (455, 75), (605, 200),
               (525, 325), (460, 280), (475, 625), (185, 625), (200, 280),
               (135, 325), (55, 200)]
    mask = Image.new("L", (660, 700), 0)
    # In an L-mode mask, white (255) keeps a pixel and black (0) hides it.
    ImageDraw.Draw(mask).polygon(outline, fill=255)
    small_crest = crest.resize((76, 90), Image.Resampling.LANCZOS)

    shirt = Image.new("RGBA", mask.size, design["primary"])
    pen = ImageDraw.Draw(shirt)
    if pattern == "hoops":
        # Change y repeatedly to create evenly spaced horizontal bands.
        for y in range(175, 650, 110):
            pen.rectangle((0, y, 660, y + 44), fill=design["secondary"])
    elif pattern == "stripes":
        # Change x instead, creating vertical bands with the same two colours.
        for x in range(0, 660, 100):
            pen.rectangle((x, 0, x + 39, 700), fill=design["secondary"])
    elif pattern == "sash":
        # Four points form a diagonal band that extends beyond the shirt edges.
        pen.polygon([(35, 480), (80, 565), (625, 165), (580, 80)], fill=design["secondary"])
    # Draw the common trim after the pattern so it remains visible.
    pen.line(outline + [outline[0]], fill=design["secondary"], width=5)
    pen.polygon([(285, 45), (375, 45), (330, 130)], fill=design["secondary"])
    shirt.putalpha(mask)
    shirt.alpha_composite(small_crest, (370, 130))
    return shirt


def make_team_sheet(design, crest, shirt):
    # Arrange the two assets on a flat presentation sheet.
    sheet = Image.new("RGB", (1440, 1000), "#fffdf7")
    pen = ImageDraw.Draw(sheet)
    pen.rectangle((0, 0, 1440, 14), fill=design["primary"])
    pen.text((75, 55), "TEAM DESIGN / CONCEPT", font=ImageFont.load_default(size=24), fill=design["primary"])
    label, font = fit_text(pen, design["team"].upper(), 1290, 62)
    pen.text((75, 105), label, font=font, fill=design["primary"])
    # Passing each RGBA image as the paste mask preserves its transparent corners.
    sheet.paste(crest, (100, 275), crest)
    sheet.paste(shirt, (700, 195), shirt)
    pen.text((100, 235), "CREST", font=ImageFont.load_default(size=22), fill=design["primary"])
    pen.text((700, 235), "FRONT SHIRT", font=ImageFont.load_default(size=22), fill=design["primary"])
    pen.text((95, 860), design["crest"].upper() + " / " + design["pattern"].upper(), font=ImageFont.load_default(size=23), fill=design["primary"])
    # Draw a colour swatch and its exact hex value for both palette choices.
    for index, colour in enumerate([design["primary"], design["secondary"]]):
        x = 95 + index * 290
        pen.rectangle((x, 925, x + 42, 957), fill=colour)
        pen.text((x + 58, 927), colour.upper(), font=ImageFont.load_default(size=23), fill=design["primary"])
    return sheet


def make_pattern_sheet(design, crest):
    # Build a side-by-side view and save each pattern as a reusable transparent asset.
    patterns = ["hoops", "stripes", "sash"]
    comparison = Image.new("RGB", (1620, 900), "#fffdf7")
    pen = ImageDraw.Draw(comparison)
    label, font = fit_text(pen, "PATTERN STUDY / " + design["team"].upper(), 1500, 38)
    pen.text((60, 50), label, font=font, fill=design["primary"])
    for index, pattern in enumerate(patterns):
        variant = make_shirt(design, crest, pattern)
        # Resize only the preview; each individual export keeps its original dimensions.
        preview = variant.resize((462, 490), Image.Resampling.LANCZOS)
        x = 50 + index * 535
        comparison.paste(preview, (x, 220), preview)
        pen.text((x + 231, 170), pattern.upper(), anchor="mm",
                 font=ImageFont.load_default(size=28), fill=design["primary"])
    pen.text((60, 790), "Same silhouette, colours and crest. Three drawing rules.",
             font=ImageFont.load_default(size=27), fill=design["primary"])
    return comparison


def crest_svg(design):
    initials = "".join(word[0] for word in design["team"].split())[:3].upper()
    svg = Element("svg", xmlns="http://www.w3.org/2000/svg", viewBox="0 0 420 500",
                  width="420", height="500", role="img")
    SubElement(svg, "title").text = design["team"] + " crest"
    # Use the same geometry and palette as the PNG crest.
    shape = {"fill": design["primary"], "stroke": design["secondary"], "stroke-width": "12"}
    if design["crest"] == "round":
        SubElement(svg, "ellipse", cx="210", cy="240", rx="175", ry="175", **shape)
    else:
        points = " ".join(f"{x},{y}" for x, y in shield)
        SubElement(svg, "polygon", points=points, **shape)
    # Text stays editable; the browser supplies its sans-serif font.
    label = SubElement(svg, "text", x="210", y="175", fill=design["secondary"],
                       attrib={"text-anchor": "middle", "dominant-baseline": "central",
                               "font-family": "sans-serif", "font-size": "68"})
    label.text = initials
    SubElement(svg, "polygon", points="210,235 260,285 210,355 160,285", fill=design["secondary"])
    # ElementTree escapes text characters so names containing '&' remain valid XML.
    svg_text = tostring(svg, encoding="unicode")
    return svg_text

def make_match_card(design, crest, settings):
    card = Image.new("RGB", (1600, 900), "#fffdf7")
    pen = ImageDraw.Draw(card)
    pen.rectangle((0, 0, 1600, 18), fill=design["primary"])
    pen.text((80, 65), "MATCHDAY / CONCEPT", fill=design["primary"], font=ImageFont.load_default(size=28))
    pen.text((80, 115), "One team identity, another format.", fill=design["primary"], font=ImageFont.load_default(size=43))
    # Reuse the generated crest, resizing a copy so the original export is untouched.
    home_badge = crest.resize((210, 250), Image.Resampling.LANCZOS)
    card.paste(home_badge, (180, 270), home_badge)
    # The opponent gets a simple initials disc rather than a downloaded club logo.
    pen.ellipse((1200, 295, 1400, 495), fill="#e8e3d9", outline=design["primary"], width=5)
    away_initials = "".join(word[0] for word in settings["opponent"].split())[:3].upper()
    pen.text((1300, 395), away_initials, anchor="mm", fill=design["primary"], font=ImageFont.load_default(size=56))
    # Centre the score separately from the two team names.
    score = f"{settings['home_score']} : {settings['away_score']}"
    pen.text((800, 385), score, anchor="mm", fill=design["primary"], font=ImageFont.load_default(size=132))
    pen.rounded_rectangle((695, 495, 905, 555), radius=16, fill=design["primary"])
    clock_text, clock_font = fit_text(pen, settings["clock"], 170, 31)
    pen.text((800, 525), clock_text, anchor="mm", fill=design["secondary"], font=clock_font)
    home_text, home_font = fit_text(pen, design["team"], 430, 35)
    pen.text((285, 600), home_text, anchor="mm", fill=design["primary"], font=home_font)
    away_text, away_font = fit_text(pen, settings["opponent"], 440, 35)
    pen.text((1300, 600), away_text, anchor="mm", fill=design["primary"], font=away_font)
    pen.line((80, 710, 1520, 710), fill=design["secondary"], width=5)
    pen.text((80, 770), "Fictional match | manually entered score and clock", fill=design["primary"], font=ImageFont.load_default(size=25))
    return card



def build_artwork(design, match):
    # Every image is built from the same settings so a changed team colour cannot
    # leave the shirt, crest and score card describing different designs.
    validate_settings(design, match)
    crest = make_crest(design)
    shirt = make_shirt(design, crest, design['pattern'])
    images = {'crest.png': crest, 'shirt_front.png': shirt,
              'team_sheet.png': make_team_sheet(design, crest, shirt),
              'pattern_comparison.png': make_pattern_sheet(design, crest),
              'matchday_card.png': make_match_card(design, crest, match)}
    for pattern in ['hoops', 'stripes', 'sash']:
        images[f'shirt_{pattern}.png'] = make_shirt(design, crest, pattern)
    return images


def save_artwork(design, match, destination):
    # Writing happens only on an explicit export action
    images = build_artwork(design, match)
    destination = Path(destination)
    destination.mkdir(parents=True, exist_ok=True)
    for name, image in images.items():
        image.save(destination / name)
    (destination / 'crest.svg').write_text(crest_svg(design), encoding='utf-8')
    project = {'design': design, 'match': match}
    (destination / 'project.json').write_text(json.dumps(project, indent=2), encoding='utf-8')
    notes = 'KIT & CREST / EXPORTED SETTINGS\n\n'
    notes += '\n'.join(f'{key}: {value}' for key, value in design.items())
    notes += '\n\nFictional match settings\n' + '\n'.join(f'{key}: {value}' for key, value in match.items())
    notes += '\n\nPNG crest and shirts have transparent backgrounds. SVG contains editable shapes and text.\n'
    notes += 'Team and comparison sheets are concept previews, not measured sewing or print specifications.\n'
    notes += 'The score and clock are manually entered, not live feeds.\n'
    (destination / 'design_notes.txt').write_text(notes, encoding='utf-8')
    return images
