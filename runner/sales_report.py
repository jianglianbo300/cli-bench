import csv
import sys
from collections import defaultdict


def build_report(csv_path):
    totals = defaultdict(float)
    with open(csv_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            region = row["region"]
            amount = float(row["amount"])
            totals[region] += amount
    return sorted(totals.items(), key=lambda item: item[1], reverse=True)


def main():
    if len(sys.argv) != 2:
        print("Usage: python sales_report.py <csv_path>")
        sys.exit(1)
    rows = build_report(sys.argv[1])
    for region, total in rows:
        print(f"{region}: {total:.2f}")


if __name__ == "__main__":
    main()
