"""
Road‑tile SVG generator — <Type>-<mask8bit> 命名版  (clean bit layout)
=================================================

* ファイル名規則:  `road-tile-<Type>-<mask8bit>.svg`
    * `<Type>`  … `curve` / `sharp` / `straight`
    * `<mask8bit>` … 新レーン配置に基づく 8 ビット値（16 進 2 桁）
* **重複する straight マスク** は形状が同一（パスを逆に描くだけ）なので
    2 枚だけ出力 (= 合計 34 枚)。

**ビット再定義 (鏡映レイアウト)  — 0 = N0, … 7 = W0**

    bit: 0  1  2  3  4  5  6  7
    port U1U2 U2U3 R1R2 R2R3 D2D3 D1D2 L2L3 L1L2
          N0  N1  E0  E1  S1  S0  W1  W0
"""

import os
from typing import Dict, Set

# ------------------------------------------------------------
# 1.  Port pair → bit index  (new clean layout)
# ------------------------------------------------------------
PAIR_TO_BIT: Dict[str, int] = {
    "U1U2": 0, "U2U3": 1,  # North side (left / right)
    "R1R2": 2, "R2R3": 3,  # East  side (top  / bottom)
    "D2D3": 4, "D1D2": 5,  # South side (**mirrored**)  right/left
    "L2L3": 6, "L1L2": 7,  # West  side (**mirrored**)  top/bottom
}


def key_to_mask(key: str) -> int:
    """Convert a tile‑key like 'U1U2-R1R2' into an 8‑bit mask."""
    mask = 0
    for pair in key.split("-"):
        try:
            mask |= 1 << PAIR_TO_BIT[pair]
        except KeyError as e:
            raise ValueError(f"Unknown port pair '{pair}'") from e
    return mask

# ------------------------------------------------------------
# 2.  SVG template (grid + road paths) — identical for all tiles
# ------------------------------------------------------------
SVG_TMPL = """<svg xmlns=\"http://www.w3.org/2000/svg\" id=\"{svg_id}\" width=\"40\" height=\"40\" viewBox=\"0 0 40 40\">\n  <desc>{desc}</desc>\n  <g stroke=\"#ccc\" stroke-width=\"0.5\">\n    <line x1=\"10\" y1=\"0\" x2=\"10\" y2=\"40\"/><line x1=\"20\" y1=\"0\" x2=\"20\" y2=\"40\"/><line x1=\"30\" y1=\"0\" x2=\"30\" y2=\"40\"/>\n    <line x1=\"0\" y1=\"10\" x2=\"40\" y2=\"10\"/><line x1=\"0\" y1=\"20\" x2=\"40\" y2=\"20\"/><line x1=\"0\" y1=\"30\" x2=\"40\" y2=\"30\"/>\n    <rect x=\"0\" y=\"0\" width=\"40\" height=\"40\" fill=\"none\"/>\n  </g>\n  <g stroke=\"#000\" stroke-width=\"1\" fill=\"none\"{transform}>\n    <path d=\"{outer}\" />\n    <path d=\"{inner}\" />\n  </g>\n</svg>"""

# ------------------------------------------------------------
# 3.  Path dictionaries (geometryは元スクリプトからコピー)
# ------------------------------------------------------------
curve_paths_base = {
    "U1U2-R1R2": {
        "outer": "M 10 0 L 10 10 C 10 15.5 14.5 20 20 20 L 40 20",
        "inner": "M 20 0 L 20 5 C 20 7.8 22.2 10 25 10 L 40 10",
    },
    "U1U2-R2R3": {
        "outer": "M 10 0 L 10 20 C 10 25.5 14.5 30 20 30 L 40 30",
        "inner": "M 20 0 L 20 15 C 20 17.8 22.2 20 25 20 L 40 20",
    },
    "U2U3-R1R2": {
        "outer": "M 20 0 L 20 10 C 20 15.5 24.5 20 30 20 L 40 20",
        "inner": "M 30 0 L 30 5 C 30 7.8 32.2 10 35 10 L 40 10",
    },
    "U2U3-R2R3": {
        "outer": "M 20 0 L 20 20 C 20 25.5 24.5 30 30 30 L 40 30",
        "inner": "M 30 0 L 30 15 C 30 17.8 32.2 20 35 20 L 40 20",
    },
}

