"""
Marker Tile SVG Generator - スタートとゴールのタイル用 (ポート指定対応版)
=================================================

* スタートタイル: デフォルトは右方向(E0)接続、マスク = 0x04
* ゴールタイル: デフォルトは左方向(W0)接続、マスク = 0x80

ビット定義 (8-bit mask):
    bit: 0  1  2  3  4  5  6  7
    port U1U2 U2U3 R1R2 R2R3 D2D3 D1D2 L2L3 L1L2
          N0  N1  E0  E1  S1  S0  W1  W0

ポート名称:
    N0: 上向き左側, N1: 上向き右側
    E0: 右向き上側, E1: 右向き下側
    S1: 下向き右側, S0: 下向き左側
    W1: 左向き下側, W0: 左向き上側
"""

import os
from typing import Dict, Tuple, List

# ------------------------------------------------------------
# 1. ポート定義とマスク計算
# ------------------------------------------------------------
# ポート名とビット位置のマッピング
PORT_TO_BIT = {
    "N0": 0, "N1": 1,
    "E0": 2, "E1": 3,
    "S1": 4, "S0": 5,
    "W1": 6, "W0": 7,
}

# ポート名とマスク値のマッピング
PORT_TO_MASK = {port: (1 << bit) for port, bit in PORT_TO_BIT.items()}

# 各ポートの接続線の座標定義 (各ポートごとに2本の線)
# 形式: [(line1_start_x, line1_start_y, line1_end_x, line1_end_y), 
#        (line2_start_x, line2_start_y, line2_end_x, line2_end_y)]
PORT_TO_LINES = {
    # 上方向への接続
    "N0": [(10, 0, 10, 10), (20, 0, 20, 10)],  # 上向き左側
    "N1": [(20, 0, 20, 10), (30, 0, 30, 10)],  # 上向き右側
    
    # 右方向への接続
    "E0": [(30, 10, 40, 10), (30, 20, 40, 20)],  # 右向き上側
    "E1": [(30, 20, 40, 20), (30, 30, 40, 30)],  # 右向き下側
    
    # 下方向への接続
    "S1": [(20, 30, 20, 40), (30, 30, 30, 40)],  # 下向き右側
    "S0": [(10, 30, 10, 40), (20, 30, 20, 40)],  # 下向き左側
    
    # 左方向への接続
    "W1": [(0, 20, 10, 20), (0, 30, 10, 30)],  # 左向き下側
    "W0": [(0, 10, 10, 10), (0, 20, 10, 20)],  # 左向き上側
}

# ------------------------------------------------------------
# 2. 出力ディレクトリ設定
# ------------------------------------------------------------
OUT_DIR = "marker_tiles"
os.makedirs(OUT_DIR, exist_ok=True)

# ------------------------------------------------------------
# 3. SVGテンプレート（グリッド線）
# ------------------------------------------------------------
SVG_BASE_TMPL = """<svg xmlns="http://www.w3.org/2000/svg" id="{svg_id}" width="40" height="40" viewBox="0 0 40 40">
  <desc>{desc}</desc>
  <g stroke="#ccc" stroke-width="0.5">
    <line x1="10" y1="0" x2="10" y2="40"/><line x1="20" y1="0" x2="20" y2="40"/><line x1="30" y1="0" x2="30" y2="40"/>
    <line x1="0" y1="10" x2="40" y2="10"/><line x1="0" y1="20" x2="40" y2="20"/><line x1="0" y1="30" x2="40" y2="30"/>
    <rect x="0" y="0" width="40" height="40" fill="none"/>
  </g>
{port_lines}
{content}
</svg>"""

# ------------------------------------------------------------
# 4. スタート・ゴールタイル用のコンテンツ（装飾部分）
# ------------------------------------------------------------
START_CONTENT = """  <!-- スタートフラッグと装飾 -->
  <g>
    <!-- フラッグポール -->
    <rect x="10" y="5" width="1.5" height="20" fill="#555" />
    <!-- フラッグ -->
    <path d="M 11.5 5 v 10 L 18 10 z" fill="#3498db" />
    <!-- 「START」テキスト -->
    <g transform="translate(5, 32)">
      <rect x="0" y="-7" width="30" height="10" rx="2" fill="#3498db" fill-opacity="0.2" />
      <text x="15" y="0" font-family="Arial, sans-serif" font-size="6" text-anchor="middle" font-weight="bold" fill="#3498db">START</text>
    </g>
  </g>"""

