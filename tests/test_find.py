"""Tests for find module.

Module was initially written without tests so I'll attempt to add them for old functions as I go.
"""

from io import BytesIO
import gzip
import pickle
from setupfinder.finder.finder import Finder
from setupfinder import find


def test_save_raw_results():
    test_finder = Finder(None)
    fake_file = BytesIO(bytearray())
    find.save_raw_results(test_finder, fake_file)
    fake_file.seek(0)
    with gzip.open(fake_file, "rb") as f:
        finder_from_file = pickle.load(f)
    assert finder_from_file.setups == test_finder.setups