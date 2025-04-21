import math
import os

# --- SVG Generation Settings ---
# Updated SVG Template based on user example
SVG_TEMPLATE = """<svg xmlns="http://www.w3.org/2000/svg" id="{svg_id}" width="40" height="40" viewBox="0 0 40 40">
  <desc>{description}</desc>
  <defs>
    <style>
      /* Styles can be kept simple or removed if not strictly needed */
      /* .grid {{ stroke: #cccccc; stroke-width: 0.5; }} */
      /* .road {{ stroke: #000000; stroke-width: 1; fill: none; }} */
      /* .point {{ fill: #ff0000; }} */
    </style>
  </defs>

  <g id="grid" stroke="#cccccc" stroke-width="0.5">
    <line x1="0" y1="10" x2="40" y2="10" /> <line x1="0" y1="20" x2="40" y2="20" /> <line x1="0" y1="30" x2="40" y2="30" />
    <line x1="10" y1="0" x2="10" y2="40" /> <line x1="20" y1="0" x2="20" y2="40" /> <line x1="30" y1="0" x2="30" y2="40" />
    <line x1="0" y1="0" x2="40" y2="0" /> <line x1="0" y1="40" x2="40" y2="40" />
    <line x1="0" y1="0" x2="0" y2="40" /> <line x1="40" y1="0" x2="40" y2="40" />
  </g>

  <g id="road" stroke="#000000" stroke-width="1" fill="none"{transform_attr}>
    <path id="road-outer-{path_type}" d="{path_outer}" />
    <path id="road-inner-{path_type}" d="{path_inner}" />
  </g>

  <g id="anchor-points" fill="#ff0000">
    <circle cx="10" cy="0" r="1" /> <circle cx="20" cy="0" r="1" /> <circle cx="30" cy="0" r="1" />
    <circle cx="40" cy="10" r="1" /> <circle cx="40" cy="20" r="1" /> <circle cx="40" cy="30" r="1" />
    <circle cx="10" cy="40" r="1" /> <circle cx="20" cy="40" r="1" /> <circle cx="30" cy="40" r="1" />
    <circle cx="0" cy="10" r="1" /> <circle cx="0" cy="20" r="1" /> <circle cx="0" cy="30" r="1" />
  </g>
</svg>
"""

# --- Helper Function ---
def get_description(tile_key, tile_type):
    """Generates a description string based on the tile key and type."""
    parts = tile_key.split('-')
    if len(parts) != 2: return f"{tile_type.capitalize()} tile"
    entry_pair, exit_pair = parts[0], parts[1]

    dir_map_full = {'U': 'Upper', 'R': 'Right', 'D': 'Bottom', 'L': 'Left'}
    pair_range_map = {
        'U1U2': '(X:10-20)', 'U2U3': '(X:20-30)',
        'R1R2': '(Y:10-20)', 'R2R3': '(Y:20-30)',
        'D1D2': '(X:10-20)', 'D2D3': '(X:20-30)',
        'L1L2': '(Y:10-20)', 'L2L3': '(Y:20-30)',
    }

    entry_dir = dir_map_full.get(entry_pair[0], 'Unknown')
    exit_dir = dir_map_full.get(exit_pair[0], 'Unknown')
    entry_range = pair_range_map.get(entry_pair, '(Unknown)')
    exit_range = pair_range_map.get(exit_pair, '(Unknown)')

    # Correct direction name for description if needed (e.g., D = Bottom)
    return f"{tile_type.capitalize()} tile: Entry {entry_dir} {entry_range}, Exit {exit_dir} {exit_range}"


# --- Path Definitions (Commas removed from C command parameters) ---

# Base Curve Paths (U->R direction) - Smooth L
curve_paths_base = {
    "U1U2-R1R2": {
        "outer": "M 10 0 L 10 10 C 10 15.5 14.5 20 20 20 L 40 20", # No commas
        "inner": "M 20 0 L 20 5 C 20 7.8 22.2 10 25 10 L 40 10"     # No commas
    },
    "U1U2-R2R3": {
        "outer": "M 10 0 L 10 20 C 10 25.5 14.5 30 20 30 L 40 30", # No commas
        "inner": "M 20 0 L 20 15 C 20 17.8 22.2 20 25 20 L 40 20" # No commas
    },
     "U2U3-R1R2": {
        "outer": "M 20 0 L 20 10 C 20 15.5 24.5 20 30 20 L 40 20", # No commas
        "inner": "M 30 0 L 30 5 C 30 7.8 32.2 10 35 10 L 40 10"     # No commas
    },
    "U2U3-R2R3": {
        "outer": "M 20 0 L 20 20 C 20 25.5 24.5 30 30 30 L 40 30", # No commas
        "inner": "M 30 0 L 30 15 C 30 17.8 32.2 20 35 20 L 40 20" # No commas
    }
}

