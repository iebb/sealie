"""Pinned original full-disk centerline stroker (OFL-1.1).
Derived from Panorama Gothic tools/build_stroke_font.py; no outline input.
"""
from __future__ import annotations
import math, re
from typing import Iterable
from pathlib import Path
from fontTools.fontBuilder import FontBuilder
from fontTools.pens.basePen import BasePen
from fontTools.pens.ttGlyphPen import TTGlyphPen
from fontTools.svgLib.path import parse_path
from fontTools.ttLib.tables._g_l_y_f import flagOverlapSimple
UNITS_PER_EM=1024
BASELINE=832
NORMALIZED_CENTERLINE_EXTENT=738.0
FLATTEN_TOLERANCE=0.10
FAMILY="Panorama Gothic Seal Individual"
Point=tuple[float,float]
def point_segment_distance(point: Point, start: Point, end: Point) -> float:
    dx, dy = end[0] - start[0], end[1] - start[1]
    length_squared = dx * dx + dy * dy
    if not length_squared:
        return math.dist(point, start)
    fraction = max(0.0, min(1.0, ((point[0] - start[0]) * dx
                                 + (point[1] - start[1]) * dy) / length_squared))
    return math.dist(point, (start[0] + fraction * dx, start[1] + fraction * dy))


def _midpoint(first: Point, second: Point) -> Point:
    return ((first[0] + second[0]) / 2, (first[1] + second[1]) / 2)


def flatten_cubic(start: Point, first: Point, second: Point, end: Point,
                  tolerance: float = FLATTEN_TOLERANCE, depth: int = 0) -> list[Point]:
    """Subdivide until the entire cubic control hull is close to its chord."""
    error = max(point_segment_distance(first, start, end),
                point_segment_distance(second, start, end))
    if error <= tolerance:
        return [end]
    if depth >= 24:
        raise ValueError("Bezier flattening did not converge within 24 subdivisions")
    a, b, c = _midpoint(start, first), _midpoint(first, second), _midpoint(second, end)
    d, e = _midpoint(a, b), _midpoint(b, c)
    middle = _midpoint(d, e)
    return (flatten_cubic(start, a, d, middle, tolerance, depth + 1)
            + flatten_cubic(middle, e, c, end, tolerance, depth + 1))


class CenterlinePen(BasePen):
    def __init__(self, tolerance: float = FLATTEN_TOLERANCE):
        super().__init__(None)
        self.tolerance = tolerance
        self.subpaths: list[tuple[list[Point], bool]] = []
        self.points: list[Point] = []

    def _moveTo(self, point):
        if self.points:
            raise ValueError("Each stroke must have exactly one continuous subpath")
        self.points = [tuple(point)]

    def _lineTo(self, point):
        point = tuple(point)
        if point != self.points[-1]:
            self.points.append(point)

    def _curveToOne(self, first, second, end):
        self.points.extend(flatten_cubic(self.points[-1], tuple(first), tuple(second),
                                         tuple(end), self.tolerance))

    def _qCurveToOne(self, control, end):
        start = self.points[-1]
        first = tuple(start[axis] + 2 / 3 * (control[axis] - start[axis]) for axis in (0, 1))
        second = tuple(end[axis] + 2 / 3 * (control[axis] - end[axis]) for axis in (0, 1))
        self._curveToOne(first, second, end)

    def _closePath(self):
        self.subpaths.append((self.points, True))
        self.points = []

    def _endPath(self):
        self.subpaths.append((self.points, False))
        self.points = []


def flatten_path(path: str, closed: bool | None = None,
                 tolerance: float = FLATTEN_TOLERANCE) -> tuple[list[Point], bool]:
    pen = CenterlinePen(tolerance)
    parse_path(path, pen)
    if pen.points:
        pen._endPath()
    if len(pen.subpaths) != 1:
        raise ValueError("Each stroke path must contain one continuous subpath")
    points, path_closed = pen.subpaths[0]
    if len(points) < 2:
        raise ValueError("Each stroke must contain at least one nonzero segment")
    if closed is not None and not closed and path_closed:
        raise ValueError("A closed SVG path must not declare closed=false")
    return points, bool(closed or path_closed)


