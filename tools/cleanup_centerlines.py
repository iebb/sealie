#!/usr/bin/env python3
"""Remove sub-pen drawing faults from centerline sources (OFL-1.1).

Tracing left some strokes with faults far smaller than the 30-unit pen. They
never read as shapes, but they bump the stroke edge and knot the outline:

* near-zero segments (consecutive vertices closer than 0.3 units);
* back-steps, where a path doubles back along itself and goes on, and
  terminal stubs that retrace the last segment;
* jitter, a run of short segments turning left and right alternately;
* notches, a short interior detour that leaves the stroke's line and returns.

Vertices are only deleted, never moved, so every kept coordinate is the
reviewed one. A jittery stroke is thinned to within 0.4 units of its drawn
line; a notch is at most 5 units deep and 24 long. Closed rings, endpoints
and single-point dots are left alone. The same function runs on glyph sources
and on shared component templates, so assigned paths stay identical.

    python tools/cleanup_centerlines.py --check
    python tools/cleanup_centerlines.py --apply

After --apply run ``svg_font.py --refresh-manifest`` and
``sync_components.py --apply``.
"""
from __future__ import annotations
import argparse, json, math, re, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from compact_backend import trim_retraced_ends, trim_zigzags

TINY = 0.3            # Vertices closer than this to the previous kept one go.
JITTER_TURN = 8.0     # Degrees; smaller alternations are curve sampling.
JITTER_SEGMENT = 4.0  # Jitter is counted on segments shorter than this.
JITTER_COUNT = 3      # Alternations that mark a stroke as jittery.
JITTER_EPSILON = 0.4  # Thinned strokes stay this close to the drawn line.
NOTCH_LENGTH = 24.0   # Longest detour, along the path, treated as a notch.
NOTCH_DEPTH = 5.0     # Deepest detour from the chord that replaces it.
NOTCH_RATIO = 1.4     # Detour length over chord length.
NOTCH_ALIGN = 45.0    # Degrees the stroke may turn into and out of the chord.

# Glyphs where thinning a jittery stroke would open or close a contact at
# Bold. Their paths are kept as drawn, wherever else the same path is shared.
KEEP_AS_DRAWN = ('U3EEC8', 'U3F7C7')

PATH = re.compile(r'(<path\b[^>]*?\bd=")([^"]*)(")')
TOKEN = re.compile(r'[MLZ]|[-+]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][-+]?\d+)?')


def _turn(a, b, c):
    ux, uy, vx, vy = b[0] - a[0], b[1] - a[1], c[0] - b[0], c[1] - b[1]
    return math.degrees(math.atan2(ux * vy - uy * vx, ux * vx + uy * vy))


def _deviation(point, start, end):
    dx, dy = end[0] - start[0], end[1] - start[1]
    length = dx * dx + dy * dy
    t = 0.0 if not length else max(0.0, min(1.0, ((point[0] - start[0]) * dx
                                                 + (point[1] - start[1]) * dy) / length))
    return math.hypot(point[0] - start[0] - t * dx, point[1] - start[1] - t * dy)


def drop_tiny(points):
    kept = [points[0]]
    for point in points[1:-1]:
        if math.dist(point, kept[-1]) >= TINY:
            kept.append(point)
    while len(kept) > 1 and math.dist(points[-1], kept[-1]) < TINY:
        kept.pop()
    kept.append(points[-1])
    return kept


def jitter(points):
    count, previous = 0, 0.0
    for a, b, c in zip(points, points[1:], points[2:]):
        if a == b or b == c:
            continue
        turn = _turn(a, b, c)
        if (abs(turn) > JITTER_TURN and abs(previous) > JITTER_TURN and turn * previous < 0
                and max(math.dist(a, b), math.dist(b, c)) < JITTER_SEGMENT):
            count += 1
        previous = turn
    return count


def thin(points, epsilon=JITTER_EPSILON):
    """Ramer-Douglas-Peucker; keeps a subset of the vertices."""
    keep = [False] * len(points)
    keep[0] = keep[-1] = True
    stack = [(0, len(points) - 1)]
    while stack:
        first, last = stack.pop()
        worst, index = 0.0, None
        for k in range(first + 1, last):
            distance = _deviation(points[k], points[first], points[last])
            if distance > worst:
                worst, index = distance, k
        if index is not None and worst > epsilon:
            keep[index] = True
            stack += [(first, index), (index, last)]
    return [point for point, kept in zip(points, keep) if kept]


