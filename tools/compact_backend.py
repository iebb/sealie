"""Analytic round-cap/round-join SVG stroke expansion (OFL-1.1).

Requires skia-pathops==0.9.2. Source polylines are not simplified. Variable
builders must compare topology at all masters, and use the legacy expansion
for every master of a glyph when Skia's offset-join topology changes.
"""
from __future__ import annotations
import math
import pathops
from fontTools.pens.ttGlyphPen import TTGlyphPen
from fontTools.ttLib.tables._g_l_y_f import flagOverlapSimple


def compact_outline(strokes, radius):
    if not math.isfinite(radius) or radius <= 0:
        raise ValueError('Stroke radius must be finite and positive')
    path = pathops.Path()
    source_points = 0
    for points, closed in strokes:
        if not points:
            raise ValueError('Empty source stroke')
        source_points += len(points)
        if closed and len(points) == 1:
            continue  # Closed move-only paths carry no stroke ink.
        path.moveTo(*points[0])
        for point in points[1:]:
            path.lineTo(*point)
        if closed:
            path.close()
        elif len(points) == 1:
            path.lineTo(*points[0])  # Explicit round-cap dot.
    path.stroke(2 * radius, pathops.LineCap.ROUND_CAP,
                pathops.LineJoin.ROUND_JOIN, 4)
    path.convertConicsToQuads(0.05 * radius / 15)
    pen = TTGlyphPen(None)
    path.draw(pen)
    glyph = pen.glyph()
    if glyph.numberOfContours and len(glyph.coordinates) > 65535:
        raise ValueError('TrueType point count limit exceeded')
    if glyph.numberOfContours:
        glyph.flags[0] |= flagOverlapSimple
    return glyph, {'backend': 'analytic-round', 'source_points': source_points,
                   'points': len(glyph.coordinates),
                   'contours': glyph.numberOfContours}


def signature(glyph):
    return tuple(glyph.endPtsOfContours), bytes(int(flag) & 1 for flag in glyph.flags)


def compatible_masters(strokes, widths, legacy_expander):
    candidates = [compact_outline(strokes, width / 2) for width in widths]
    topology = signature(candidates[0][0])
    if all(signature(glyph) == topology for glyph, _ in candidates):
        return candidates, False
    fallback = [legacy_expander(strokes, width / 2) for width in widths]
    topology = signature(fallback[0][0])
    if any(signature(glyph) != topology for glyph, _ in fallback):
        raise ValueError('Legacy fallback masters have incompatible topology')
    return fallback, True