# Base Sharp Paths (U->R direction) - Right-angled L
sharp_paths_base = {
    "U1U2-R1R2": {"outer": "M 10 0 L 10 20 L 40 20", "inner": "M 20 0 L 20 10 L 40 10"},
    "U1U2-R2R3": {"outer": "M 10 0 L 10 30 L 40 30", "inner": "M 20 0 L 20 20 L 40 20"},
    "U2U3-R1R2": {"outer": "M 20 0 L 20 20 L 40 20", "inner": "M 30 0 L 30 10 L 40 10"},
    "U2U3-R2R3": {"outer": "M 20 0 L 20 30 L 40 30", "inner": "M 30 0 L 30 20 L 40 20"}
}


# Straight Paths (Central Lanes Only, using '23' pairs)
straight_paths = {
    "L2L3-R2R3": {"outer": "M 0 20 L 40 20", "inner": "M 0 30 L 40 30"},
    "R2R3-L2L3": {"outer": "M 40 20 L 0 20", "inner": "M 40 30 L 0 30"},
    "U2U3-D2D3": {"outer": "M 20 0 L 20 40", "inner": "M 30 0 L 30 40"},
    "D2D3-U2U3": {"outer": "M 20 40 L 20 0", "inner": "M 30 40 L 30 0"},
} # 4 types


# --- File Generation ---
output_dir = "road_tiles" # Changed output directory name again
if not os.path.exists(output_dir):
    os.makedirs(output_dir)

generated_files_count = 0

# Mapping for rotated keys
rotated_keys_map = {
    "U1U2-R1R2": ["R1R2-D1D2", "D1D2-L1L2", "L1L2-U1U2"],
    "U1U2-R2R3": ["R1R2-D2D3", "D1D2-L2L3", "L1L2-U2U3"],
    "U2U3-R1R2": ["R2R3-D1D2", "D2D3-L1L2", "L2L3-U1U2"],
    "U2U3-R2R3": ["R2R3-D2D3", "D2D3-L2L3", "L2L3-U2U3"],
}

# Function to generate files for curve or sharp types (using group transform)
def generate_rotated_tiles(base_paths, tile_type):
    global generated_files_count
    for base_key, path_data in base_paths.items():
        # The base path data corresponds to angle 0
        base_outer_path = path_data["outer"]
        base_inner_path = path_data["inner"]

        for i, angle in enumerate([0, 90, 180, 270]):
            # Determine the key for the rotated tile
            if angle == 0:
                tile_key = base_key
            elif base_key in rotated_keys_map and i-1 < len(rotated_keys_map[base_key]):
                 tile_key = rotated_keys_map[base_key][i-1]
            else:
                print(f"Warning: Rotated key mapping not found for {base_key} at {angle} deg.")
                continue

            # Set transform attribute for the <g id="road"> element
            transform_attr = ""
            if angle != 0:
                transform_attr = f' transform="rotate({angle} 20 20)"' # Added space before transform

            filename = f"road-tile-{tile_type}-{tile_key}.svg"
            svg_id = filename.replace(".svg", "") # Use filename without extension as svg id
            description = get_description(tile_key, tile_type)
            filepath = os.path.join(output_dir, filename)

            # Use the base path data; rotation is handled by transform_attr
            svg_content = SVG_TEMPLATE.format(
                svg_id=svg_id,
                description=description,
                transform_attr=transform_attr,
                path_type=tile_type, # 'curve' or 'sharp' for path IDs
                path_outer=base_outer_path,
                path_inner=base_inner_path
            )

            with open(filepath, "w") as f: f.write(svg_content)
            generated_files_count += 1

# Generate Curve Tiles (16 types)
print("Generating curve tiles...")
generate_rotated_tiles(curve_paths_base, "curve")

# Generate Sharp Tiles (16 types)
print("Generating sharp tiles...")
generate_rotated_tiles(sharp_paths_base, "sharp")

# Generate Straight Tiles (Central Lanes Only - 4 types)
print("Generating straight tiles (central lanes only)...")
tile_type = "straight"
for key, path_data in straight_paths.items():
    filename = f"road-tile-{tile_type}-{key}.svg"
    svg_id = filename.replace(".svg", "")
    description = get_description(key, tile_type)
    filepath = os.path.join(output_dir, filename)

    # Straight tiles don't need rotation
    svg_content = SVG_TEMPLATE.format(
        svg_id=svg_id,
        description=description,
        transform_attr="", # No transform for straight tiles
        path_type=tile_type,
        path_outer=path_data["outer"],
        path_inner=path_data["inner"]
    )
    with open(filepath, "w") as f: f.write(svg_content)
    generated_files_count += 1

print(f"\nSuccessfully generated {generated_files_count} SVG files in '{output_dir}' directory.")
# Verification message
if generated_files_count == 36:
    print("Generated 16 curve, 16 sharp, and 4 straight (central lanes only) tiles as expected.")
else:
    print(f"Warning: Expected 36 files (16 curve + 16 sharp + 4 straight), but generated {generated_files_count}.")