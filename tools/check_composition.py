#!/usr/bin/env python3
"""Audit every glyph against Sealie's composition rules (docs/COMPOSITION.md).

Pure Python, read-only. Measures each centerline source at the Regular pen and
reports where it departs from the frame, width and spacing rules. The rules
are Sealie's own; no reference font or image is read.

    python tools/check_composition.py --report reports/composition.json

With --check the audit is compared with the committed report instead of being
written: the exit status is 1 if any glyph departs from a rule it kept before.
Departures already recorded there are the known exceptions.
"""
from __future__ import annotations
import argparse, json, math, re
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

PEN = 30.0
R = PEN / 2
TOP, BOTTOM, AXIS, MIDDLE = 704.0, -64.0, 512.0, 320.0   # F2: ordinary body frame
BODY = TOP - BOTTOM                                       # 768
STANDARD_WIDTH, WIDE_WIDTH = 520.0, 640.0                 # F3
TOLERANCE = 2.0
OPEN_AT_BOLD = 20.0   # S4: white needed at Regular to stay open at Bold (pen +19.5)
HARD_GAP = 0.5        # S4: least white between strokes that do not join
COVERED = 10.0        # S4: a third centerline this close to the narrowest point means it is inked
BAND_GAP = 8.0        # C1: least white channel that separates columns or rows
EM = (0.0, 1024.0, -192.0, 896.0)

# F4: the closed set of short forms, as ink height x ink width, centred on y=320.
SHORT_FORMS = {
    '3D000': (30, 470), '3D007': (440, 430), '3D010': (440, 430), '3F850': (440, 430),
    '3D066': (540, 430), '3FB72': (640, 430), '3D068': (620, 430), '3D06D': (620, 430),
    '3DDBF': (580, 430), '3F859': (680, 430), '3D113': (640, 450), '3FBAD': (650, 500),
    '3DD6E': (650, 500), '3D011': (700, 430), '3D012': (680, 400), '3D4C4': (680, 430),
    '3D5E5': (700, 430), '3D67E': (700, 470), '3D689': (680, 430), '3D8D5': (660, 430),
    '3D374': (600, 340), '3E1C9': (640, 470), '3E1CF': (620, 430), '3E2F3': (640, 360),
    '3E352': (640, 450), '3E375': (680, 510), '3F912': (640, 400), '3D97F': (640, 340),
    '3FA5D': (620, 450), '3F60C': (700, 400), '3FB8D': (700, 450), '3F5B3': (700, 490),
    '3F59A': (640, 450), '3DA16': (680, 470), '3D64A': (700, 470), '3D3DC': (700, 430),
    '3D420': (700, 430), '3D3B7': (700, 470), '3D32C': (660, 490), '3D590': (700, 450),
    '3DA48': (680, 380), '3DB5D': (660, 450), '3DE14': (660, 400), '3DE16': (660, 400),
    '3E37E': (700, 430), '3E38B': (700, 400), '3E882': (700, 360), '3E895': (700, 490),
    '3EB0A': (700, 400), '3EB5C': (680, 450), '3F2E0': (700, 320),
}

TOKEN = re.compile(r'[MLZ]|[-+]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][-+]?\d+)?')
PATH = re.compile(r'<path\b[^>]*?\bd="([^"]*)"')


def read_strokes(path):
    strokes = []
    for data in PATH.findall(Path(path).read_text(encoding='utf-8')):
        tokens = TOKEN.findall(data)
        numbers = [float(token) for token in tokens if token not in 'MLZ']
        points = list(zip(numbers[0::2], numbers[1::2]))
        if tokens[-1] == 'Z':
            points.append(points[0])
        if len(points) == 1:
            points.append(points[0])
        strokes.append(points)
    return strokes


def _foot(p, a, b):
    """Distance from p to segment ab, and the nearest point on it."""
    dx, dy = b[0] - a[0], b[1] - a[1]
    length = dx * dx + dy * dy
    t = 0.0 if not length else max(0.0, min(1.0, ((p[0] - a[0]) * dx + (p[1] - a[1]) * dy) / length))
    q = (a[0] + t * dx, a[1] + t * dy)
    return math.hypot(p[0] - q[0], p[1] - q[1]), q


def _point_segment(p, a, b):
    return _foot(p, a, b)[0]


def _crosses(a, b, c, d):
    def side(p, q, r):
        return (q[0] - p[0]) * (r[1] - p[1]) - (q[1] - p[1]) * (r[0] - p[0])
    return side(a, b, c) * side(a, b, d) < 0 and side(c, d, a) * side(c, d, b) < 0


