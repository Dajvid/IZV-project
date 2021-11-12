#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import requests, glob, zipfile, csv, io, os, pickle, gzip
import numpy as np
import regex as re

from bs4 import BeautifulSoup


def int_validator(value, invalid_value=-1):
    try:
        return int(value)
    except ValueError:
        return invalid_value


def float_validator(value, invalid_value=float("NaN")):
    try:
        return float(value)
    except ValueError:
        return invalid_value


def string_validator(value):
    return str(value.encode("utf-8"))


class DataDownloader:
    """ TODO: dokumentacni retezce

    Attributes:
        headers    Nazvy hlavicek jednotlivych CSV souboru, tyto nazvy nemente!
        regions     Dictionary s nazvy kraju : nazev csv souboru
    """

    # TODO lépe pořešit validátory a zakomponovat do nich rozsahy
    headers = [
        ("p1", np.int64, int_validator),
        ("p36", np.int8, int_validator),
        ("p37", np.int64, int_validator),
        ("p2a", np.datetime64, None),
        ("weekday(p2a)", np.int8, int_validator),
        ("p2b", np.string_, string_validator),
        ("p6", np.int8, int_validator),
        ("p7", np.int8, int_validator),
        ("p8", np.int8, int_validator),
        ("p9", np.int8, int_validator),
        ("p10", np.int8, int_validator),
        ("p11", np.int8, int_validator),
        ("p12", np.int16, int_validator),
        ("p13a", np.int64, int_validator),
        ("p13b", np.int64, int_validator),
        ("p13c", np.int64, int_validator),
        ("p14", np.int64, int_validator),
        ("p15", np.int8, int_validator),
        ("p16", np.int8, int_validator),
        ("p17", np.int8, int_validator),
        ("p18", np.int8, int_validator),
        ("p19", np.int8, int_validator),
        ("p20", np.int8, int_validator),
        ("p21", np.int8, int_validator),
        ("p22", np.int8, int_validator),
        ("p23", np.int8, int_validator),
        ("p24", np.int8, int_validator),
        ("p27", np.int8, int_validator),
        ("p28", np.int8, int_validator),
        ("p34", np.int64, int_validator),
        ("p35", np.int8, int_validator),
        ("p39", np.int8, int_validator),
        ("p44", np.int8, int_validator),
        ("p45a", np.int8, int_validator),
        ("p47", np.int64, int_validator),
        ("p48a", np.int8, int_validator),
        ("p49", np.int8, int_validator),
        ("p50a", np.int8, int_validator),
        ("p50b", np.int8, int_validator),
        ("p51", np.int8, int_validator),
        ("p52", np.int8, int_validator),
        ("p53", np.int64, int_validator),
        ("p55a", np.int8, int_validator),
        ("p57", np.int8, int_validator),
        ("p58", np.int8, int_validator),
        ("a", np.double, float_validator),
        ("b", np.double, float_validator),
        ("d", np.double, float_validator),
        ("e", np.double, float_validator),
        ("f", np.double, float_validator),
        ("g", np.double, float_validator),
        ("h", np.string_, string_validator),
        ("i", np.string_, string_validator),
        ("j", np.object_, None),
        ("k", np.string_, string_validator),
        ("l", np.string_, string_validator),
        ("n", np.int64, int_validator),
        ("o", np.object_, None),
        ("p", np.string_, string_validator),
        ("q", np.string_, string_validator),
        ("r", np.int64, int_validator),
        ("s", np.int64, int_validator),
        ("t", np.string_, string_validator),
        ("p5a", np.int8, int_validator)
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

    def __init__(self, url="https://ehw.fit.vutbr.cz/izv/", folder="data",
                 cache_filename="data_{}.pkl.gz"):
        self.url = url
        self.folder = folder
        self.cache_filename = cache_filename
        try:
            os.makedirs(folder)
        except FileExistsError:
            pass

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
            if result[self.headers[0][0]].size > 0:
                break
            else:
                self.download_data()

        for header in self.headers:
            result[header[0]] = np.array(result[header[0]], dtype=header[1])
        result["region"] = np.repeat(region, result[self.headers[0][0]].size)
        return result

    def get_dict(self, regions=None):
        regions = regions if regions else self.regions
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
    all_regions = a.get_dict(["KVK"])
    for (key, value) in all_regions.items():
        print(f"{key} : {value.shape}")