GOAL_CONTENT = """  <!-- チェッカーフラッグと装飾 -->
  <g>
    <!-- 「GOAL」テキスト -->
    <g transform="translate(5, 32)">
      <rect x="0" y="-7" width="30" height="10" rx="2" fill="#e74c3c" fill-opacity="0.2" />
      <text x="15" y="0" font-family="Arial, sans-serif" font-size="6" text-anchor="middle" font-weight="bold" fill="#e74c3c">GOAL</text>
    </g>
    <!-- ターゲットマーク -->
    <g transform="translate(20, 15)">
      <circle cx="0" cy="0" r="6" fill="none" stroke="#e74c3c" stroke-width="1" />
      <circle cx="0" cy="0" r="3" fill="none" stroke="#e74c3c" stroke-width="1" />
      <circle cx="0" cy="0" r="1" fill="#e74c3c" />
    </g>
  </g>"""

# ------------------------------------------------------------
# 5. ポート線の生成関数
# ------------------------------------------------------------
def generate_port_lines(ports: List[str]) -> str:
    """指定されたポートに対応する接続線のSVGを生成する"""
    if not ports:
        return ""
    
    lines = []
    lines.append("  <!-- ポート接続（黒線） -->")
    lines.append('  <g stroke="#000" stroke-width="1" fill="none">')
    
    for port in ports:
        if port in PORT_TO_LINES:
            for line in PORT_TO_LINES[port]:
                x1, y1, x2, y2 = line
                lines.append(f'    <path d="M {x1} {y1} L {x2} {y2}" />')
    
    lines.append("  </g>")
    return "\n".join(lines)

# ------------------------------------------------------------
# 6. SVG生成関数
# ------------------------------------------------------------
def write_marker_svg(filename: str, desc: str, ports: List[str], content: str):
    """マーカータイル用のSVGファイルを生成する"""
    svg_id = filename[:-4]  # .svgを除く
    port_lines = generate_port_lines(ports)
    
    svg_content = SVG_BASE_TMPL.format(
        svg_id=svg_id, 
        desc=desc, 
        port_lines=port_lines,
        content=content
    )
    
    with open(os.path.join(OUT_DIR, filename), "w", encoding="utf-8") as fp:
        fp.write(svg_content)

# ------------------------------------------------------------
# 7. マスク値計算関数
# ------------------------------------------------------------
def calculate_mask(ports: List[str]) -> int:
    """ポートリストからマスク値を計算する"""
    mask = 0
    for port in ports:
        if port in PORT_TO_MASK:
            mask |= PORT_TO_MASK[port]
    return mask

# ------------------------------------------------------------
# 8. メイン生成関数
# ------------------------------------------------------------
def generate_marker_tile(tile_type: str, ports: List[str]):
    """指定されたタイプとポートでマーカータイルを生成する"""
    mask = calculate_mask(ports)
    port_str = "_".join(ports) if ports else "none"
    
    if tile_type == "start":
        filename = f"road-tile-marker-start-{mask:02X}.svg"
        desc = f"Start marker tile, ports=[{','.join(ports)}], mask=0x{mask:02X}"
        content = START_CONTENT
    else:  # goal
        filename = f"road-tile-marker-goal-{mask:02X}.svg"
        desc = f"Goal marker tile, ports=[{','.join(ports)}], mask=0x{mask:02X}"
        content = GOAL_CONTENT
    
    write_marker_svg(filename, desc, ports, content)
    print(f"生成: {filename} (ポート: {port_str}, マスク: 0x{mask:02X})")
    return filename

# ------------------------------------------------------------
# 9. メイン処理
# ------------------------------------------------------------
def generate_marker_tiles(start_port: str = "E0", goal_port: str = "W0"):
    """スタートとゴールのマーカータイルを生成する
    
    Args:
        start_port: スタートタイルの接続ポート (デフォルト: E0)
        goal_port: ゴールタイルの接続ポート (デフォルト: W0)
    """
    # 指定されたポートが有効か確認
    if start_port not in PORT_TO_MASK:
        print(f"警告: 無効なスタートポート '{start_port}' が指定されました。デフォルトの 'E0' を使用します。")
        start_port = "E0"
        
    if goal_port not in PORT_TO_MASK:
        print(f"警告: 無効なゴールポート '{goal_port}' が指定されました。デフォルトの 'W0' を使用します。")
        goal_port = "W0"
    
    # スタートタイル生成
    start_file = generate_marker_tile("start", [start_port])
    
    # ゴールタイル生成
    goal_file = generate_marker_tile("goal", [goal_port])
    
    print(f"マーカータイル生成完了。ファイルは {OUT_DIR} ディレクトリに保存されました。")
    return start_file, goal_file

# ------------------------------------------------------------
# 10. コマンドライン実行用
# ------------------------------------------------------------
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='スタートとゴールのマーカータイルを生成します。')
    parser.add_argument('--start', default='E0', help='スタートタイルの接続ポート (デフォルト: E0)')
    parser.add_argument('--goal', default='W0', help='ゴールタイルの接続ポート (デフォルト: W0)')
    
    args = parser.parse_args()
    
    generate_marker_tiles(args.start, args.goal)