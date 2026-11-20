"""Analytic round-cap/round-join SVG stroke expansion (OFL-1.1).

Requires skia-pathops==0.9.2. Source polylines are not simplified. Variable
builders must compare topology at all masters, and use the legacy expansion
for every master of a glyph when Skia's offset-join topology changes.

Skia closes every inner join by drawing back to the centerline vertex and out
again. Those zero-width spikes, and the swallowtail loops left where a curve is
tighter than the pen, never change the filled area but show up in outlines as
hairlines across the stroke. ``fold_repair`` collapses each such loop onto the
point where the offset edge crosses itself. Points are moved, never added or
removed, so every master keeps the same contour structure.
"""
from __future__ import annotations
import math
import pathops
from fontTools.pens.recordingPen import RecordingPen
from fontTools.pens.ttGlyphPen import TTGlyphPen
from fontTools.ttLib.tables._g_l_y_f import flagOverlapSimple

FOLD_WINDOW = 256  # Contour edges searched beyond an edge for a fold crossing.
FOLD_STEP = 4      # First search window; widened once shorter loops are gone.


def _cross(ax, ay, bx, by):
    return ax * by - ay * bx


def _segment_crossing(p, q, r, s):
    """Return the proper crossing of segments pq and rs, or None."""
    dx1, dy1 = q[0] - p[0], q[1] - p[1]
    dx2, dy2 = s[0] - r[0], s[1] - r[1]
    denominator = _cross(dx1, dy1, dx2, dy2)
    if abs(denominator) < 1e-12:
        return None
    ex, ey = r[0] - p[0], r[1] - p[1]
    t = _cross(ex, ey, dx2, dy2) / denominator
    u = _cross(ex, ey, dx1, dy1) / denominator
    if not (1e-9 < t < 1 - 1e-9 and 1e-9 < u < 1 - 1e-9):
        return None
    return (p[0] + t * dx1, p[1] + t * dy1)


def _segment_distance(point, segments):
    best = math.inf
    px, py = point
    for (ax, ay), (bx, by) in segments:
        dx, dy = bx - ax, by - ay
        length = dx * dx + dy * dy
        t = 0.0 if not length else max(0.0, min(1.0, ((px - ax) * dx + (py - ay) * dy) / length))
        best = min(best, math.hypot(px - ax - t * dx, py - ay - t * dy))
    return best


def _centerline_distance(point, centerline):
    if len(centerline) == 1:
        return math.dist(point, centerline[0])
    return _segment_distance(point, list(zip(centerline, centerline[1:])))


FOLD_MARGIN = 0.02  # Font units a folded point must lie inside the pen edge.
FOLD_REACH = 4.0    # Radii of centerline, each side of a fold, judged as local.


class _Centerline:
    """Centerline segments, with lookup of Skia's inner-join pivot points."""

    def __init__(self, points, radius):
        self.points = points
        self.segments = list(zip(points, points[1:])) or [(points[0], points[0])]
        self.arc = [0.0]
        for a, b in self.segments:
            self.arc.append(self.arc[-1] + math.dist(a, b))
        self.reach = FOLD_REACH * radius
        self.buckets = {}
        for index, (x, y) in enumerate(points):
            self.buckets.setdefault((math.floor(x), math.floor(y)), []).append(index)

    def pivots(self, point):
        x, y = point
        found = []
        for bx in (math.floor(x) - 1, math.floor(x), math.floor(x) + 1):
            for by in (math.floor(y) - 1, math.floor(y), math.floor(y) + 1):
                for index in self.buckets.get((bx, by), ()):
                    if math.dist(point, self.points[index]) < 1e-3:
                        found.append(index)
        return found

    def local(self, loop):
        """Segments near the loop's pivots; far parts of the stroke are real
        overlaps and must not decide whether a local fold is ink."""
        lengths = [self.arc[index] for point in loop for index in self.pivots(point)]
        if not lengths:
            return self.segments
        low, high = min(lengths) - self.reach, max(lengths) + self.reach
        return [segment for segment, start, end
                in zip(self.segments, self.arc, self.arc[1:])
                if end >= low and start <= high]


