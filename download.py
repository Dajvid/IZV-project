#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import requests, glob, zipfile, csv, io, os, pickle, gzip
import numpy as np
import regex as re

from bs4 import BeautifulSoup


def int_validator(val, ranges=None, invalid_value=-1):
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


def float_validator(value, invalid_value=float("NaN")):
    try:
        return float(value.replace(',', '.'))
    except ValueError:
        return invalid_value


class DataDownloader:
    """ TODO: dokumentacni retezce

    Attributes:
        headers    Nazvy hlavicek jednotlivych CSV souboru, tyto nazvy nemente!
        regions     Dictionary s nazvy kraju : nazev csv souboru
    """
    # TODO lépe pořešit validátory a zakomponovat do nich rozsahy
    headers = [
        ("p1", "i8", int_validator), # TODO
        ("p36", "i1", lambda v: int_validator(v, [(0, 8)])),
        ("p37", "i8", lambda v: 0 if v.strip() == ""
            else int_validator(v, [(0, 99), (101, 999), (1000, 999999)])),
        ("p2a", np.datetime64, None), # TODO
        ("weekday(p2a)", "i1", lambda v: int_validator(v, [(0, 6)])),
        ("p2b", "U", None),
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
        ("p13c", "i8", int_validator), # TODO uint checks
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
        ("p34", "i8", int_validator), # TODO uint checks
        ("p35", "i1", lambda v: int_validator(v, [(0, 0), (10, 19), (22, 29)])),
        ("p39", "i1", lambda v: int_validator(v, [(1, 9)])),
        ("p44", "i1", lambda v: int_validator(v, [(0, 18)])),
        ("p45a", "i1", lambda v: -2 if v.strip() == "" else int_validator(v, [(0, 99)])),
        ("p47", "i8", lambda v: -2 if v.strip() == "XX" else int_validator(v)),
        ("p48a", "i1", lambda v: -2 if v.strip() == "" else int_validator(v, [(0, 18)])),
        ("p49", "i1", lambda v: -2 if v.strip() == "" else int_validator(v, [(0, 1)])),
        ("p50a", "i1", lambda v: -2 if v.strip() == "" else int_validator(v, [(0, 4)])),
        ("p50b", "i1", lambda v: -2 if v.strip() == "" else int_validator(v, [(0, 4)])),
        ("p51", "i1", lambda v: -2 if v.strip() == "" else int_validator(v, [(1, 3)])),
        ("p52", "i1", lambda v: -2 if v.strip() == "" else int_validator(v, [(1, 6), (10, 99)])),
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

    mem_cache = {}
    # TODO cache path/position
    def __init__(self, url="https://ehw.fit.vutbr.cz/izv/", folder="data",
                 cache_filename="data_{}.pkl.gz"):
        self.url = url
        self.folder = folder
        self.cache_filename = cache_filename
        os.makedirs(folder, exist_ok=True)

    def download_data(self):
        r = requests.get(self.url)
        page = BeautifulSoup(r.content, features="lxml")
        [x.parent.decompose() for x in page.find_all(string="neexistuje")]
        last_buttons = page.select("td:last-of-type button")
        links = [self.url + re.search("'([^']*)'", button.get('onclick'))[1]
                 for button in last_buttons]
        for link in links:
            file_path = self.folder + "/" + link.split('/')[-1]
            if not os.path.isfile(file_path):
                with requests.get(link) as r:
                    with open(file_path, "wb") as f:
                        f.write(r.content)

    def parse_region_data(self, region):
        # todo resolve duplicates
        region_id = self.regions[region]
        result = {header[0] : [] for header in self.headers}

        # TODO make this more elegant
        for _ in range(2):
            for archive in glob.glob(f"{self.folder}/*.zip"):
                    with zipfile.ZipFile(archive, "r") as zf:
                        with zf.open(region_id + ".csv", "r") as f:
                            reader = csv.reader(io.TextIOWrapper(f, encoding="cp1250"),
                                                delimiter=";", quotechar='"')
                            for row in reader:
                                for header, record in zip(self.headers, row):
                                    if header[2]:
                                        result[header[0]].append(header[2](record))
                                    else:
                                        result[header[0]].append(record)
            if len(result[self.headers[0][0]]) > 0:
                break
            else:
                self.download_data()

        for header in self.headers:
            result[header[0]] = np.array(result[header[0]], dtype=header[1])
        result["region"] = np.repeat(region, result[self.headers[0][0]].size)
        return result

    def get_dict(self, regions=None):
        regions = regions if regions else self.regions.keys()
        colls = {header[0] : [] for header in self.headers}
        # TODO add region header more inteligently
        colls["region"] = []
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
                    region_data = self.parse_region_data(region)
                    # store in file cache
                    with gzip.open(cache_filename, "wb") as f:
                        pickle.dump(region_data, f)
                    #  store in mem
                    self.mem_cache[region] = region_data

            for coll_key in colls.keys():
                colls[coll_key].append(region_data[coll_key])
        for coll_key in colls.keys():
            colls[coll_key] = np.concatenate(colls[coll_key])
        return colls


if __name__ == "__main__":
    # TODO výpis základních informací
    a = DataDownloader()
    all_regions = a.get_dict([])
    for (key, value) in all_regions.items():
        print(f"key: {key}, value:{value[0]}")
    print(a.headers[2][2]("101"))
    # print(int_validator("2100200753"))
