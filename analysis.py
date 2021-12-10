#!/usr/bin/env python3.9
# coding=utf-8
"""analysis.py Analyze data from dataset about car accidents provided by PČR"""

__author__ = "David Sedlák"
__email__ = "xsedla1d@stud.fit.vutbr.cz"

from matplotlib import pyplot as plt
import pandas as pd
import seaborn as sns
import numpy as np
import os

# muzete pridat libovolnou zakladni knihovnu ci knihovnu predstavenou na prednaskach
# dalsi knihovny pak na dotaz



""" Ukol 1:
načíst soubor nehod, který byl vytvořen z vašich dat. Neznámé integerové hodnoty byly mapovány na -1.

Úkoly:
- vytvořte sloupec date, který bude ve formátu data (berte v potaz pouze datum, tj sloupec p2a)
- vhodné sloupce zmenšete pomocí kategorických datových typů. Měli byste se dostat po 0.5 GB. Neměňte však na kategorický typ region (špatně by se vám pracovalo s figure-level funkcemi)
- implementujte funkci, která vypíše kompletní (hlubkou) velikost všech sloupců v DataFrame v paměti:
orig_size=X MB
new_size=X MB

Poznámka: zobrazujte na 1 desetinné místo (.1f) a počítejte, že 1 MB = 1e6 B. 
"""


def get_dataframe(filename: str, verbose: bool = False) -> pd.DataFrame:
    """Parse dataframe from pickle file.

    Parameters
    ----------
    filename : String
        Path to file with processed dataset in pickle format
    verbose : Bool
        When set to True, print the size of loaded dataset and size of
        dataset after converting appropriate collumns to categoricla.
    Returns
    -------
    Parsed dataframe
    """
    df = pd.read_pickle(filename)
    df["date"] = df["p2a"].astype("datetime64")
    orig_size = df.memory_usage(deep=True).sum()
    # p2b?, p14?, p47?, p53?, j?, n?, o?, r?
    cat_cols = ["p36", "p37", "weekday(p2a)", "p6", "p7", "p8", "p9", "p10", "p11",
                "p12", "p13a", "p13b", "p13c", "p15", "p16", "p17", "p18", "p19", "p20",
                "p21", "p22", "p23", "p24", "p27", "p28", "p34", "p35", "p39", "p44",
                "p45a", "p48a", "p49", "p50a", "p50b", "p51", "p52", "p55a", "p57",
                "p58", "h", "i", "k", "l", "p", "q", "t", "p5a"]
    df[cat_cols] = df[cat_cols].astype("category")
    new_size = df.memory_usage(deep=True).sum()
    if verbose:
        mibi = 1024 ** 2
        print(f"orig_size={orig_size / mibi :.1f} MB")
        print(f"new_size={new_size / mibi :.1f} MB")
    return df


def plot_roadtype(df: pd.DataFrame, fig_location: str = None,
                  show_figure: bool = False):
    if not fig_location and not show_figure:
        return

    # TODO ordering?
    df["p21"] = df["p21"].map({
        0: "Jiná komunikace",
        1: "Dvoupruhová komunikace",
        2: "Třípruhová komunikace",
        3: "Čtyřpruhová komunikace",
        4: "Čtyřpruhová komunikace",
        5: "Vícepruhová komunikace",
        6: "Rychlostní komunikace"
    })
    df["Počet nehod"] = 1
    grouped = df.groupby(["region", "p21"]).agg({"Počet nehod": "sum"}).reset_index()
    displayed_regions = ["PHA", "JHM", "OLK", "ZLK"]
    g = sns.catplot(data=grouped[grouped["region"].isin(displayed_regions)], x="region",
                    y="Počet nehod", ci=None, col="p21", kind="bar",  col_wrap=3)
    g.set_axis_labels("Kraj", "Počet nehod").set_titles("{col_name}")
    if fig_location:
        plt.savefig(fig_location)
    if show_figure:
        plt.show()


def plot_animals(df: pd.DataFrame, fig_location: str = None,
                 show_figure: bool = False):
    if not fig_location and not show_figure:
        return

    # TODO ordering?, axis_labels, hue_labels? != p10
    df["p10"] = df["p10"].map({
        1: "řidičem",
        2: "řidičem",
        4: "zvěří",
        3: "jiné",
        5: "jiné",
        6: "jiné",
        7: "jiné",
        0: "jiné"
    })
    df["Počet nehod"] = 1
    df = df[df["date"] < "2021-01-01"]
    grouped = df.groupby(["region", df['date'].dt.month, "p10"]).agg({"Počet nehod": "sum"}).reset_index()
    displayed_regions = ["PHA", "JHM", "OLK", "ZLK"]
    g = sns.catplot(data=grouped[grouped["region"].isin(displayed_regions)], x="date",
                    y="Počet nehod", kind="bar", ci=None, col="region", hue="p10",
                    col_wrap=2)
    g.set_axis_labels("Měsíc", "Počet nehod").set_titles("Kraj: {col_name}")
    if fig_location:
        plt.savefig(fig_location)
    if show_figure:
        plt.show()


# Ukol 4: Povětrnostní podmínky
def plot_conditions(df: pd.DataFrame, fig_location: str = None,
                    show_figure: bool = False):
    if not fig_location and not show_figure:
        return

    df["p18"] = df["p18"].map({
        1: "neztížené",
        2: "mlha",
        3: "na počátku deště",
        4: "déšť",
        5: "sněžení",
        6: "náledí",
        7: "vítr"
    })
    df = df[df["p18"] != 0]
    displayed_regions = ["PHA", "JHM", "OLK", "ZLK"]
    displayed_regions = ["JHM", "MSK", "OLK", "ZLK"]
    df = df[df["region"].isin(displayed_regions)]
    df["Počet nehod"] = 1
    df = df[df["date"] < "2021-01-01"]
    df = pd.pivot_table(df, columns="p18", index=["date", "region"], values="Počet nehod", aggfunc="sum")
    #print(df.unstack(level=1).resample("M").sum().stack("region"))
    df = df.unstack(level=1).resample("M").sum().stack("region").swaplevel(0,1)
    # print(df)
    df = df.melt(ignore_index=False).reset_index()
    g = sns.relplot(data=df, kind="line", x="date", y="value", hue="p18", col="region", col_wrap=2) #sharex=false
    g.set_axis_labels(None, "Počet nehod").set_titles("Kraj: {col_name}")
    plt.show()


if __name__ == "__main__":
    # zde je ukazka pouziti, tuto cast muzete modifikovat podle libosti
    # skript nebude pri testovani pousten primo, ale budou volany konkreni ¨
    # funkce.
    df = get_dataframe("accidents.pkl.gz", verbose=True) # tento soubor si stahnete sami, při testování pro hodnocení bude existovat
    # plot_roadtype(df, fig_location="01_roadtype.png", show_figure=True)
    # plot_animals(df, "02_animals.png", True)
    plot_conditions(df, "03_conditions.png", True)