def _loop_is_ink(loop, crossing, segments, radius):
    """Accept only a fold: a loop drawn inside the stroke's own ink.

    Points of the true outline lie exactly one radius from the centerline;
    fold points lie closer. The collapse point must be on the pen edge. The
    loop's two ends may sit on the outline (gentle joins fold by less than the
    margin), but every interior point must be covered, and the loop must not
    enclose a counter.
    """
    limit = radius - FOLD_MARGIN
    if _segment_distance(crossing, segments) < limit:
        return False  # Crossing of folded edges; the outer crossing absorbs it.
    if any(_segment_distance(point, segments) >= limit for point in loop[1:-1]):
        return False
    far = max(loop, key=lambda point: math.dist(point, crossing))
    probe = ((far[0] + crossing[0]) / 2, (far[1] + crossing[1]) / 2)
    return _segment_distance(probe, segments) < limit


def _quad_line_crossing(a, c, b, p, q):
    """First parameter u, and point, where quadratic a-c-b properly crosses pq."""
    dx, dy = q[0] - p[0], q[1] - p[1]
    length = dx * dx + dy * dy
    if not length:
        return None
    k0 = _cross(a[0] - p[0], a[1] - p[1], dx, dy)
    k1 = 2 * _cross(c[0] - a[0], c[1] - a[1], dx, dy)
    k2 = _cross(a[0] - 2 * c[0] + b[0], a[1] - 2 * c[1] + b[1], dx, dy)
    if abs(k2) < 1e-12:
        roots = [] if abs(k1) < 1e-12 else [-k0 / k1]
    else:
        disc = k1 * k1 - 4 * k2 * k0
        if disc < 0:
            return None
        root = math.sqrt(disc)
        roots = [(-k1 - root) / (2 * k2), (-k1 + root) / (2 * k2)]
    for u in sorted(roots):
        if not 1e-9 < u < 1 - 1e-9:
            continue
        point = ((1 - u) ** 2 * a[0] + 2 * u * (1 - u) * c[0] + u * u * b[0],
                 (1 - u) ** 2 * a[1] + 2 * u * (1 - u) * c[1] + u * u * b[1])
        v = ((point[0] - p[0]) * dx + (point[1] - p[1]) * dy) / length
        if 1e-9 < v < 1 - 1e-9:
            return u, point
    return None


def _lerp(a, b, u):
    return ((1 - u) * a[0] + u * b[0], (1 - u) * a[1] + u * b[1])


def _quad_at(a, c, b, u):
    return ((1 - u) ** 2 * a[0] + 2 * u * (1 - u) * c[0] + u * u * b[0],
            (1 - u) ** 2 * a[1] + 2 * u * (1 - u) * c[1] + u * u * b[1])


def _quad_quad_crossing(first, second):
    """Parameters and point where two quadratics properly cross, or None."""
    # The first curve is extended past its end and the second before its
    # start, so a loop already closed onto the other curve's end still meets.
    steps, reach = 16, 0.05
    ones = [k * (1 + reach) / steps for k in range(steps + 1)]
    twos = [-reach + k * (1 + reach) / steps for k in range(steps + 1)]
    one = [_quad_at(*first, u) for u in ones]
    two = [_quad_at(*second, v) for v in twos]
    for m in range(steps):
        for n in range(steps):
            point = _segment_crossing(one[m], one[m + 1], two[n], two[n + 1])
            if point is None:
                continue
            fraction = lambda s, e: math.dist(s, point) / max(math.dist(s, e), 1e-12)
            u = ones[m] + fraction(one[m], one[m + 1]) * (ones[1] - ones[0])
            v = twos[n] + fraction(two[n], two[n + 1]) * (twos[1] - twos[0])
            for _ in range(8):  # Newton on B1(u) - B2(v) = 0.
                (a, c, b), (d, e, f) = first, second
                p, q = _quad_at(a, c, b, u), _quad_at(d, e, f, v)
                du = [2 * ((1 - u) * (c[k] - a[k]) + u * (b[k] - c[k])) for k in (0, 1)]
                dv = [2 * ((1 - v) * (e[k] - d[k]) + v * (f[k] - e[k])) for k in (0, 1)]
                det = _cross(-dv[0], -dv[1], du[0], du[1])
                if abs(det) < 1e-12:
                    break
                gx, gy = p[0] - q[0], p[1] - q[1]
                u -= _cross(gx, gy, -dv[0], -dv[1]) / -det
                v -= _cross(du[0], du[1], gx, gy) / -det
            if not (1e-9 < u < 1 + reach and -reach < v < 1 - 1e-9):
                return None
            u, v = min(u, 1.0), max(v, 0.0)
            return u, v, _quad_at(*first, u)
    return None


