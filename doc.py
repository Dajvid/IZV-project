#!/usr/bin/python3.8
# coding=utf-8
"""doc.py Calculate statistics, plots and tables used in final doc"""

__author__ = "David Sedlák"
__email__ = "xsedla1d@stud.fit.vutbr.cz"

import os

import pandas as pd
import seaborn as sns
from matplotlib import pyplot as plt


def get_dataframe(filename: str) -> pd.DataFrame:
    """Parse dataframe from pickle file.

    Parameters
    ----------
    filename : String
        Path to file with processed dataset in pickle format
    Returns
    -------
    Parsed dataframe
    """
    df = pd.read_pickle(filename)
    df["datum"] = df["p2a"].astype("datetime64")

    return df


def plot_alcohol(df: pd.DataFrame, fig_location: str = None,
                 show_figure: bool = False):
    """Plot week days and number of accidents with influence of alcohol

    Parameters
    ----------
    df : pd.DataFrame
        Dataframe
    fig_location : String
        Path where to save the resulting figure.
    show_figure : Bool
        When set to True, figure is shown on the screen.
    """
    # create column with day of the week for each accident
    df["day"] = df["datum"].dt.dayofweek
    # create column to aggregate over
    df["Počet nehod"] = 1

    alcohol_mask = df["p11"].isin([1, 3, 5, 6, 7, 8, 9])
    alcohol_df = df[alcohol_mask].copy()
    no_alcohol_df = df[~alcohol_mask].copy()
    # print absolute and relative number of alcohol accidents
    print(f"Absolutní počet nehod pod vlivem alkoholu: {len(alcohol_df)}")
    print(f"Relativní počet nehod pod vlivem alkoholu: {len(alcohol_df) / len(no_alcohol_df) * 100:.2f} %")

    grouped_alcohol = alcohol_df.groupby(["day"]).agg({"Počet nehod": "sum"})
    grouped_no_alcohol = no_alcohol_df.groupby(["day"]).agg({"Počet nehod": "sum"})
    # calculate relative ratio of accidents involving alcohol
    grouped_alcohol_relative = grouped_alcohol / (grouped_alcohol + grouped_no_alcohol) * 100

    # concatenate both dataframes
    grouped_alcohol["type"] = "Absolutní počet"
    grouped_alcohol_relative["type"] = "Relativní počet [%]"
    result = pd.concat([grouped_alcohol, grouped_alcohol_relative]).reset_index()

    # add proper day labels
    result["day"] = result["day"].map({
        0: "Po",
        1: "Út",
        2: "St",
        3: "Čt",
        4: "Pá",
        5: "So",
        6: "Ne"
    })

    # plot the result
    sns.set_theme()
    g = sns.catplot(data=result, x="day",
                    y="Počet nehod", ci=None, col="type", kind="bar",
                    sharex=True, sharey=False)
    g.set_axis_labels("Dny v týdnu", "Nehody zaviněné pod vlivem alkoholu").set_titles("{col_name}")

    if fig_location is not None:
        path = os.path.realpath(os.path.relpath(fig_location))
        dirname = os.path.dirname(path)
        os.makedirs(dirname, exist_ok=True)
        plt.savefig(path)
    if show_figure:
        plt.show()


def calculate_alcohol_causalities(df: pd.DataFrame, verbose: bool = False):
    """Calculate number of causalities in accidents with influence of alcohol

    Parameters
    ----------
    df : pd.DataFrame
        Dataframe
    verbose : Bool
        When set to True, print the output to stdout.
    Returns
    -------
    Absolute and relative number of casualties
    """
    alcohol_mask = df["p11"].isin([1, 3, 5, 6, 7, 8, 9])
    df["alcohol"] = False
    df.loc[alcohol_mask, "alcohol"] = True
    # drop invalid values
    df = df.drop(df[df["p13a"] < 0].index)
    grouped = df.groupby(["alcohol"]).agg({"p13a": "sum"})
    absolute_alcohol_causalities = grouped.loc[True]["p13a"]
    no_alcohol_causalities = grouped.loc[False]["p13a"]
    relative_alcohol_causalities = 100 * absolute_alcohol_causalities / (absolute_alcohol_causalities +
                                                                         no_alcohol_causalities)
    if verbose:
        print(f"Absolutní počet obětí v nehodách pod vlivem alkoholu: {absolute_alcohol_causalities}")
        print(f"Relativní počet obětí v nehodách pod vlivem alkoholu: {relative_alcohol_causalities:.2f} %")

    return absolute_alcohol_causalities, relative_alcohol_causalities


def alcohol_vehicle_category(df: pd.DataFrame, verbose: bool = False):
    """Generate table of vehicle types with they relative number of alcohol accidents

    Parameters
    ----------
    df : pd.DataFrame
        Dataframe
    verbose : Bool
        When set to True, print the output to stdout.
    Returns
    -------
    Resulting dataframe.
    """
    # drop invalid and unknown values
    df = df.drop(df[(df["p44"] < 0) | (df["p44"] == 17) | (df["p44"] == 18)].index)

    df["Druh vozidla"] = df["p44"].map({
        0: "Moped",
        1: "Malý motocykl",
        2: "Motocykl",
        3: "Osobní automobil",
        4: "Osobní automobil",
        5: "Nákladní automobil",
        6: "Nákladní automobil",
        7: "Nákladní automobil",
        8: "Autobus",
        9: "Traktor",
        10: "Tramvaj",
        11: "Trolejbus",
        12: "Jiné motorové",
        13: "Jízdní kolo",
        14: "Jiné nemotorové",
        15: "Jiné nemotorové",
        16: "Vlak",
        18: "Jiné"
    })

    alcohol_mask = df["p11"].isin([1, 3, 5, 6, 7, 8, 9])
    df["Poměr nehod"] = 1
    df_alcohol = df[alcohol_mask].copy()
    df_no_alcohol = df[~alcohol_mask].copy()

    alcohol_grouped = df_alcohol.groupby(["Druh vozidla"]).agg({"Poměr nehod": "sum"})
    no_alcohol_grouped = df_no_alcohol.groupby(["Druh vozidla"]).agg({"Poměr nehod": "sum"})

    result = 100 * alcohol_grouped / (alcohol_grouped + no_alcohol_grouped)
    result = result.dropna().sort_values("Poměr nehod", ascending=False)
    if verbose:
        print("Tabulka relativních počtů nehod pod vlivem alkoholu v jednotlivých kategoriích:")
        print(result.to_latex(na_rep=0, column_format='lc', float_format="{:,.2f} %".format, label="tab:alcohol",
                              caption="Relativní poměr nehod pod vlivem alkoholu u jednotlivých typů vozidla"))

    return result


if __name__ == "__main__":
    dataframe = get_dataframe("accidents.pkl.gz")
    plot_alcohol(dataframe, "alcohol.pdf", show_figure=True)
    calculate_alcohol_causalities(dataframe, verbose=True)
    alcohol_vehicle_category(dataframe, verbose=True)
