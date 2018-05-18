"""Tests for img module."""

import sys
sys.path.append("..\\src")

import time
from setupfinder import img, fumen, sfinder


def benchmark(trials):
    """Benchmark different image generation functions."""
    test_fumen = "v115@9gwhCeBtDewhQ4CeBti0whR4AeRpilg0whAeQ4AeRp?glMeAgl"

    data = ""
    timer_start = time.perf_counter()
    blocks = img.get_blocks_from_skin("block.png")
    for _ in range(trials):
        data += img.fumen_to_image(test_fumen, 7, blocks)
    total_time = time.perf_counter() - timer_start
    avg_time = total_time / trials
    data_size = len(data) // 1024
    print(
        "fumen_to_image: Trials: %d, Total time: %.2fsec, Avg. Time: %.4fsec, Data size: %dkB"
        % (trials, total_time, avg_time, data_size))

    data = ""
    timer_start = time.perf_counter()
    sf = sfinder.SFinder(
        "C:\\Users\\metazilla\\code\\setup-finder\\solution-finder-0.511")
    for _ in range(trials):
        data += sf.fig_png(test_fumen, "7")
    total_time = time.perf_counter() - timer_start
    avg_time = total_time / trials
    data_size = len(data) // 1024
    print(
        "sf.fig_png: Trials: %d, Total time: %.2fsec, Avg. Time: %.4fsec, Data size: %dkB"
        % (trials, total_time, avg_time, data_size))


def main():
    """Run benchmarks for img module."""
    benchmark(100)


if __name__ == '__main__':
    main()
