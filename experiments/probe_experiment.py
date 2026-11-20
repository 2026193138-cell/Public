import csv
import random
import statistics
import time
from pathlib import Path


OUTPUT_DIR = Path(__file__).resolve().parent
CAPACITY = 4096
LOAD_FACTORS = (0.25, 0.5, 0.75, 1.0, 1.25, 1.5, 2.0, 2.5, 3.0, 4.0)
TRIALS = 30
SAMPLE_KEYS = 2000


def hash_key(key):
    value = 0
    for character in key:
        value = (value * 31 + ord(character)) & 0xFFFFFFFF
    return value


def probe(table, key):
    bucket = table[hash_key(key) % len(table)]
    for index, existing_key in enumerate(bucket, start=1):
        if existing_key == key:
            return index
    return len(bucket) + 1


def run_trial(load_factor, trial):
    random_source = random.Random(20260000 + trial)
    item_count = int(CAPACITY * load_factor)
    table = [[] for _ in range(CAPACITY)]

    inserted = []
    insertion_probes = 0
    for index in range(item_count):
        key = f"present-{trial}-{index}-{random_source.getrandbits(64):016x}"
        bucket = table[hash_key(key) % CAPACITY]
        insertion_probes += len(bucket) + 1
        bucket.append(key)
        inserted.append(key)

    success_probes = 0
    success_sample = random_source.sample(inserted, min(SAMPLE_KEYS, len(inserted)))
    for key in success_sample:
        success_probes += probe(table, key)

    unsuccessful_probes = 0
    for index in range(min(SAMPLE_KEYS, item_count)):
        key = f"absent-{trial}-{index}-{random_source.getrandbits(64):016x}"
        bucket = table[hash_key(key) % CAPACITY]
        unsuccessful_probes += len(bucket)

    return (
        insertion_probes / item_count,
        success_probes / len(success_sample),
        unsuccessful_probes / min(SAMPLE_KEYS, item_count),
    )


def write_csv(rows):
    path = OUTPUT_DIR / "load_factor_results.csv"
    with path.open("w", newline="", encoding="utf-8") as output:
        writer = csv.DictWriter(output, fieldnames=(
            "load_factor",
            "insertion_average_probes",
            "successful_lookup_average_probes",
            "successful_lookup_theoretical",
            "unsuccessful_lookup_average_probes",
            "unsuccessful_lookup_theoretical",
            "trials",
        ))
        writer.writeheader()
        writer.writerows(rows)
    return path


