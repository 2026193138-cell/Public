import csv
import random
import statistics
import struct
import time
import zlib
from pathlib import Path

from src.hash_table import HashTable
from src.linear_probing_hash_table import LinearProbingHashTable


OUTPUT_DIR = Path(__file__).resolve().parent
CAPACITY = 10000
TARGET_LOAD_FACTORS = tuple(index / 10 for index in range(1, 8)) + (0.75, 0.8, 0.9)
INSERTION_REPEATS = 5
RANDOM_SEED = 20261127
IMPLEMENTATIONS = ("chaining", "linear_probing")
METRICS = (
    "successful_lookup_avg_probes_or_comparisons",
    "unsuccessful_lookup_avg_probes_or_comparisons",
    "insertion_time_ms",
    "insert_collision_count",
)


class FixedCapacityHashTable(HashTable):
    def _resize(self):
        pass


class FixedCapacityLinearProbingHashTable(LinearProbingHashTable):
    def _resize(self):
        pass


FONT = {
    "A": ("010", "101", "111", "101", "101"),
    "B": ("110", "101", "110", "101", "110"),
    "C": ("011", "100", "100", "100", "011"),
    "D": ("110", "101", "101", "101", "110"),
    "E": ("111", "100", "110", "100", "111"),
    "F": ("111", "100", "110", "100", "100"),
    "G": ("011", "100", "101", "101", "011"),
    "H": ("101", "101", "111", "101", "101"),
    "I": ("111", "010", "010", "010", "111"),
    "J": ("001", "001", "001", "101", "010"),
    "K": ("101", "101", "110", "101", "101"),
    "L": ("100", "100", "100", "100", "111"),
    "M": ("101", "111", "111", "101", "101"),
    "N": ("101", "111", "111", "111", "101"),
    "O": ("010", "101", "101", "101", "010"),
    "P": ("110", "101", "110", "100", "100"),
    "Q": ("010", "101", "101", "111", "011"),
    "R": ("110", "101", "110", "101", "101"),
    "S": ("011", "100", "010", "001", "110"),
    "T": ("111", "010", "010", "010", "010"),
    "U": ("101", "101", "101", "101", "111"),
    "V": ("101", "101", "101", "101", "010"),
    "W": ("101", "101", "111", "111", "101"),
    "X": ("101", "101", "010", "101", "101"),
    "Y": ("101", "101", "010", "010", "010"),
    "Z": ("111", "001", "010", "100", "111"),
    "0": ("111", "101", "101", "101", "111"),
    "1": ("010", "110", "010", "010", "111"),
    "2": ("110", "001", "010", "100", "111"),
    "3": ("110", "001", "010", "001", "110"),
    "4": ("101", "101", "111", "001", "001"),
    "5": ("111", "100", "110", "001", "110"),
    "6": ("011", "100", "110", "101", "010"),
    "7": ("111", "001", "010", "010", "010"),
    "8": ("010", "101", "010", "101", "010"),
    "9": ("010", "101", "011", "001", "110"),
    ".": ("000", "000", "000", "000", "010"),
    "-": ("000", "000", "111", "000", "000"),
    "_": ("000", "000", "000", "000", "111"),
}


def make_keys(count, prefix, seed):
    source = random.Random(seed)
    return [f"{prefix}-{source.getrandbits(64):016x}" for _ in range(count)]


def insertion_time(table_type, keys):
    elapsed = 0
    for _ in range(INSERTION_REPEATS):
        table = table_type(capacity=CAPACITY)
        started = time.perf_counter_ns()
        for key in keys:
            table.put(key, key)
        elapsed += time.perf_counter_ns() - started
    return elapsed / INSERTION_REPEATS / 1_000_000


def count_collisions(table, keys, implementation):
    collisions = 0
    for key in keys:
        if implementation == "chaining":
            bucket = table._buckets[table._index(key)]
            collisions += len(bucket)
        else:
            start = table._hash(key) % table.capacity
            for offset in range(table.capacity):
                slot = table._slots[(start + offset) % table.capacity]
                if not isinstance(slot, tuple):
                    break
                collisions += 1
        table.put(key, key)
    return collisions