def _clockwise_rectangle(pen: TTGlyphPen, start: Point, end: Point, radius: float):
    dx, dy = end[0] - start[0], end[1] - start[1]
    length = math.hypot(dx, dy)
    if length < 1e-9:
        return
    nx, ny = -dy / length * radius, dx / length * radius
    pen.moveTo((start[0] + nx, start[1] + ny))
    pen.lineTo((end[0] + nx, end[1] + ny))
    pen.lineTo((end[0] - nx, end[1] - ny))
    pen.lineTo((start[0] - nx, start[1] - ny))
    pen.closePath()


def _clockwise_disk(pen: TTGlyphPen, center: Point, radius: float):
    """Sixteen tangent-matched quadratic arcs approximate a constant-radius disk.

    At each tangent control point the radius is r/cos(pi/16). The maximum radial
    error is below 0.00019*r, in addition to final TrueType coordinate rounding.
    """
    cx, cy = center
    pen.moveTo((cx + radius, cy))
    control_radius = radius / math.cos(math.pi / 16)
    for index in range(16):
        middle = -(index + 0.5) * math.pi / 8
        end = -(index + 1) * math.pi / 8
        # Close at the identical first point. sin(-2*pi)'s floating residual
        # otherwise makes TTGlyphPen remove the duplicate at some radii but
        # retain it at others, breaking compatible variable-font masters.
        endpoint = ((cx + radius, cy) if index == 15 else
                    (cx + radius * math.cos(end), cy + radius * math.sin(end)))
        pen.qCurveTo((cx + control_radius * math.cos(middle),
                      cy + control_radius * math.sin(middle)), endpoint)
    pen.closePath()


def expand_polylines(strokes: Iterable[tuple[list[Point], bool]], radius: float):
    """Return the nonzero-winding union of constant-radius stroke primitives."""
    if not math.isfinite(radius) or radius <= 0:
        raise ValueError("Stroke radius must be finite and positive")
    pen = TTGlyphPen(None)
    counts = {"segment_rectangles": 0, "round_disks": 0}
    for points, closed in strokes:
        segments = list(zip(points, points[1:]))
        if closed and points[-1] != points[0]:
            segments.append((points[-1], points[0]))
        for start, end in segments:
            if math.dist(start, end) > 1e-9:
                _clockwise_rectangle(pen, start, end, radius)
                counts["segment_rectangles"] += 1
        disk_points = points[:-1] if closed and points[0] == points[-1] else points
        for point in disk_points:
            _clockwise_disk(pen, point, radius)
            counts["round_disks"] += 1
    glyph = pen.glyph()
    if glyph.numberOfContours and len(glyph.coordinates) > 65535:
        raise ValueError(f"Glyph has {len(glyph.coordinates)} points; TrueType limit is 65535")
    if glyph.numberOfContours:
        glyph.flags[0] |= flagOverlapSimple
    return glyph, counts


def codepoint_number(value) -> int:
    if isinstance(value, int):
        number = value
    else:
        number = int(value.removeprefix("U+").removeprefix("0x"), 16)
    if not 0 <= number <= 0x10FFFF or 0xD800 <= number <= 0xDFFF:
        raise ValueError(f"Invalid Unicode scalar value: {value!r}")
    return number


def source_transform(view_box: list[float]):
    if len(view_box) != 4:
        raise ValueError("viewBox must contain x, y, width, height")
    left, top, width, height = map(float, view_box)
    if width <= 0 or height <= 0:
        raise ValueError("viewBox width and height must be positive")
    scale = UNITS_PER_EM / max(width, height)
    x_margin = (UNITS_PER_EM - width * scale) / 2
    y_margin = (UNITS_PER_EM - height * scale) / 2

    def transform(point):
        return ((point[0] - left) * scale + x_margin,
                BASELINE - (point[1] - top) * scale - y_margin)

    return transform, scale


