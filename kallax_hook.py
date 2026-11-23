"""Clip-on clothes hook for IKEA Kallax. Slides onto the front edge of a shelf.

Usage: python3 kallax_hook.py [shelf_thickness_mm ...]
Kallax: inner shelves/dividers 16 mm, outer frame 39 mm. Measure yours first.
"""
import sys
import math
import datetime
import numpy as np
import trimesh
from shapely.geometry import box, LineString, Point
from shapely.ops import unary_union

VERSION = "v1"
WIDTH = 25.0      # extrusion width of the hook (mm)
ARM_LEN = 70.0    # how deep the clip reaches onto the shelf
ARM_T = 3.0       # thickness of the two clip arms
BODY_T = 5.0      # thickness of the front web and the hook
CLEAR = 0.3       # clearance added to the shelf thickness
GRIP = 0.5        # how far the grip ridge protrudes into the gap
DROP = 16.0       # straight part below the shelf before the curve
HOOK_R = 13.0     # centreline radius of the hook curve
TIP_LEN = 12.0    # upward tip after the curve
TIP_LEAN = 12.0   # tip leans outward (degrees)


def profile(shelf_t):
    """2D side profile. Shelf occupies x <= 0, -shelf_t <= y <= 0."""
    gap = shelf_t + CLEAR
    x_web = 0.4                                  # small gap to the shelf edge
    top = box(-ARM_LEN, 0, x_web + BODY_T, ARM_T)
    web = box(x_web, -gap - ARM_T, x_web + BODY_T, ARM_T)
    bottom = box(-ARM_LEN, -gap - ARM_T, x_web, -gap)
    ridge = Point(-ARM_LEN + 4, -gap - 1.5 + GRIP).buffer(1.5, 32)

    xc = x_web + BODY_T / 2
    y0 = -gap - ARM_T - DROP
    pts = [(xc, -gap), (xc, y0)]
    for a in np.linspace(180, 360, 40):
        pts.append((xc + HOOK_R + HOOK_R * math.cos(math.radians(a)),
                    y0 + HOOK_R * math.sin(math.radians(a))))
    lean = math.radians(TIP_LEAN)
    pts.append((pts[-1][0] + TIP_LEN * math.sin(lean),
                pts[-1][1] + TIP_LEN * math.cos(lean)))
    hook = LineString(pts).buffer(BODY_T / 2, 32)

    shape = unary_union([top, web, bottom, ridge, hook])
    shape = shape.buffer(0.8, 16).buffer(-0.8, 16)   # fillet inner corners
    shape = shape.buffer(-0.6, 16).buffer(0.6, 16)   # round outer corners
    return shape


def build(shelf_t):
    mesh = trimesh.creation.extrude_polygon(profile(shelf_t), WIDTH)
    assert mesh.is_watertight
    return mesh


if __name__ == "__main__":
    sizes = [float(a) for a in sys.argv[1:]] or [16.0, 39.0]
    date = datetime.date.today().isoformat()
    for s in sizes:
        name = f"kallax_hook_{s:g}mm_{VERSION}_{date}.stl"
        m = build(s)
        m.export(name)
        print(name, "bbox mm:", np.round(m.extents, 1), "volume cm3:", round(m.volume / 1000, 1))