def _edge_curve(points, on_curve, k):
    """Edge k as ('line', p, q), ('quad', a, c, b, a_index, control, b_index) or None."""
    count = len(points)
    at = lambda n: points[n % count]
    on = lambda n: on_curve[n % count]
    if on(k) and on(k + 1):
        return ('line', at(k), at(k + 1), k, None, k + 1)
    if on(k) and on(k + 2):
        return ('quad', at(k), at(k + 1), at(k + 2), k, k + 1, k + 2)
    if on(k - 1) and on(k + 1):
        return ('quad', at(k - 1), at(k), at(k + 1), k - 1, k, k + 1)
    return None  # Leg of a multi-control quadratic.


def _curve_crossing(points, on_curve, i, j):
    """True crossing of edges i and j when either is a quadratic's leg.

    A crossing on the control polygon is not on the outline, so find where
    the curves themselves meet. Returns the crossing, the indices to collapse
    onto it and the (control index, new position) moves that split each curve
    there (de Casteljau), so the parts that remain are unchanged; or None.
    """
    one, two = _edge_curve(points, on_curve, i), _edge_curve(points, on_curve, j)
    if one is None or two is None or one[0] == two[0] == 'line':
        return None
    first = i + 1 if one[0] == 'line' else one[-1]
    last = j if two[0] == 'line' else two[-3]
    if one[0] == 'quad' and two[0] == 'quad' and one[-1] > two[-3]:
        return None  # Adjacent curves share an end; nothing between them.
    if last < first:
        return None
    if one[0] == 'line':
        found = _quad_line_crossing(*two[1:4], one[1], one[2])
        if found is None:
            return None
        v, point = found
        u = None
    elif two[0] == 'line':
        found = _quad_line_crossing(*one[1:4], two[1], two[2])
        if found is None:
            return None
        u, point = found
        v = None
    else:
        found = _quad_quad_crossing(one[1:4], two[1:4])
        if found is None:
            return None
        u, v, point = found
    moves = []
    if u is not None:
        moves.append((one[5], _lerp(one[1], one[2], u)))
    if v is not None:
        moves.append((two[5], _lerp(two[2], two[3], v)))
    return point, range(first, last + 1), moves


