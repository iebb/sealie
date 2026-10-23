"""Conservative optical fitting of Sealie round-centerline glyphs.

Pure Python: no rasterizer, AI service, mutable global registry or font dependency.
The caller supplies the previously measured metric record. Standalone dictionary
radicals and naturally simple/narrow/short forms preserve their existing shape.
"""
from __future__ import annotations
from math import isfinite


def _clamp(value, lo, hi):
    return max(lo, min(hi, value))


def _standalone_radical(metric):
    cp = str(metric.get('codepoint', '')).upper().removeprefix('U+').removeprefix('U')
    return any(value.split('.')[-1].upper() == cp
               for value in str(metric.get('radical', '')).split())


def optical_fit(strokes, metric):
    """Return ``(strokes, record)`` without modifying the input.

    ``strokes`` is an iterable of ``(points, closed)`` pairs; each point is ``x,y``
    in the font frame (center512,320). ``metric`` is keyed as in the accompanying
    all-glyph audit. The pen remains30 units; only centerline coordinates move.
    """
    original = [([(float(x), float(y)) for x, y in points], bool(closed))
                for points, closed in strokes]
    reasons = []
    if len(original) < 5:
        reasons.append('simple_form_fewer_than_5_paths')
    ink_width = float(metric['ink_width'])
    if ink_width < 360:
        reasons.append('natural_narrow_form_ink_width_below_360')
    if abs(float(metric['centerline_height']) - 738) > 1e-6:
        reasons.append('natural_short_or_wide_form_not_full_height')
    if _standalone_radical(metric):
        reasons.append('standalone_dictionary_radical')
    record = {
        'codepoint': metric.get('codepoint'), 'eligible': not reasons,
        'reasons': reasons, 'path_count': len(original), 'pen_width': 30,
        'before_ink_width': ink_width, 'x_scale': 1.0,
        'offset_x': 0.0, 'offset_y': 0.0,
    }
    if reasons:
        record['after_ink_width'] = ink_width
        return original, record
    target = 560 + 0.35 * (ink_width - 560)
    scale = _clamp((target - 30) / (ink_width - 30), .90, 1.12)
    dx = _clamp(-.25 * float(metric['mass_dx']) * scale, -12.0, 12.0)
    dy = _clamp(-.25 * float(metric['mass_dy']), -16.0, 16.0)
    assert all(isfinite(v) for v in (scale, dx, dy))
    result = [([(512 + (x - 512) * scale + dx, y + dy) for x, y in points], closed)
              for points, closed in original]
    record.update({
        'target_ink_width_before_cap': target, 'x_scale': scale,
        'offset_x': dx, 'offset_y': dy,
        'after_ink_width': (ink_width - 30) * scale + 30,
        'changed': abs(scale - 1) > 1e-12 or abs(dx) > 1e-12 or abs(dy) > 1e-12,
    })
    return result, record
