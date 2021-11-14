#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""download.py: Download and process dataset about car accidents provided by PČR"""

__author__ = "David Sedlák"
__email__ = "xsedla1d@stud.fit.vutbr.cz"

import csv
import glob
import gzip
import io
import numpy as np
import os
import pickle
import regex as re
import requests
import zipfile
from bs4 import BeautifulSoup


def int_validator(val, ranges=None, invalid_value=-1):
    """Validate and convert integer like value.

    Parameters
    ----------
    val : Int_like
        Value to convert and validate.
    ranges : Iterable, optional
        Iterable containing tuples specifying allowed ranges.
        Ranges are inclusive from both sides so for example tuple
        (4, 8) represents interval <4, 8>. To allow single value,
        tuple (a, a) can be used to allow value a. When not specified,
        range of values is not limited.
    invalid_value : Int, optional
        Value returned when val can't be converted to Int or when it's out
        of specified range.
    Returns
    -------
    Converted and validated value. When value can't be converted or is not valid,
    returns invalid_value.
    """
    try:
        int_val = int(val)
    except ValueError:
        return invalid_value

    if not ranges:
        return int_val

    for (left, right) in ranges:
        if left <= int_val <= right:
            return int_val
    return invalid_value


def float_validator(val, invalid_value=float("NaN")):
    """Convert float like value.

    Parameters
    ----------
    val : float_like
        Value to convert.
    invalid_value : Float, optional
        Value returned when val can't be converted to FP.
    Returns
    -------
    Converted value. When value can't be converted, returns invalid_value.
    """
    try:
        return float(val.replace(',', '.'))
    except ValueError:
        return invalid_value


def date_validator(val, invalid_value=np.datetime64('nat')):
    """Convert date value.

    Parameters
    ----------
    val : date like
        Value to convert.
    invalid_value : datetime64, optional
        Value to use as a fill for invalid entries.
        datetime64('nat') [not a time] from numpy is used as default fill value.

    Returns
    -------
    Converted value. When value can't be converted, returns invalid_value.
    """
    try:
        return np.datetime64(val)
    except ValueError:
        return invalid_value