def fold_repair(points, centerline, radius, closed=True, on_curve=None):
    """Collapse local self-crossing loops of one contour in place.

    ``points`` is a list of mutable [x, y] pairs in contour order and
    ``on_curve`` their on-curve flags. Loops are collapsed shortest first: a
    counter's inner edge only lies on the pen edge once the folds along it are
    gone, so it is never mistaken for one. A crossing on a quadratic's control
    leg is not on the outline, and moving one end of that curve would bulge
    it past the pen, so such a loop collapses onto the curve's own crossing
    with the line and the curve is split there (``_curve_crossing``).
    Returns the number of collapsed loops.
    """
    count = len(points)
    if count < 4:
        return 0
    if on_curve is None:
        on_curve = [True] * count
    centerline = _Centerline(centerline, radius)
    repaired = 0
    window = FOLD_STEP
    for _ in range(64):
        changed = False
        edges = count if closed else count - 1
        i = 0
        while i < edges:
            p, q = points[i], points[(i + 1) % count]
            if p == q:
                i += 1
                continue
            straight_i = on_curve[i] and on_curve[(i + 1) % count]
            low_x, high_x = min(p[0], q[0]), max(p[0], q[0])
            low_y, high_y = min(p[1], q[1]), max(p[1], q[1])
            limit = min(i + window, i + edges - 2 if closed else edges - 1)
            for j in range(i + 2, limit + 1):
                r, s = points[j % count], points[(j + 1) % count]
                rx, sx = r[0], s[0]
                if (rx < low_x and sx < low_x) or (rx > high_x and sx > high_x):
                    continue
                ry, sy = r[1], s[1]
                if (ry < low_y and sy < low_y) or (ry > high_y and sy > high_y):
                    continue
                straight_j = on_curve[j % count] and on_curve[(j + 1) % count]
                crossing = _segment_crossing(p, q, r, s)
                if crossing is None:
                    continue
                loop = [points[k % count] for k in range(i + 1, j + 1)]
                refined = None
                if not (straight_i and straight_j):
                    refined = _curve_crossing(points, on_curve, i, j)
                    if refined is None:
                        continue
                    crossing = refined[0]
                if not _loop_is_ink(loop, crossing, centerline.local(loop), radius):
                    continue
                if refined is not None:
                    _, indices, moves = refined
                    loop = [points[k % count] for k in indices]
                    for control, moved in moves:
                        points[control % count][0], points[control % count][1] = moved
                for point in loop:
                    point[0], point[1] = crossing
                repaired += 1
                changed = True
                i = j - 1
                break
            i += 1
        if not changed:
            if window >= FOLD_WINDOW:
                break
            window = min(window * 4, FOLD_WINDOW)
    # Where a turn is much tighter than the pen, the inner offset shrinks to a
    # sub-unit cluster whose edges need not cross; drop any join spike still
    # reaching the centerline. Triangle A-pivot-B lies inside the pivot's disk.
    for index, point in enumerate(points):
        if on_curve[index] and centerline.pivots(point):
            before, after = points[index - 1], points[(index + 1) % count]
            if not (on_curve[index - 1] and on_curve[(index + 1) % count]):
                continue
            if centerline.pivots(before) or centerline.pivots(after):
                continue
            point[0] = (before[0] + after[0]) / 2
            point[1] = (before[1] + after[1]) / 2
            repaired += 1
    return repaired


TRIM_TOLERANCE = 0.01  # Font units; a stub this close to its retrace adds no ink.


def _on_segment(point, start, end, tolerance=TRIM_TOLERANCE):
    if start == end:
        return math.dist(point, start) <= tolerance
    return _segment_distance(point, [(start, end)]) <= tolerance


def trim_retraced_ends(points):
    """Drop terminal vertices that double back along the previous segment.

    Such a stub adds no ink (its cap sits inside the segment it retraces), but
    the 180-degree join Skia draws for it leaves a hairline across the stroke.
    """
    points = list(points)
    while len(points) >= 3 and _on_segment(points[-1], points[-3], points[-2]):
        points.pop()
    while len(points) >= 3 and _on_segment(points[0], points[2], points[1]):
        points.pop(0)
    return points


ZIGZAG_TOLERANCE = 0.5  # Font units a back-step may stray from the line it retraces.


def _reverses(a, b, c):
    """True when the path turns back by more than 150 degrees at b."""
    ux, uy, vx, vy = b[0] - a[0], b[1] - a[1], c[0] - b[0], c[1] - b[1]
    lengths = math.hypot(ux, uy) * math.hypot(vx, vy)
    return lengths > 0 and ux * vx + uy * vy < -math.cos(math.pi / 6) * lengths


def trim_zigzags(points):
    """Drop interior back-steps: A-B-C-D where C retraces onto AB and B lies on CD.

    The pen covers C from A-B to within the tolerance, but each 180-degree
    turn leaves a round-cap arc and a pivot spike inside the ink. Only C is
    dropped; B stays, so A-B-D keeps the stroke's own edge.
    """
    points = list(points)
    i = 1
    while i + 2 < len(points):
        a, b, c, d = points[i - 1:i + 3]
        if (_reverses(a, b, c) and _reverses(b, c, d)
                and _on_segment(c, a, b, ZIGZAG_TOLERANCE)
                and _on_segment(b, c, d, ZIGZAG_TOLERANCE)):
            del points[i + 1]
            i = max(1, i - 1)
        else:
            i += 1
    return points


