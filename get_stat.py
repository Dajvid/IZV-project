#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.colors import LogNorm, Normalize

import argparse

from download import DataDownloader


def plot_stat(data_source,
              fig_location=None,
              show_figure=False):
    ylabels = [
        "Přerušovaná žlutá",
        "Semafor mimo provoz",
        "Dopravní značky",
        "Přenosné dopravní značky",
        "Nevyznačena",
        "Žádná úprava",
    ]
    regions, starting_indexes, regions_counts = np.unique(data_source["region"],
                                                          return_index=True,
                                                          return_counts=True)
    abs_matrix = np.zeros((6, len(regions)))
    # TODO handle invalid values

    for i in range(len(regions)):
        region_slice = data_source["p24"][starting_indexes[i]: starting_indexes[i] +
                                                               regions_counts[i]]
        accidents_values, accidents_counts = np.unique(region_slice, return_counts=True)
        abs_matrix[accidents_values, i] = accidents_counts
    abs_matrix = np.roll(abs_matrix, -1, axis=0)

    # Absolute plot
    fig = plt.figure(figsize=(8, 6), dpi=100)
    ax = plt.imshow(np.ma.masked_where(abs_matrix == 0, abs_matrix),
                          cmap="viridis",
                          norm=LogNorm(vmax=10 ** np.ceil(np.log10(abs_matrix.max())))
                          )
    plt.title("Absolutně")
    plt.xticks(range(len(regions)), regions)
    plt.yticks(range(6), ylabels)
    plt.colorbar(ax)
    if show_figure:
        plt.show()

    # Relative plot
    sums = np.sum(abs_matrix, axis=1)
    rel_matrix = (abs_matrix.T / sums).T * 100
    rel_plot = plt.imshow(np.ma.masked_where(rel_matrix == 0, rel_matrix),
                          cmap="viridis")
    plt.title("Relativně vůči příčině")
    plt.xticks(range(len(regions)), regions)
    plt.yticks(range(6), ylabels)
    plt.colorbar(rel_plot)
    if show_figure:
        plt.show()


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--fig_location",
        default=None,
        help="Defines location of resulting plots."
    )
    parser.add_argument(
        "--show_figure",
        action="store_true",
        help="Show the plot when it's created."
    )
    args = parser.parse_args(argv)
    plot_stat(DataDownloader().get_dict(), args.fig_location, args.show_figure)


if __name__ == "__main__":
    main()
