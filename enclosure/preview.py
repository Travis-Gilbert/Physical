"""Render an STL to PNG with correct occlusion.

matplotlib's Poly3DCollection has no depth buffer, so a solid with holes in it
renders inside-out. This is a small orthographic z-buffer rasterizer instead:
backface cull, barycentric fill, per-face lambert shading. Slow, exact, and
dependency-light.
"""

from __future__ import annotations

import numpy as np
import trimesh


def _basis(elev_deg: float, azim_deg: float) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    e, a = np.radians(elev_deg), np.radians(azim_deg)
    fwd = np.array(
        [np.cos(e) * np.cos(a), np.cos(e) * np.sin(a), np.sin(e)], dtype=float
    )
    fwd /= np.linalg.norm(fwd)
    world_up = np.array([0.0, 0.0, 1.0])
    if abs(fwd @ world_up) > 0.999:
        world_up = np.array([0.0, 1.0, 0.0])
    right = np.cross(world_up, fwd)
    right /= np.linalg.norm(right)
    up = np.cross(fwd, right)
    return right, up, fwd


def render(
    mesh: trimesh.Trimesh,
    elev: float,
    azim: float,
    width: int = 900,
    height: int = 620,
    margin: float = 1.10,
    base=(0.80, 0.81, 0.84),
    bg=(1.0, 1.0, 1.0),
) -> np.ndarray:
    """Orthographic render. Camera sits along (elev, azim) looking at centroid."""
    right, up, fwd = _basis(elev, azim)
    verts = mesh.vertices - mesh.centroid

    # Camera space: u across, v up, w toward viewer (larger = nearer).
    # `fwd` points from the origin toward the camera, so a vertex's projection
    # onto it IS its nearness. Negating here (and in the cull below) silently
    # renders the antipodal viewpoint: ask for a plan view, get the underside.
    u = verts @ right
    v = verts @ up
    w = verts @ fwd

    # Fit both axes independently, then take the tighter scale. Using
    # min(width, height) squashed wide elevations into a fraction of the canvas.
    span_u = (u.max() - u.min()) * margin
    span_v = (v.max() - v.min()) * margin
    cx, cy = (u.max() + u.min()) / 2, (v.max() + v.min()) / 2
    scale = min(width / span_u, height / span_v)

    px = (u - cx) * scale + width / 2
    py = height / 2 - (v - cy) * scale

    tri = mesh.faces
    normals = mesh.face_normals

    # Backface cull: keep faces whose normal points toward the camera.
    facing = normals @ fwd
    keep = facing > 0.0
    tri, normals, facing = tri[keep], normals[keep], facing[keep]

    light = np.array([0.35, -0.75, 0.56])
    light /= np.linalg.norm(light)
    lam = np.clip(normals @ light, 0.0, 1.0)
    shade = 0.30 + 0.62 * lam + 0.08 * facing

    # Depth cue. Without it, an interior surface seen through an opening shades
    # identically to the near wall and the opening becomes invisible — which is
    # exactly how a correctly-cut bay bank can look like solid metal.
    face_w = w[tri].mean(axis=1)
    lo, hi = face_w.min(), face_w.max()
    depth = (face_w - lo) / max(hi - lo, 1e-9)
    shade = shade * (0.42 + 0.58 * depth)

    img = np.ones((height, width, 3), dtype=float) * np.array(bg)
    zbuf = np.full((height, width), -np.inf)

    ax_, ay_ = px[tri[:, 0]], py[tri[:, 0]]
    bx_, by_ = px[tri[:, 1]], py[tri[:, 1]]
    cx_, cy_ = px[tri[:, 2]], py[tri[:, 2]]
    aw, bw, cw = w[tri[:, 0]], w[tri[:, 1]], w[tri[:, 2]]

    for i in range(len(tri)):
        x0 = max(int(np.floor(min(ax_[i], bx_[i], cx_[i]))), 0)
        x1 = min(int(np.ceil(max(ax_[i], bx_[i], cx_[i]))) + 1, width)
        y0 = max(int(np.floor(min(ay_[i], by_[i], cy_[i]))), 0)
        y1 = min(int(np.ceil(max(ay_[i], by_[i], cy_[i]))) + 1, height)
        if x1 <= x0 or y1 <= y0:
            continue

        xs = np.arange(x0, x1) + 0.5
        ys = np.arange(y0, y1) + 0.5
        gx, gy = np.meshgrid(xs, ys)

        d = (by_[i] - cy_[i]) * (ax_[i] - cx_[i]) + (cx_[i] - bx_[i]) * (ay_[i] - cy_[i])
        if abs(d) < 1e-12:
            continue
        l1 = ((by_[i] - cy_[i]) * (gx - cx_[i]) + (cx_[i] - bx_[i]) * (gy - cy_[i])) / d
        l2 = ((cy_[i] - ay_[i]) * (gx - cx_[i]) + (ax_[i] - cx_[i]) * (gy - cy_[i])) / d
        l3 = 1.0 - l1 - l2

        inside = (l1 >= -1e-6) & (l2 >= -1e-6) & (l3 >= -1e-6)
        if not inside.any():
            continue

        z = l1 * aw[i] + l2 * bw[i] + l3 * cw[i]
        sub_z = zbuf[y0:y1, x0:x1]
        win = inside & (z > sub_z)
        if not win.any():
            continue
        sub_z[win] = z[win]
        img[y0:y1, x0:x1][win] = np.array(base) * shade[i]

    return np.clip(img, 0, 1)