def _ring_is_filled(points, radius):
    """True when the pen covers a closed ring's whole interior.

    Skia's inner contour then lies entirely inside ink; collapsing its loops
    could turn part of it back into a hole, so such rings are left unrepaired.
    """
    xs, ys = [x for x, _ in points], [y for _, y in points]
    low_x, high_x, low_y, high_y = min(xs), max(xs), min(ys), max(ys)
    if min(high_x - low_x, high_y - low_y) > 4 * radius:
        return False
    segments = list(zip(points, points[1:] + points[:1]))
    y = math.floor(low_y) + 0.5
    while y < high_y:
        crossings = sorted(ax + (y - ay) * (bx - ax) / (by - ay)
                           for (ax, ay), (bx, by) in segments
                           if (ay <= y) != (by <= y))
        for left, right in zip(crossings[::2], crossings[1::2]):
            x = math.floor(left) + 0.5
            while x < right:
                if _segment_distance((x, y), segments) > radius:
                    return False
                x += 1.0
        y += 1.0
    return True


def _stroke(points, closed, radius):
    path = pathops.Path()
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
    recording = RecordingPen()
    path.draw(recording)
    return recording.value


def _draw_repaired(value, pen, centerline, radius):
    """Replay one stroked outline into ``pen`` with fold loops collapsed."""
    repaired = 0
    contour = []
    for operator, arguments in value:
        contour.append((operator, [list(point) for point in arguments]))
        if operator not in ('closePath', 'endPath'):
            continue
        points = [point for _, arguments in contour for point in arguments]
        on_curve = [operator != 'qCurveTo' or index == len(arguments) - 1
                    for operator, arguments in contour
                    for index in range(len(arguments))]
        repaired += fold_repair(points, centerline, radius, on_curve=on_curve)
        for name, arguments in contour:
            getattr(pen, name)(*[tuple(point) for point in arguments])
        contour = []
    return repaired


def _draw_filled_ring(value, pen, centerline, radius):
    """Replay a filled ring with its inside-out inner contour folded flat.

    The pen covers the ring's hole, so Skia's inner contour lies wholly inside
    ink and only draws join spikes. Its points are moved onto one straight
    edge of the outer contour: zero area, so fill can only gain ink the pen
    covers anyway, and the outline shows no extra line.
    """
    contours, contour = [], []
    for operator, arguments in value:
        contour.append((operator, [list(point) for point in arguments]))
        if operator in ('closePath', 'endPath'):
            contours.append(contour)
            contour = []
    segments = list(zip(centerline, centerline[1:]))
    limit = radius - FOLD_MARGIN
    buried = [all(_segment_distance(point, segments) < limit
                  for _, arguments in contour for point in arguments)
              for contour in contours]
    edge = None
    for contour, inside in zip(contours, buried):
        if inside:
            continue
        previous = None
        for operator, arguments in contour:
            if operator == 'lineTo' and previous is not None and previous != arguments[0]:
                edge = list(previous), list(arguments[0])
                break
            if arguments:
                previous = arguments[-1]
        if edge:
            break
    folds = 0
    for contour, inside in zip(contours, buried):
        if inside and edge:
            points = [point for _, arguments in contour for point in arguments]
            # Start apart from the rest so the contour keeps two distinct
            # points; a closing duplicate of the start must stay one, because
            # the pen drops it and every master needs the same point count.
            closes = len(points) > 2 and points[-1] == points[0]
            points[0][0], points[0][1] = edge[0]
            for point in points[1:]:
                point[0], point[1] = edge[1]
            if closes:
                points[-1][0], points[-1][1] = edge[0]
            folds += 1
        for name, arguments in contour:
            getattr(pen, name)(*[tuple(point) for point in arguments])
    return folds