def escape_xml(value):
    return str(value).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def write_svg(rows):
    path = OUTPUT_DIR / "load_factor_performance.svg"
    width, height = 960, 600
    left, right, top, bottom = 85, 35, 45, 70
    plot_width = width - left - right
    plot_height = height - top - bottom

    max_y = max(
        [row["unsuccessful_lookup_average_probes"] for row in rows]
        + [row["unsuccessful_lookup_theoretical"] for row in rows]
        + [row["insertion_average_probes"] for row in rows]
    )
    max_y = max(1.0, (int(max_y) + 1) * 1.0)
    max_x = 4.0

    def x(value):
        return left + value / max_x * plot_width

    def y(value):
        return top + plot_height - value / max_y * plot_height

    series = (
        ("insertion_average_probes", "#1f77b4", "Insertion measured"),
        ("successful_lookup_average_probes", "#2ca02c", "Successful lookup measured"),
        ("successful_lookup_theoretical", "#98df8a", "Successful lookup theoretical"),
        ("unsuccessful_lookup_average_probes", "#d62728", "Unsuccessful lookup measured"),
        ("unsuccessful_lookup_theoretical", "#ff9896", "Unsuccessful lookup theoretical"),
    )

    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        '<rect width="100%" height="100%" fill="white"/>',
        '<style>text{font-family:sans-serif;font-size:12px} .title{font-size:18px;font-weight:bold}</style>',
        '<text x="480" y="24" text-anchor="middle" class="title">Hash Table Performance by Load Factor</text>',
    ]

    for tick in range(0, 5):
        value = tick
        parts.append(f'<line x1="{x(value):.2f}" y1="{top}" x2="{x(value):.2f}" y2="{top + plot_height}" stroke="#dddddd"/>')
        parts.append(f'<text x="{x(value):.2f}" y="{top + plot_height + 22}" text-anchor="middle">{value:.0f}</text>')

    for tick in range(6):
        value = max_y * tick / 5
        parts.append(f'<line x1="{left}" y1="{y(value):.2f}" x2="{left + plot_width}" y2="{y(value):.2f}" stroke="#dddddd"/>')
        parts.append(f'<text x="{left - 10}" y="{y(value) + 4:.2f}" text-anchor="end">{value:.1f}</text>')

    parts.append(f'<rect x="{left}" y="{top}" width="{plot_width}" height="{plot_height}" fill="none" stroke="#555555"/>')
    parts.append(f'<text x="{left + plot_width / 2}" y="{height - 15}" text-anchor="middle">Load factor</text>')
    parts.append(f'<text x="18" y="{top + plot_height / 2}" text-anchor="middle" transform="rotate(-90 18 {top + plot_height / 2})">Average probe count</text>')

    for key, color, label in series:
        points = " ".join(f"{x(row['load_factor']):.2f},{y(row[key]):.2f}" for row in rows)
        parts.append(f'<polyline fill="none" stroke="{color}" stroke-width="2.5" points="{points}"/>')
        for row in rows:
            parts.append(f'<circle cx="{x(row["load_factor"]):.2f}" cy="{y(row[key]):.2f}" r="3" fill="{color}"/>')

    legend_x = left + 20
    legend_y = top + 15
    for index, (_, color, label) in enumerate(series):
        item_y = legend_y + index * 20
        parts.append(f'<line x1="{legend_x}" y1="{item_y}" x2="{legend_x + 24}" y2="{item_y}" stroke="{color}" stroke-width="3"/>')
        parts.append(f'<text x="{legend_x + 30}" y="{item_y + 4}">{escape_xml(label)}</text>')

    parts.append('</svg>')
    path.write_text("\n".join(parts), encoding="utf-8")
    return path


def main():
    rows = []
    started = time.perf_counter()

    for load_factor in LOAD_FACTORS:
        samples = [run_trial(load_factor, trial) for trial in range(TRIALS)]
        insertion = statistics.mean(sample[0] for sample in samples)
        successful = statistics.mean(sample[1] for sample in samples)
        unsuccessful = statistics.mean(sample[2] for sample in samples)
        rows.append({
            "load_factor": load_factor,
            "insertion_average_probes": insertion,
            "successful_lookup_average_probes": successful,
            "successful_lookup_theoretical": 1.0 + load_factor / 2.0,
            "unsuccessful_lookup_average_probes": unsuccessful,
            "unsuccessful_lookup_theoretical": load_factor,
            "trials": TRIALS,
        })

    csv_path = write_csv(rows)
    svg_path = write_svg(rows)
    elapsed = time.perf_counter() - started

    print("Hash table probe experiment")
    print(f"CSV: {csv_path}")
    print(f"SVG: {svg_path}")
    print(f"Elapsed: {elapsed:.3f}s")
    print("load_factor,insertion_avg,success_avg,success_theory,unsuccess_avg,unsuccess_theory")
    for row in rows:
        print(
            f"{row['load_factor']:0.2f},{row['insertion_average_probes']:.3f},"
            f"{row['successful_lookup_average_probes']:.3f},{row['successful_lookup_theoretical']:.3f},"
            f"{row['unsuccessful_lookup_average_probes']:.3f},{row['unsuccessful_lookup_theoretical']:.3f}"
        )


if __name__ == "__main__":
    main()