def chain_lookup_cost(table, key):
    comparisons = 0
    for existing_key, _ in table._buckets[table._index(key)]:
        comparisons += 1
        if existing_key == key:
            return comparisons
    return comparisons


def linear_probe_cost(table, key):
    start = table._hash(key) % table.capacity
    probes = 0
    for offset in range(table.capacity):
        slot = table._slots[(start + offset) % table.capacity]
        probes += 1
        if not isinstance(slot, tuple):
            return probes
        if slot[0] == key:
            return probes
    return probes


def average_lookup_cost(table, keys, cost_function):
    return statistics.mean(cost_function(table, key) for key in keys)


def collect_rows():
    rows = []
    maximum_count = int(CAPACITY * max(TARGET_LOAD_FACTORS))
    all_keys = make_keys(maximum_count, "present", RANDOM_SEED)
    all_missing = make_keys(maximum_count, "absent", RANDOM_SEED + 1)

    for target_factor in TARGET_LOAD_FACTORS:
        item_count = round(CAPACITY * target_factor)
        keys = all_keys[:item_count]
        missing_keys = all_missing[:item_count]
        load_factor = item_count / CAPACITY

        for implementation, table_type, cost_function in (
            ("chaining", FixedCapacityHashTable, chain_lookup_cost),
            ("linear_probing", FixedCapacityLinearProbingHashTable, linear_probe_cost),
        ):
            table = table_type(capacity=CAPACITY)
            collisions = count_collisions(table, keys, implementation)
            values = {
                "successful_lookup_avg_probes_or_comparisons": average_lookup_cost(
                    table, keys, cost_function
                ),
                "unsuccessful_lookup_avg_probes_or_comparisons": average_lookup_cost(
                    table, missing_keys, cost_function
                ),
                "insertion_time_ms": insertion_time(table_type, keys),
                "insert_collision_count": collisions,
            }
            rows.extend(
                {
                    "implementation": implementation,
                    "load_factor": load_factor,
                    "metric": metric,
                    "value": values[metric],
                }
                for metric in METRICS
            )
    return rows


def write_csv(rows):
    path = OUTPUT_DIR / "results.csv"
    with path.open("w", newline="", encoding="utf-8") as output:
        writer = csv.DictWriter(
            output,
            fieldnames=("implementation", "load_factor", "metric", "value"),
        )
        writer.writeheader()
        writer.writerows(rows)
    return path


def set_pixel(pixels, width, height, x, y, color):
    if 0 <= x < width and 0 <= y < height:
        offset = (y * width + x) * 3
        pixels[offset:offset + 3] = bytes(color)


def draw_line(pixels, width, height, x0, y0, x1, y1, color):
    dx = abs(x1 - x0)
    sx = 1 if x0 < x1 else -1
    dy = -abs(y1 - y0)
    sy = 1 if y0 < y1 else -1
    error = dx + dy
    while True:
        set_pixel(pixels, width, height, x0, y0, color)
        if x0 == x1 and y0 == y1:
            break
        doubled_error = 2 * error
        if doubled_error >= dy:
            error += dy
            x0 += sx
        if doubled_error <= dx:
            error += dx
            y0 += sy


def draw_text(pixels, width, height, x, y, text, color, scale=1):
    cursor = x
    for character in text.upper():
        glyph = FONT.get(character)
        if glyph is not None:
            for row, pattern in enumerate(glyph):
                for column, bit in enumerate(pattern):
                    if bit == "1":
                        for vertical in range(scale):
                            for horizontal in range(scale):
                                set_pixel(
                                    pixels,
                                    width,
                                    height,
                                    cursor + column * scale + horizontal,
                                    y + row * scale + vertical,
                                    color,
                                )
        cursor += 4 * scale


def png_chunk(chunk_type, data):
    payload = chunk_type + data
    return struct.pack(">I", len(data)) + payload + struct.pack(
        ">I", zlib.crc32(payload) & 0xFFFFFFFF
    )


