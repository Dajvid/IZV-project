#!/usr/bin/env python3.9
# coding=utf-8
"""analysis.py Analyze data from dataset about car accidents provided by PČR"""

__author__ = "David Sedlák"
__email__ = "xsedla1d@stud.fit.vutbr.cz"

from matplotlib import pyplot as plt
import pandas as pd
import seaborn as sns
import pprint


def get_dataframe(filename: str, verbose: bool = False) -> pd.DataFrame:
    """Parse dataframe from pickle file.

    Parameters
    ----------
    filename : String
        Path to file with processed dataset in pickle format
    verbose : Bool
        When set to True, print the size of loaded dataset and size of
        dataset after converting appropriate columns to categorical.
    Returns
    -------
    Parsed dataframe
    """
    df = pd.read_pickle(filename)
    df["date"] = df["p2a"].astype("datetime64")
    orig_size = df.memory_usage(deep=True).sum()
    # cat_cols = ["p36", "p37", "weekday(p2a)", "p6", "p7", "p8", "p9", "p10", "p11",
    #             "p12", "p13a", "p13b", "p13c", "p15", "p16", "p17", "p18", "p19",
    #             "p20",
    #             "p21", "p22", "p23", "p24", "p27", "p28", "p34", "p35", "p39", "p44",
    #             "p45a", "p48a", "p49", "p50a", "p50b", "p51", "p52", "p55a", "p57",
    #             "p58", "h", "i", "k", "l", "p", "q", "t", "p5a"]
    cat_cols = ["h", "i", "k", "l", "p", "q", "t", "n", "o"]  # n?
    df[cat_cols] = df[cat_cols].astype("category")
    new_size = df.memory_usage(deep=True).sum()
    pp = pprint.PrettyPrinter(width=41, compact=True)
    pp.pprint(dict(df.dtypes))
    if verbose:
        mibi = 1024 ** 2
        print(f"orig_size={orig_size / mibi :.1f} MB")
        print(f"new_size={new_size / mibi :.1f} MB")
    return df


def plot_roadtype(df: pd.DataFrame, fig_location: str = None,
                  show_figure: bool = False):
    """Plot roadtype categorical plot.

    Parameters
    ----------
    df : pd.DataFrame
        Dataframe
    fig_location : String
        Path where to save the resulting figure.
    show_figure : Bool
        When set to True, figure is shown on the screen.
    """
    if not fig_location and not show_figure:
        return

    # TODO sharex? sharey?
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

    sns.set_theme()
    sns.set(rc={'axes.facecolor': 'lightblue'})
    g = sns.catplot(data=grouped[grouped["region"].isin(displayed_regions)], x="region",
                    y="Počet nehod", ci=None, col="p21", kind="bar",  col_wrap=3,
                    sharex=True, sharey=True)
    g.set_axis_labels("Kraj", "Počet nehod").set_titles("{col_name}")
    if fig_location:
        plt.savefig(fig_location)
    if show_figure:
        plt.show()


def plot_animals(df: pd.DataFrame, fig_location: str = None,
                 show_figure: bool = False):
    """Plot animals categorical plot.

    Parameters
    ----------
    df : pd.DataFrame
        Dataframe
    fig_location : String
        Path where to save the resulting figure.
    show_figure : Bool
        When set to True, figure is shown on the screen.
    """
    # TODO sharex? sharey?
    if not fig_location and not show_figure:
        return

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
    df = df.groupby(["region", df['date'].dt.month, "p10"]).agg({"Počet nehod": "sum"})
    displayed_regions = ["PHA", "JHM", "OLK", "ZLK"]

    sns.set_theme()
    df = df.reset_index().rename(columns={"p10": "Zavinění"})
    g = sns.catplot(data=df[df["region"].isin(displayed_regions)], x="date",
                    y="Počet nehod", kind="bar", ci=None, col="region", hue="Zavinění",
                    col_wrap=2, sharex=False, sharey=True)
    g.set_axis_labels("Měsíc", "Počet nehod").set_titles("Kraj: {col_name}")
    if fig_location:
        plt.savefig(fig_location)
    if show_figure:
        plt.show()


def plot_conditions(df: pd.DataFrame, fig_location: str = None,
                    show_figure: bool = False):
    """Plot conditions relation plot.

    Parameters
    ----------
    df : pd.DataFrame
        Dataframe
    fig_location : String
        Path where to save the resulting figure.
    show_figure : Bool
        When set to True, figure is shown on the screen.
    """
    # TODO sharex? sharey?
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
    # displayed_regions = ["JHM", "MSK", "OLK", "ZLK"]
    df = df[df["region"].isin(displayed_regions)]
    df["Počet nehod"] = 1
    df = df[df["date"] < "2021-01-01"]
    df = df[df["date"] >= "2016-01-01"]
    df = pd.pivot_table(df, columns="p18", index=["date", "region"],
                        values="Počet nehod", aggfunc="sum")
    df = df.unstack(level=1).resample("M").sum().stack("region").swaplevel(0, 1)
    df = df.melt(ignore_index=False).reset_index()
    df = df.rename(columns={"p18": "Podmínky"})

    sns.set_theme()
    g = sns.relplot(data=df, kind="line", x="date", y="value",
                    hue="Podmínky", col="region", col_wrap=2,
                    facet_kws={'sharey': True, 'sharex': False})
    g.set_axis_labels("", "Počet nehod").set_titles("Kraj: {col_name}")
    g.set(xticks=["2016-01-01", "2017-01-01", "2018-01-01", "2019-01-01",
                  "2020-01-01", "2021-01-01"])
    g.set_xticklabels(["01/16", "01/17", "01/18", "01/19", "01/20", "01/21"])
    if fig_location:
        plt.savefig(fig_location)
    if show_figure:
        plt.show()


if __name__ == "__main__":
    dataframe = get_dataframe("accidents.pkl.gz", verbose=True)
    plot_roadtype(dataframe, fig_location="01_roadtype.png", show_figure=True)
    plot_animals(dataframe, "02_animals.png", True)
    plot_conditions(dataframe, "03_conditions.png", True)