def closest_points(first, second, limit):
    """Least distance between two polylines with the two points that realise it, or None beyond ``limit``."""
    best = (limit, None, None)
    for a, b in zip(first, first[1:]):
        for c, d in zip(second, second[1:]):
            if (max(c[0], d[0]) < min(a[0], b[0]) - best[0] or min(c[0], d[0]) > max(a[0], b[0]) + best[0] or
                    max(c[1], d[1]) < min(a[1], b[1]) - best[0] or min(c[1], d[1]) > max(a[1], b[1]) + best[0]):
                continue
            for p, (u, v), swap in ((a, (c, d), False), (b, (c, d), False), (c, (a, b), True), (d, (a, b), True)):
                distance, q = _foot(p, u, v)
                if distance < best[0]:
                    best = (distance, q, p) if swap else (distance, p, q)
    return None if best[1] is None else best


def stroke_distance(first, second, limit):
    """Least distance between two polylines, or ``limit`` if they are farther apart."""
    best = limit
    for a, b in zip(first, first[1:]):
        ax0, ax1 = min(a[0], b[0]) - best, max(a[0], b[0]) + best
        ay0, ay1 = min(a[1], b[1]) - best, max(a[1], b[1]) + best
        for c, d in zip(second, second[1:]):
            if max(c[0], d[0]) < ax0 or min(c[0], d[0]) > ax1 or max(c[1], d[1]) < ay0 or min(c[1], d[1]) > ay1:
                continue
            if _crosses(a, b, c, d):
                return 0.0
            best = min(best, _point_segment(a, c, d), _point_segment(b, c, d),
                       _point_segment(c, a, b), _point_segment(d, a, b))
            ax0, ax1 = min(a[0], b[0]) - best, max(a[0], b[0]) + best
            ay0, ay1 = min(a[1], b[1]) - best, max(a[1], b[1]) + best
    return best


def bands(intervals):
    """Merge ink intervals; bands are separated by at least BAND_GAP of white."""
    intervals = sorted(intervals)
    merged = [list(intervals[0])]
    for low, high in intervals[1:]:
        if low - merged[-1][1] >= BAND_GAP:
            merged.append([low, high])
        else:
            merged[-1][1] = max(merged[-1][1], high)
    return merged