def save_png(path, width, height, pixels):
    raw = b"".join(
        b"\x00" + pixels[row * width * 3:(row + 1) * width * 3]
        for row in range(height)
    )
    png = (
        b"\x89PNG\r\n\x1a\n"
        + png_chunk(b"IHDR", struct.pack(">2I5B", width, height, 8, 2, 0, 0, 0))
        + png_chunk(b"IDAT", zlib.compress(raw))
        + png_chunk(b"IEND", b"")
    )
    path.write_bytes(png)


def write_plot(rows, metric):
    width, height = 900, 560
    plot_left, plot_top = 95, 90
    plot_right, plot_bottom = width - 35, height - 90
    plot_width = plot_right - plot_left
    plot_height = plot_bottom - plot_top
    pixels = bytearray([255]) * (width * height * 3)
    black = (25, 25, 25)
    grid = (220, 220, 220)
    colors = {"chaining": (35, 105, 190), "linear_probing": (220, 70, 55)}

    draw_text(pixels, width, height, plot_left, 20, metric.replace("_", " "), black, 2)
    draw_line(pixels, width, height, plot_left, plot_top, plot_left, plot_bottom, black)
    draw_line(pixels, width, height, plot_left, plot_bottom, plot_right, plot_bottom, black)
    draw_text(pixels, width, height, plot_left, height - 35, "LOAD FACTOR", black, 2)
    draw_text(pixels, width, height, 15, plot_top - 18, "VALUE", black, 2)

    grouped = {}
    for row in rows:
        if row["metric"] == metric:
            grouped.setdefault(row["implementation"], []).append(row)
    values = [row["value"] for group in grouped.values() for row in group]
    maximum = max(values, default=1)
    maximum = maximum * 1.08 if maximum else 1
    maximum_load_factor = max(
        row["load_factor"] for group in grouped.values() for row in group
    )

    for tick in range(6):
        y_value = maximum * tick / 5
        y = round(plot_bottom - y_value / maximum * plot_height)
        draw_line(pixels, width, height, plot_left, y, plot_right, y, grid)
        draw_text(pixels, width, height, 40, y - 3, f"{y_value:.1f}", black)

    def point(row):
        x = plot_left + round(row["load_factor"] / maximum_load_factor * plot_width)
        y = plot_bottom - round(row["value"] / maximum * plot_height)
        return x, y

    for implementation in IMPLEMENTATIONS:
        series = sorted(grouped.get(implementation, []), key=lambda row: row["load_factor"])
        color = colors[implementation]
        for previous, current in zip(series, series[1:]):
            draw_line(pixels, width, height, *point(previous), *point(current), color)
        for row in series:
            x, y = point(row)
            for offset_x in range(-3, 4):
                for offset_y in range(-3, 4):
                    if offset_x * offset_x + offset_y * offset_y <= 9:
                        set_pixel(pixels, width, height, x + offset_x, y + offset_y, color)

    for index, (implementation, label) in enumerate(
        (("chaining", "CHAINING"), ("linear_probing", "LINEAR PROBING"))
    ):
        legend_y = 55 + index * 20
        draw_line(pixels, width, height, plot_left + 300, legend_y + 2, plot_left + 325, legend_y + 2, colors[implementation])
        draw_text(pixels, width, height, plot_left + 332, legend_y, label, black)

    for factor in sorted({row["load_factor"] for row in grouped.get("chaining", [])}):
        x = plot_left + round(factor / maximum_load_factor * plot_width)
        draw_line(pixels, width, height, x, plot_bottom, x, plot_bottom + 4, black)
        draw_text(pixels, width, height, x - 12, plot_bottom + 12, f"{factor:.2f}", black)

    path = OUTPUT_DIR / f"comparison_{metric}.png"
    save_png(path, width, height, pixels)
    return path


def main():
    rows = collect_rows()
    csv_path = write_csv(rows)
    plot_paths = [write_plot(rows, metric) for metric in METRICS]

    print(f"CSV: {csv_path}")
    for path in plot_paths:
        print(f"PNG: {path}")
    print("load_factor,implementation,metric,value")
    for row in rows:
        print(
            f"{row['load_factor']:.4f},{row['implementation']},"
            f"{row['metric']},{row['value']:.6f}"
        )


if __name__ == "__main__":
    main()