def compact_outline(strokes, radius, repair=True, fold_rings=True):
    if not math.isfinite(radius) or radius <= 0:
        raise ValueError('Stroke radius must be finite and positive')
    pen = TTGlyphPen(None)
    source_points = 0
    folds = 0
    for points, closed in strokes:
        if not points:
            raise ValueError('Empty source stroke')
        source_points += len(points)
        if closed and len(points) == 1:
            continue  # Closed move-only paths carry no stroke ink.
        if repair and not closed:
            points = trim_retraced_ends(trim_zigzags(points))
        value = _stroke(points, closed, radius)
        filled = repair and closed and _ring_is_filled(list(points), radius)
        if filled and fold_rings:
            folds += _draw_filled_ring(value, pen, list(points) + [points[0]], radius)
        elif repair and not filled:
            centerline = list(points) + ([points[0]] if closed else [])
            folds += _draw_repaired(value, pen, centerline, radius)
        else:
            for operator, arguments in value:
                getattr(pen, operator)(*arguments)
    glyph = pen.glyph()
    if glyph.numberOfContours and len(glyph.coordinates) > 65535:
        raise ValueError('TrueType point count limit exceeded')
    if glyph.numberOfContours:
        glyph.flags[0] |= flagOverlapSimple
    return glyph, {'backend': 'analytic-round', 'source_points': source_points,
                   'points': len(glyph.coordinates),
                   'contours': glyph.numberOfContours, 'folds': folds}


def signature(glyph):
    return tuple(glyph.endPtsOfContours), bytes(int(flag) & 1 for flag in glyph.flags)


def _compact_masters(strokes, widths, repair, fold_rings=True):
    candidates = [compact_outline(strokes, width / 2, repair, fold_rings)
                  for width in widths]
    topology = signature(candidates[0][0])
    if all(signature(glyph) == topology for glyph, _ in candidates):
        return candidates
    return None


def _between(a, p, q):
    """True when integer point a lies exactly on segment pq."""
    if (a[0] - p[0]) * (q[1] - p[1]) != (a[1] - p[1]) * (q[0] - p[0]):
        return False
    return (min(p[0], q[0]) <= a[0] <= max(p[0], q[0])
            and min(p[1], q[1]) <= a[1] <= max(p[1], q[1]))


def prune_masters(glyphs):
    """Drop on-curve points that are redundant in every master.

    A point goes only if, at all weights, it repeats the previous kept point
    or lies exactly on the straight edge between its on-curve neighbours, so
    each master's outline is unchanged and the masters stay compatible.
    Returns the number of points removed per master.
    """
    first = glyphs[0]
    if not first.numberOfContours:
        return 0
    flags = first.flags
    coordinates = [glyph.coordinates for glyph in glyphs]
    keep, ends, start = [], [], 0
    for end in first.endPtsOfContours:
        kept = [start]
        for index in range(start + 1, end + 1):
            last = kept[-1]
            following = index + 1 if index < end else start
            if flags[index] & 1 and flags[last] & 1:
                if all(c[index] == c[last] for c in coordinates):
                    continue
                if (flags[following] & 1 and end - index + len(kept) >= 3
                        and all(_between(c[index], c[last], c[following])
                                for c in coordinates)):
                    continue
            kept.append(index)
        keep.extend(kept)
        ends.append(len(keep) - 1)
        start = end + 1
    removed = len(flags) - len(keep)
    if removed:
        for glyph in glyphs:
            glyph.coordinates = type(glyph.coordinates)(
                [glyph.coordinates[index] for index in keep])
            glyph.flags = type(glyph.flags)(
                glyph.flags.typecode, [glyph.flags[index] for index in keep])
            glyph.endPtsOfContours = list(ends)
    return removed


def compatible_masters(strokes, widths, legacy_expander):
    # Fold repair only moves points; if a collapse ever lands on a contour's
    # start point the pen drops the closing duplicate, so fall back to the
    # unrepaired outline before resorting to the legacy disk stroker. Folding
    # a pen-filled ring is tried first and given up first, since a ring may be
    # filled at some weights only.
    for repair, fold_rings in ((True, True), (True, False), (False, False)):
        candidates = _compact_masters(strokes, widths, repair, fold_rings)
        if candidates is not None:
            removed = prune_masters([glyph for glyph, _ in candidates])
            for glyph, info in candidates:
                info['points'] = len(glyph.coordinates)
                info['pruned'] = removed
            return candidates, False
    fallback = [legacy_expander(strokes, width / 2) for width in widths]
    topology = signature(fallback[0][0])
    if any(signature(glyph) != topology for glyph, _ in fallback):
        raise ValueError('Legacy fallback masters have incompatible topology')
    return fallback, True