def measure(job):
    codepoint, path = job
    strokes = read_strokes(path)
    boxes = [(min(x for x, _ in s), max(x for x, _ in s), min(y for _, y in s), max(y for _, y in s))
             for s in strokes]
    x0 = min(b[0] for b in boxes) - R; x1 = max(b[1] for b in boxes) + R
    y0 = min(b[2] for b in boxes) - R; y1 = max(b[3] for b in boxes) + R
    columns = bands([(b[0] - R, b[1] + R) for b in boxes])
    rows = bands([(b[2] - R, b[3] + R) for b in boxes])
    count = len(strokes)
    parent = list(range(count))

    def find(a):
        while parent[a] != a:
            parent[a] = parent[parent[a]]
            a = parent[a]
        return a

    reach = PEN + OPEN_AT_BOLD + 10
    tightest = None
    for i in range(count):
        for j in range(i + 1, count):
            a, b = boxes[i], boxes[j]
            if a[0] - b[1] > reach or b[0] - a[1] > reach or a[2] - b[3] > reach or b[2] - a[3] > reach:
                continue
            distance = stroke_distance(strokes[i], strokes[j], reach)
            if distance < PEN:            # the two pens overlap: the strokes join
                parent[find(i)] = find(j)
            elif distance < reach:
                # The narrowest point between the two strokes is white only if no third stroke's ink lies on it.
                _, p, q = closest_points(strokes[i], strokes[j], reach + 1)
                middle = ((p[0] + q[0]) / 2, (p[1] + q[1]) / 2)
                if any(k != i and k != j and
                       min(_point_segment(middle, a, b) for a, b in zip(strokes[k], strokes[k][1:])) < COVERED
                       for k in range(count)):
                    continue
                white = distance - PEN
                tightest = white if tightest is None else min(tightest, white)
    width, height = x1 - x0, y1 - y0
    record = {
        'codepoint': 'U+' + codepoint, 'strokes': count, 'pieces': len({find(i) for i in range(count)}),
        'ink': [round(x0, 1), round(y0, 1), round(x1, 1), round(y1, 1)],
        'width': round(width, 1), 'height': round(height, 1),
        'columns': len(columns), 'rows': len(rows),
        'column_gaps': [round(b[0] - a[1], 1) for a, b in zip(columns, columns[1:])],
        'row_gaps': [round(b[0] - a[1], 1) for a, b in zip(rows, rows[1:])],
        'tightest_gap': None if tightest is None else round(tightest, 1),
    }
    notes = []
    if x0 < EM[0] or x1 > EM[1] or y0 < EM[2] or y1 > EM[3]:
        notes.append('F1 ink outside the em box')
    short = SHORT_FORMS.get(codepoint)
    if short:
        record['frame'] = 'short'
        if abs(height - short[0]) > TOLERANCE or abs(width - short[1]) > TOLERANCE:
            notes.append(f'F4 short form is {height:.0f}x{width:.0f}, registered {short[0]}x{short[1]}')
        if abs((y0 + y1) / 2 - MIDDLE) > TOLERANCE:
            notes.append(f'F4 short form centred on y={(y0 + y1) / 2:.0f}, not {MIDDLE:.0f}')
    else:
        record['frame'] = 'body'
        if abs(y1 - TOP) > TOLERANCE:
            notes.append(f'F2 ink top {y1:.0f}, not {TOP:.0f}')
        if abs(y0 - BOTTOM) > TOLERANCE:
            notes.append(f'F2 ink bottom {y0:.0f}, not {BOTTOM:.0f}')
    if abs((x0 + x1) / 2 - AXIS) > TOLERANCE:
        notes.append(f'F2 ink centred on x={(x0 + x1) / 2:.0f}, not {AXIS:.0f}')
    if width > WIDE_WIDTH + TOLERANCE:
        notes.append(f'F3 width {width:.0f} over {WIDE_WIDTH:.0f}')
    record['width_class'] = ('narrow' if width < STANDARD_WIDTH - TOLERANCE else
                             'standard' if width <= STANDARD_WIDTH + TOLERANCE else 'wide')
    if tightest is not None and tightest < HARD_GAP:
        notes.append(f'S4 separate strokes {tightest:.2f} apart')
    record['closes_by_bold'] = tightest is not None and tightest < OPEN_AT_BOLD
    record['notes'] = notes
    return record


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    parser.add_argument('--svg-dir', type=Path, default=Path('svg'))
    parser.add_argument('--report', type=Path, default=Path('reports/composition.json'))
    parser.add_argument('--check', action='store_true', help='compare with the report; write nothing')
    parser.add_argument('--workers', type=int, default=None)
    args = parser.parse_args(argv)
    rows = json.loads((args.svg_dir / 'manifest.json').read_text())['glyphs']
    jobs = [(row['codepoint'][2:], str(args.svg_dir / f"U{row['codepoint'][2:]}.svg")) for row in rows]
    with ProcessPoolExecutor(max_workers=args.workers) as pool:
        records = list(pool.map(measure, jobs, chunksize=64))
    def count(test):
        return sum(1 for record in records if test(record))
    rules = {}
    for record in records:
        for note in record['notes']:
            rules.setdefault(note.split()[0], []).append(record['codepoint'])
    summary = {
        'schema_version': 1, 'guideline': 'docs/COMPOSITION.md', 'glyph_count': len(records),
        'pen': PEN, 'body_frame': {'top': TOP, 'bottom': BOTTOM, 'axis': AXIS, 'height': BODY},
        'frames': {'body': count(lambda r: r['frame'] == 'body'), 'short': count(lambda r: r['frame'] == 'short')},
        'width_classes': {name: count(lambda r, name=name: r['width_class'] == name)
                          for name in ('narrow', 'standard', 'wide')},
        'columns': {str(n): count(lambda r, n=n: r['columns'] == n) for n in sorted({r['columns'] for r in records})},
        'rows': {str(n): count(lambda r, n=n: r['rows'] == n) for n in sorted({r['rows'] for r in records})},
        'glyphs_with_a_gap_that_closes_by_bold': count(lambda r: r['closes_by_bold']),
        'departures': {rule: {'count': len(found), 'codepoints': found} for rule, found in sorted(rules.items())},
    }
    new = {}
    if args.check:
        known = json.loads(args.report.read_text())['departures']
        for rule, found in summary['departures'].items():
            added = sorted(set(found['codepoints']) - set(known.get(rule, {}).get('codepoints', [])))
            if added:
                new[rule] = added
    else:
        args.report.write_text(json.dumps({**summary, 'glyphs': records}, separators=(',', ':')) + '\n')
    printable = dict(summary)
    printable['departures'] = {rule: {'count': v['count'], 'codepoints': v['codepoints'][:12]}
                               for rule, v in summary['departures'].items()}
    if args.check:
        printable['status'] = 'new departures' if new else 'clean'
        printable['new_departures'] = new
    print(json.dumps(printable, indent=2))
    return 1 if new else 0


if __name__ == '__main__':
    raise SystemExit(main())
