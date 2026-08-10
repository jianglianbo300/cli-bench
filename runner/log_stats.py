#!/usr/bin/env python3
"""统计日志文件：总行数、ERROR 行数、INFO 行数。

用法:
    python log_stats.py <log文件路径>
"""
import sys


def main():
    if len(sys.argv) < 2:
        print("用法: python log_stats.py <log文件路径>")
        sys.exit(1)

    log_path = sys.argv[1]
    total = 0
    error_count = 0
    info_count = 0

    with open(log_path, 'r', encoding='utf-8', errors='replace') as f:
        for line in f:
            total += 1
            if '[ERROR]' in line:
                error_count += 1
            elif '[INFO]' in line:
                info_count += 1

    print(f"总行数: {total}")
    print(f"ERROR: {error_count}")
    print(f"INFO: {info_count}")


if __name__ == '__main__':
    main()