def drop_notches(points):
    points = list(points)
    i = 1
    while i < len(points) - 3:
        best, length = None, 0.0
        for j in range(i + 1, len(points) - 1):
            length += math.dist(points[j - 1], points[j])
            if length > NOTCH_LENGTH:
                break
            chord = math.dist(points[i], points[j])
            if j == i + 1 or chord < 1.0 or length < NOTCH_RATIO * chord:
                continue
            if max(_deviation(points[k], points[i], points[j]) for k in range(i + 1, j)) > NOTCH_DEPTH:
                continue
            if (abs(_turn(points[i - 1], points[i], points[j])) > NOTCH_ALIGN
                    or abs(_turn(points[i], points[j], points[j + 1])) > NOTCH_ALIGN):
                continue
            best = j
        if best is None:
            i += 1
        else:
            del points[i + 1:best]
            i += 1
    return points


def clean(points, closed):
    """Return the kept vertices of one stroke and the faults removed."""
    points = list(points)
    found = {}
    if closed or len(points) < 3:
        return points, found

    def step(name, function):
        nonlocal points
        result = function(points)
        if len(result) != len(points):
            found[name] = found.get(name, 0) + len(points) - len(result)
            points = result

    for _ in range(8):  # One fix can expose another; repeat until stable.
        before = len(points)
        step('tiny', drop_tiny)
        step('back_step', lambda value: trim_retraced_ends(trim_zigzags(value)))
        if len(points) >= 3 and jitter(points) >= JITTER_COUNT:
            step('jitter', thin)
        step('notch', drop_notches)
        if len(points) == before or len(points) < 3:
            break
    return points, found


def clean_text(text, keep=frozenset()):
    """Clean every path of one SVG; returns the new text and per-path faults.

    ``keep`` holds path data strings that must stay exactly as drawn.
    """
    report = []
    index = -1

    def replace(match):
        nonlocal index
        index += 1
        if match.group(2) in keep:
            return match.group(0)
        tokens = TOKEN.findall(match.group(2))
        closed = bool(tokens) and tokens[-1] == 'Z'
        numbers = [token for token in tokens if token not in 'MLZ']
        pairs = list(zip(numbers[0::2], numbers[1::2]))
        points = [(float(x), float(y)) for x, y in pairs]
        kept, found = clean(points, closed)
        if not found:
            return match.group(0)
        # Kept vertices are a subsequence; reuse their source tokens verbatim.
        text_pairs, cursor = [], 0
        for point in kept:
            while points[cursor] != point:
                cursor += 1
            text_pairs.append(pairs[cursor])
            cursor += 1
        data = ' L '.join(f'{x} {y}' for x, y in text_pairs)
        report.append({'path': index, 'points': len(points), 'kept': len(kept), **found})
        return match.group(1) + 'M ' + data + match.group(3)

    return PATH.sub(replace, text), report


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    parser.add_argument('--svg-dir', type=Path, default=Path('svg'))
    parser.add_argument('--components-dir', type=Path, default=Path('components'))
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument('--check', action='store_true')
    mode.add_argument('--apply', action='store_true')
    parser.add_argument('--output', type=Path, help='Write changed glyph SVGs here instead of in place')
    parser.add_argument('--report', type=Path)
    args = parser.parse_args(argv)
    totals, rows = {}, []
    keep = frozenset(match.group(2) for name in KEEP_AS_DRAWN
                     for match in PATH.finditer((args.svg_dir / f'{name}.svg').read_text(encoding='utf-8')))
    for folder, kind in ((args.svg_dir, 'glyph'), (args.components_dir, 'component')):
        for path in sorted(folder.glob('*.svg')):
            text = path.read_text(encoding='utf-8')
            cleaned, report = clean_text(text, keep)
            if not report:
                continue
            rows.append({'file': f'{folder.name}/{path.name}', 'kind': kind, 'paths': report})
            for entry in report:
                for name in ('tiny', 'back_step', 'jitter', 'notch'):
                    if name in entry:
                        totals.setdefault(name, [0, 0])
                        totals[name][0] += 1
                        totals[name][1] += entry[name]
            if args.apply:
                path.write_text(cleaned, encoding='utf-8')
            elif args.output and kind == 'glyph':
                args.output.mkdir(parents=True, exist_ok=True)
                (args.output / path.name).write_text(cleaned, encoding='utf-8')
    summary = {'schema_version': 1, 'status': 'applied' if args.apply else ('clean' if not rows else 'cleanup_available'),
               'policy': {'tiny': TINY, 'jitter_epsilon': JITTER_EPSILON, 'jitter_count': JITTER_COUNT,
                          'notch_length': NOTCH_LENGTH, 'notch_depth': NOTCH_DEPTH},
               'files': len(rows), 'glyphs': sum(1 for row in rows if row['kind'] == 'glyph'),
               'paths_and_vertices_removed': {name: {'paths': a, 'vertices': b} for name, (a, b) in sorted(totals.items())}}
    if args.report:
        args.report.write_text(json.dumps({**summary, 'details': rows}, indent=2) + '\n')
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