class DataDownloader:
    """Handle download and processing of accident statistics dataset provided by PČR.

    Attributes
    ----------
    headers List of headers for individual fields in CSV data files.
        Each header is stored as tuple. Where first value is string representing name
        of that header. Second value is numpy data type later used for given fields.
        And third value is lambda expression for conversion and validation of that given
        field, if any.
    regions Dictionary with {region name : CSV_data_file name}

    Methods
    -------
    __init__ Initializer which sets needed instance attributes on instance creation.
    download_data Method to download latest dataset from url specified in initializer.
    parse_region_data Method to parse data for specified region.
    get_dict Method to obtain dataset for specified regions.
    """

    headers = [
        ("p1", "i8", int_validator),
        ("p36", "i1", lambda v: int_validator(v, [(0, 8)])),
        ("p37", "i8", lambda v: 0 if v.strip() == ""
            else int_validator(v, [(0, 99), (101, 999), (1000, 999999)])),
        ("p2a", 'datetime64[D]', date_validator),
        ("weekday(p2a)", "i1", lambda v: int_validator(v, [(0, 6)])),
        # Change format of p2b depending on a future usecase of this field. For now
        # storing it as i2 should preserve all needed data including unknown m/h (60/25)
        ("p2b", "i2", int_validator),
        ("p6", "i1", lambda v: int_validator(v, [(0, 9)])),
        ("p7", "i1", lambda v: int_validator(v, [(0, 4)])),
        ("p8", "i1", lambda v: int_validator(v, [(0, 9)])),
        ("p9", "i1", lambda v: int_validator(v, [(1, 2)])),
        ("p10", "i1", lambda v: int_validator(v, [(0, 7)])),
        ("p11", "i1", lambda v: int_validator(v, [(0, 9)])),
        ("p12", "i2", lambda v: int_validator(v, [(100, 100), (301, 311), (401, 414),
                                                  (501, 516), (601, 615)])),
        ("p13a", "i8", int_validator),
        ("p13b", "i8", int_validator),
        ("p13c", "i8", int_validator),
        ("p14", "i8", int_validator),
        ("p15", "i1", lambda v: int_validator(v, [(1, 6)])),
        ("p16", "i1", lambda v: int_validator(v, [(0, 9)])),
        ("p17", "i1", lambda v: int_validator(v, [(1, 12)])),
        ("p18", "i1", lambda v: int_validator(v, [(0, 7)])),
        ("p19", "i1", lambda v: int_validator(v, [(1, 7)])),
        ("p20", "i1", lambda v: int_validator(v, [(0, 6)])),
        ("p21", "i1", lambda v: int_validator(v, [(0, 6)])),
        ("p22", "i1", lambda v: int_validator(v, [(0, 9)])),
        ("p23", "i1", lambda v: int_validator(v, [(0, 3)])),
        ("p24", "i1", lambda v: 0 if v.strip() == "" else int_validator(v, [(0, 5)])),
        ("p27", "i1", lambda v: int_validator(v, [(0, 10)])),
        ("p28", "i1", lambda v: int_validator(v, [(1, 7)])),
        ("p34", "i8", int_validator),
        ("p35", "i1", lambda v: int_validator(v, [(0, 0), (10, 19), (22, 29)])),
        ("p39", "i1", lambda v: int_validator(v, [(1, 9)])),
        ("p44", "i1", lambda v: int_validator(v, [(0, 18)])),
        ("p45a", "i1",
         lambda v: -2 if v.strip() == "" else int_validator(v, [(0, 99)])),
        ("p47", "i8", lambda v: -2 if v.strip() == "XX" else int_validator(v)),
        ("p48a", "i1",
         lambda v: -2 if v.strip() == "" else int_validator(v, [(0, 18)])),
        ("p49", "i1", lambda v: -2 if v.strip() == "" else int_validator(v, [(0, 1)])),
        ("p50a", "i1", lambda v: -2 if v.strip() == "" else int_validator(v, [(0, 4)])),
        ("p50b", "i1", lambda v: -2 if v.strip() == "" else int_validator(v, [(0, 4)])),
        ("p51", "i1", lambda v: -2 if v.strip() == "" else int_validator(v, [(1, 3)])),
        ("p52", "i1",
         lambda v: -2 if v.strip() == "" else int_validator(v, [(1, 6), (10, 99)])),
        ("p53", "i8", int_validator),
        ("p55a", "i1", lambda v: int_validator(v, [(0, 9)])),
        ("p57", "i1", lambda v: int_validator(v, [(0, 9)])),
        ("p58", "i1", lambda v: int_validator(v, [(0, 5)])),
        ("a", "d", float_validator),
        ("b", "d", float_validator),
        ("d", "d", float_validator),
        ("e", "d", float_validator),
        ("f", "d", float_validator),
        ("g", "d", float_validator),
        ("h", "U", None),
        ("i", "U", None),
        ("j", "U", None),
        ("k", "U", None),
        ("l", "U", None),
        ("n", "i8", lambda v: -2 if v.strip() == "" else int_validator(v)),
        ("o", "U", None),
        ("p", "U", None),
        ("q", "U", None),
        ("r", "i8", lambda v: -2 if v.strip() == "" else int_validator(v)),
        ("s", "i8", lambda v: -2 if v.strip() == "" else int_validator(v)),
        ("t", "U", None),
        ("p5a", "i1", lambda v: int_validator(v, [(0, 1)])),
    ]

    regions = {
        "PHA": "00",
        "STC": "01",
        "JHC": "02",
        "PLK": "03",
        "ULK": "04",
        "HKK": "05",
        "JHM": "06",
        "MSK": "07",
        "OLK": "14",
        "ZLK": "15",
        "VYS": "16",
        "PAK": "17",
        "LBK": "18",
        "KVK": "19",
    }

    def __init__(self, url="https://ehw.fit.vutbr.cz/izv/", folder="data",
                 cache_filename="data_{}.pkl.gz"):
        """Initializer which sets needed instance attributes on instance creation.

        Parameters
        ----------
        url : String, optional
            URL specifying address where dataset can be downloaded.
        folder : String, optional
            Path to folder where temporary data will be stored. Is created when
            it doesn't exist.
        cache_filename : String, optional
            String template specifying name of cache files stored in folder.
            Only *.pkl.gz formats are supported.
        """
        self.url = url
        self.folder = os.path.realpath(os.path.relpath(folder))
        self.cache_filename = os.path.join(self.folder, cache_filename)
        self.mem_cache = {}

    def download_data(self):
        """Method to download latest dataset version."""
        os.makedirs(self.folder, exist_ok=True)
        r = requests.get(self.url)
        page = BeautifulSoup(r.content, features="lxml")
        [x.parent.decompose() for x in page.find_all(string="neexistuje")]
        last_buttons = page.select("td:last-of-type button")
        links = [self.url + re.search("'([^']*)'", button.get('onclick'))[1]
                 for button in last_buttons]
        for link in links:
            file_path = os.path.join(self.folder, link.split('/')[-1])
            if not os.path.isfile(file_path):
                with requests.get(link) as r:
                    with open(file_path, "wb") as f:
                        f.write(r.content)

    def parse_region_data(self, region):
        """Method to parse data for specified region.

        Parameters
        ----------
        region : String
            Shortname of region that should be parsed.

        Returns
        -------
        Dictionary with headers as key and ndarray as value {header : ndarray}
        """
        region_id = self.regions[region]
        result = {header[0]: [] for header in self.headers}
        used_ids = {}

        # Check if we have all available data and download what's missing...
        self.download_data()
        # parse individual columns into lists and check data validity where possible
        for archive in glob.glob(os.path.join(self.folder, "*.zip")):
            with zipfile.ZipFile(archive, "r") as zf:
                with zf.open(region_id + ".csv", "r") as f:
                    reader = csv.reader(io.TextIOWrapper(f, encoding="cp1250"),
                                        delimiter=";", quotechar='"')
                    for row in reader:
                        for header, record in zip(self.headers, row):
                            # handle records with duplicate IDs
                            if header[0] == "p1":
                                if record in used_ids.keys():
                                    break
                                else:
                                    used_ids[record] = 1
                            if header[2]:
                                result[header[0]].append(header[2](record))
                            else:
                                result[header[0]].append(record)

        # create numpy array from lists representing data columns
        for header in self.headers:
            result[header[0]] = np.array(result[header[0]], dtype=header[1])
        # and add region "column"
        result["region"] = np.repeat(region, result[self.headers[0][0]].size)
        return result

    def get_dict(self, regions=None):
        """Method to obtain dataset for specified regions.

        Parsed data of individual regions is cached and parse_region_data is
        used only when desired region is not found in the cache.
        Parameters
        ----------
        regions : Iterable, optional
            Iterable holding shortnames of regions to include in prepared dataset.
            When empty or None, all regions are included.
        Returns
        -------
             Dictionary with headers as key and ndarray as value {header : ndarray}
             Similarly to parse_region_data, but
        """
        regions = regions if regions else self.regions.keys()
        cols = {header[0]: [] for header in self.headers + [("region",)]}
        for region in regions:
            # obtain data
            try:
                # check mem cache
                region_data = self.mem_cache[region]
            except KeyError:
                cache_filename = self.cache_filename.format(region)
                # check file cache
                try:
                    with gzip.open(cache_filename, "rb") as f:
                        region_data = pickle.load(f)
                except FileNotFoundError:
                    # Not found in cache, parse it
                    region_data = self.parse_region_data(region)
                    # store in file cache
                    # I chose compresslevel=8 because from my testing on given dataset
                    # of interest default (level 9) compared to level 8 only compressed
                    # by additional ~0.63 % but took twice as long to compute. I also
                    # tested lower levels, but after level 8 loss on compression was
                    # substantial from my point of view (>2 %) and outweighed the
                    # longer computation time. PS Decompression time deltas were
                    # almost same, so I'm not even mentioning them here...
                    with gzip.open(cache_filename, "wb", compresslevel=8) as f:
                        pickle.dump(region_data, f)
                    #  store in mem cache
                    self.mem_cache[region] = region_data

            for coll_key in cols.keys():
                cols[coll_key].append(region_data[coll_key])
        for coll_key in cols.keys():
            cols[coll_key] = np.concatenate(cols[coll_key])
        return cols


if __name__ == "__main__":
    # Example with PHA, JHM and OLK regions
    example_regions = ["PHA", "JHM", "OLK"]
    example_data = DataDownloader().get_dict(example_regions)
    print("Sloupce:")
    for hdr, col in example_data.items():
        print(" " * 4 + f"{hdr}, počet položek: {len(col)}")
    print(f"Kraje:")
    for reg in np.unique(example_data["region"]):
        print(" " * 4 + f"{reg}")