sharp_paths_base = {
    "U1U2-R1R2": {
        "outer": "M 10 0 L 10 20 L 40 20",
        "inner": "M 20 0 L 20 10 L 40 10",
    },
    "U1U2-R2R3": {
        "outer": "M 10 0 L 10 30 L 40 30",
        "inner": "M 20 0 L 20 20 L 40 20",
    },
    "U2U3-R1R2": {
        "outer": "M 20 0 L 20 20 L 40 20",
        "inner": "M 30 0 L 30 10 L 40 10",
    },
    "U2U3-R2R3": {
        "outer": "M 20 0 L 20 30 L 40 30",
        "inner": "M 30 0 L 30 20 L 40 20",
    },
}

straight_paths = {
    "L2L3-R2R3": {
        "outer": "M 0 20 L 40 20",
        "inner": "M 0 30 L 40 30",
    },
    "R2R3-L2L3": {
        "outer": "M 40 20 L 0 20",
        "inner": "M 40 30 L 0 30",
    },
    "U2U3-D2D3": {
        "outer": "M 20 0 L 20 40",
        "inner": "M 30 0 L 30 40",
    },
    "D2D3-U2U3": {
        "outer": "M 20 40 L 20 0",
        "inner": "M 30 40 L 30 0",
    },
}

# ------------------------------------------------------------
# 4.  Rotation mapping (90° steps)
# ------------------------------------------------------------
# キー名は旧来と変わらないため、この dict はそのまま使える。
ROT_KEYS = {
    "U1U2-R1R2": ["R1R2-D1D2", "D1D2-L1L2", "L1L2-U1U2"],
    "U1U2-R2R3": ["R1R2-D2D3", "D1D2-L2L3", "L1L2-U2U3"],
    "U2U3-R1R2": ["R2R3-D1D2", "D2D3-L1L2", "L2L3-U1U2"],
    "U2U3-R2R3": ["R2R3-D2D3", "D2D3-L2L3", "L2L3-U2U3"],
}

# ------------------------------------------------------------
# 5.  Output settings
# ------------------------------------------------------------
OUT_DIR = "road_tiles_8bit"
os.makedirs(OUT_DIR, exist_ok=True)

# ------------------------------------------------------------
# 6.  Core generation helpers
# ------------------------------------------------------------

def write_svg(fname: str, desc: str, outer: str, inner: str, transform: str = ""):
    svg_txt = SVG_TMPL.format(svg_id=fname[:-4], desc=desc, transform=transform, outer=outer, inner=inner)
    with open(os.path.join(OUT_DIR, fname), "w", encoding="utf-8") as fp:
        fp.write(svg_txt)

# ------------------------------------------------------------
# 7.  Generate L‑curve tiles (curve / sharp) 4 rotations each
# ------------------------------------------------------------

def gen_rot_tiles(base_dict: Dict[str, Dict[str, str]], tile_type: str):
    used_masks: Set[int] = set()
    for base_key, paths in base_dict.items():
        for idx, angle in enumerate((0, 90, 180, 270)):
            key = base_key if angle == 0 else ROT_KEYS[base_key][idx - 1]
            mask = key_to_mask(key)
            fname = f"road-tile-{tile_type}-{mask:02X}.svg"
            if mask in used_masks:
                # 直線などの重複防止
                continue
            used_masks.add(mask)
            write_svg(
                fname,
                f"{tile_type} tile, key={key}, mask=0x{mask:02X}",
                paths["outer"],
                paths["inner"],
                "" if angle == 0 else f' transform=\"rotate({angle} 20 20)\"',
            )

# ------------------------------------------------------------
# 8.  Run generation
# ------------------------------------------------------------
if __name__ == "__main__":
    print("Generating curve tiles …")
    gen_rot_tiles(curve_paths_base, "curve")

    print("Generating sharp tiles …")
    gen_rot_tiles(sharp_paths_base, "sharp")

    print("Generating straight tiles …")
    used_masks: Set[int] = set()
    for key, paths in straight_paths.items():
        mask = key_to_mask(key)
        fname = f"road-tile-straight-{mask:02X}.svg"
        if mask in used_masks:
            continue  # duplicate geometry (reverse path)
        used_masks.add(mask)
        write_svg(fname, f"straight tile, key={key}, mask=0x{mask:02X}", paths["outer"], paths["inner"])

    print("Done. SVG files are in:", OUT_DIR)