def normalize_sources(sources: list[dict], extent: float = NORMALIZED_CENTERLINE_EXTENT) -> list[dict]:
    """Fit each complete glyph proportionally; never scale its pen width.

    One affine transform is applied to every stroke of a character. The same
    transformed paths are reused at every weight. Reviewed input JSON stays
    immutable, including the nominal width used during its original review.
    """
    if not math.isfinite(extent) or not 0 < extent < UNITS_PER_EM:
        raise ValueError("Normalized extent must be positive and smaller than one em")
    result = []
    center = (UNITS_PER_EM / 2, BASELINE - UNITS_PER_EM / 2)
    for source in sources:
        points = [point for stroke, _ in source["strokes"] for point in stroke]
        bounds = (min(p[0] for p in points), min(p[1] for p in points),
                  max(p[0] for p in points), max(p[1] for p in points))
        longest = max(bounds[2] - bounds[0], bounds[3] - bounds[1])
        if longest <= 0:
            raise ValueError(f"U+{source['codepoint']:05X}: cannot normalize an empty trajectory")
        factor = extent / longest
        offset = (center[0] - factor * (bounds[0] + bounds[2]) / 2,
                  center[1] - factor * (bounds[1] + bounds[3]) / 2)
        normalized = dict(source)
        normalized["strokes"] = [
            ([(factor*x + offset[0], factor*y + offset[1]) for x, y in stroke], closed)
            for stroke, closed in source["strokes"]
        ]
        normalized["normalization"] = {
            "preserve_aspect_ratio": True, "pen_width_scaled": False,
            "target_centerline_extent": extent,
            "matrix_font_units": [factor, 0, 0, factor, *offset],
            "original_centerline_bounds_font_units": list(bounds),
            "center_font_units": list(center),
        }
        result.append(normalized)
    return result


def family_basename(family: str) -> str:
    basename = re.sub(r"[^A-Za-z0-9]", "", family)
    if not basename:
        raise ValueError("Family name must include at least one ASCII letter or number")
    return basename


def build_font(sources: list[dict], target: Path, family: str = FAMILY,
               font_stroke_width: float | None = None) -> dict:
    basename = family_basename(family)
    if font_stroke_width is not None and (not math.isfinite(font_stroke_width) or font_stroke_width <= 0):
        raise ValueError("font_stroke_width must be finite and positive")
    glyph_names = [f"u{source['codepoint']:05X}" for source in sources]
    glyph_order = [".notdef", *glyph_names]
    glyphs, metrics, reports = {}, {}, {}
    notdef, _ = expand_polylines([([(160, 0), (160, 640), (640, 640), (640, 0)], True)], 16)
    glyphs[".notdef"], metrics[".notdef"] = notdef, (UNITS_PER_EM, 144)
    for name, source in zip(glyph_names, sources):
        width = source["width"] if font_stroke_width is None else font_stroke_width
        glyph, counts = expand_polylines(source["strokes"], width / 2)
        glyph.recalcBounds(None)
        glyphs[name], metrics[name] = glyph, (UNITS_PER_EM, glyph.xMin)
        reports[f"U+{source['codepoint']:05X}"] = {"stroke_width_font_units": width,
                                                "contours": glyph.numberOfContours,
                                                "points": len(glyph.coordinates), **counts}
    fb = FontBuilder(UNITS_PER_EM, isTTF=True)
    fb.setupGlyphOrder(glyph_order)
    fb.setupCharacterMap({source["codepoint"]: name for name, source in zip(glyph_names, sources)})
    fb.setupGlyf(glyphs)
    fb.setupHorizontalMetrics(metrics)
    ascent = max(896, max(glyph.yMax for glyph in glyphs.values()))
    descent = min(-192, min(glyph.yMin for glyph in glyphs.values()))
    fb.setupHorizontalHeader(ascent=ascent, descent=descent, lineGap=0)
    style = "Regular"
    fb.setupNameTable({
        "copyright": "Panorama Gothic contributors, 2026. Generated glyph drawings.",
        "familyName": family, "styleName": style,
        "uniqueFontIdentifier": f"{basename};0.6;{style}",
        "fullName": f"{family} {style}",
        "psName": f"{basename}-{style.replace(' ', '')}",
        "version": "Version 0.6; normalized centerline stroke prototype",
        "description": ("Constant-width centerline expansion. Manual and automatic geometry are "
                        "identified separately in the accompanying manifest; script review is pending."),
        "licenseDescription": "This Font Software is licensed under the SIL Open Font License, Version 1.1.",
        "licenseInfoURL": "https://openfontlicense.org/",
        "typographicFamily": family, "typographicSubfamily": style,
    })
    fb.setupOS2(sTypoAscender=ascent, sTypoDescender=descent, sTypoLineGap=0,
                usWinAscent=ascent, usWinDescent=-descent, usWeightClass=400,
                fsSelection=1 << 6, sxHeight=512, sCapHeight=704)
    fb.setupPost(keepGlyphNames=True)
    fb.setupMaxp()
    # A fixed timestamp makes repeated builds bit-for-bit reproducible.
    fb.font["head"].created = fb.font["head"].modified = 3875126400
    fb.font["head"].fontRevision = 0.6
    fb.font.recalcTimestamp = False
    fb.save(target)
    return reports
