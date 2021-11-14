#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import argparse
import os
import matplotlib.pyplot as plt
import numpy as np

from matplotlib.colors import LogNorm
from download import DataDownloader


def plot_stat(data_source, fig_location=None, show_figure=False):
    """Plot statistics of absolute and relative accidents and causes across regions.

    Parameters
    ----------
    data_source : Dictionary with data in format produced by DataDownloader.get_dict
    fig_location : String, optional
        Path to store resulting plot, including filename and format extension.
        If not specified, figure is not saved.
    show_figure : Bool, optional
        When set to True, resulting figure is also shown on the screen. If not
        specified default value is False, and hence figure is not shown on the screen.
    """
    # prepare data
    regs, reg_ind, reg_counts = np.unique(data_source["region"], return_index=True,
                                          return_counts=True)
    abs_matrix = np.zeros((6, len(regs)))
    for i in range(len(regs)):
        region_slice = data_source["p24"][reg_ind[i]: reg_ind[i] + reg_counts[i]]
        accidents_values, accidents_counts = np.unique(region_slice, return_counts=True)
        # handle possible invalid values (they would be mapped to -1)
        if accidents_values[0] == -1:
            accidents_values = accidents_values[1:]
            accidents_counts = accidents_counts[1:]
        abs_matrix[accidents_values, i] = accidents_counts
    abs_matrix = np.roll(abs_matrix, -1, axis=0)
    sums = np.sum(abs_matrix, axis=1)
    rel_matrix = (abs_matrix.T / sums).T * 100

    # plot results
    ylabels = ["Přerušovaná žlutá", "Semafor mimo provoz", "Dopravní značky",
               "Přenosné dopravní značky", "Nevyznačena", "Žádná úprava"]
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(8.8, 5.8))
    fig.tight_layout(pad=3)
    masked = np.ma.masked_where(abs_matrix == 0, abs_matrix)
    im_abs = ax1.imshow(masked, cmap="viridis",
                        norm=LogNorm(vmax=10 ** np.ceil(np.log10(abs_matrix.max()))))
    ax1.set_title("Absolutně")
    cbar1 = plt.colorbar(im_abs, ax=ax1, shrink=1.15)
    ax1.set_xticks(range(len(regs)))
    ax1.set_xticklabels(regs)
    ax1.set_yticks(range(len(ylabels)))
    ax1.set_yticklabels(ylabels)
    cbar1.set_label("Počet nehod")

    masked = np.ma.masked_where(rel_matrix == 0, rel_matrix)
    im_rel = ax2.imshow(masked, cmap="plasma", vmin=0, vmax=100)
    ax2.set_title("Relativně vůči příčině")
    cbar2 = plt.colorbar(im_rel, ax=ax2, shrink=1.15)
    ax2.set_xticks(range(len(regs)))
    ax2.set_xticklabels(regs)
    ax2.set_yticks(range(len(ylabels)))
    ax2.set_yticklabels(ylabels)
    cbar2.set_label("Podíl nehod pro danou příčinu [%]")

    if show_figure:
        plt.show()
    if fig_location is not None:
        path = os.path.realpath(os.path.relpath(fig_location))
        dirname = os.path.dirname(path)
        os.makedirs(dirname, exist_ok=True)
        fig.savefig(path)


def main(argv=None):
    """Main function

    Parameters
    ----------
    argv Argument vector passed to the ArgumentParser.
    Following arguments are defined and can be passed from command line:
        --fig_location : Defines location of resulting plots..
        --show_figure : Show the plot when it's created.
    """
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
    if args.fig_location is None and not args.show_figure:
        return

    plot_stat(DataDownloader().get_dict(), args.fig_location, args.show_figure)


if __name__ == "__main__":
    main()
