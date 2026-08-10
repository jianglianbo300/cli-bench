from collections import defaultdict


def main():
    counts = defaultdict(int)

    with open("data.txt") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            fruit, count = line.split()
            counts[fruit] += int(count)

    for fruit, total in sorted(counts.items(), key=lambda x: x[1], reverse=True):
        print(f"{fruit}={total}")


if __name__ == "__main__":
    main()
