#!/usr/bin/python3.8
# coding=utf-8
"""geo.py Make geographical plots from dataset about car accidents provided by PČR"""

__author__ = "David Sedlák"
__email__ = "xsedla1d@stud.fit.vutbr.cz"

import pandas as pd
import geopandas
import matplotlib.pyplot as plt
import contextily
import sklearn.cluster
import numpy as np
# muzete pridat vlastni knihovny


def make_geo(df: pd.DataFrame) -> geopandas.GeoDataFrame:
    """ Konvertovani dataframe do geopandas.GeoDataFrame se spravnym kodovani"""
    print(len(df)) # todo check and remove
    df.dropna(subset=["d", "e"], inplace=True)
    df["date"] = df["p2a"].astype("datetime64")
    print(len(df))
    gdf = geopandas.GeoDataFrame(df,
                                 geometry=geopandas.points_from_xy(df["d"], df["e"]),
                                 crs="EPSG:5514")
    gdf.to_crs("epsg:3857", inplace=True)
    return gdf


def plot_geo(gdf: geopandas.GeoDataFrame, fig_location: str = None,
             show_figure: bool = False):
    """Create graphs based on location of the accidents for years 2018 - 2020

    Parameters
    ----------
    gdf : geopandas.GeoDataFrame
        Geopandas dataframe with dataset.
    fig_location : String
        Path where to save the resulting figure.
    show_figure : Bool
        When set to True, figure is shown on the screen.
    """
    region = "JHM"
    # filter the region of interets
    gdf = gdf[gdf["region"] == "JHM"]
    fig, axes = plt.subplots(3, 2, figsize=(8, 12))
    fig.tight_layout

    for i, year in enumerate([2018, 2019, 2020]):
        year_data = gdf[gdf["date"].dt.year == year]
        # highway
        year_data[year_data["p36"] == 0].plot(ax=axes[i][0], markersize=1, color="green")
        contextily.add_basemap(axes[i][0], crs=year_data.crs.to_string(),
                               source=contextily.providers.Stamen.TonerLite,
                               zoom=10, alpha=0.9)
        # TODO poměr stran?
        axes[i][0].set_aspect("auto")
        axes[i][0].axis('off')
        axes[i][0].set_title(f"{region} kraj: dálnice ({year})")

        # first class roads
        year_data[year_data["p36"] == 1].plot(ax=axes[i][1], markersize=1, color="red")
        contextily.add_basemap(axes[i][1], crs=year_data.crs.to_string(),
                               source=contextily.providers.Stamen.TonerLite,
                               zoom=10, alpha=0.9)
        # TODO poměr stran?
        axes[i][1].set_aspect("auto")
        axes[i][1].axis('off')
        axes[i][1].set_title(f"{region} kraj: silnice první třídy ({year})")

    if fig_location:
        # todo check existence
        plt.savefig(fig_location)
    if show_figure:
        plt.show()


def plot_cluster(gdf: geopandas.GeoDataFrame, fig_location: str = None,
                 show_figure: bool = False):
    """ Vykresleni grafu s lokalitou vsech nehod v kraji shlukovanych do clusteru """
    region = "JHM"
    # filter the region of interets
    gdf = gdf[gdf["region"] == "JHM"]

    fig, ax = plt.subplots(1, 1, figsize=(8, 12))


if __name__ == "__main__":
    # zde muzete delat libovolne modifikace
    gdf = make_geo(pd.read_pickle("accidents.pkl.gz"))
    plot_geo(gdf, "geo1.png", True)
    # plot_cluster(gdf, "geo2.png", True)
