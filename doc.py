import os

import pandas as pd
import seaborn as sns
from matplotlib import pyplot as plt


def get_dataframe(filename: str, verbose: bool = False) -> pd.DataFrame:
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
    print(f"Relativní podíl nehod pod vlivem alkoholu: {len(alcohol_df) / len(no_alcohol_df) * 100} %")

    grouped_alcohol = alcohol_df.groupby(["day"]).agg({"Počet nehod": "sum"})
    grouped_no_alcohol = no_alcohol_df.groupby(["day"]).agg({"Počet nehod": "sum"})
    # calculate relative ratio of accidents involivng alcohol
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

    if fig_location:
        plt.savefig(fig_location)
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
    print(absolute_alcohol_causalities, no_alcohol_causalities)
    if verbose:
        print(f"Absolutní počet obětí v nehodách pod vlivem alkoholu: {absolute_alcohol_causalities}")
        print(f"Relativní počet obětí v nehodách podvlivem alkoholu: {relative_alcohol_causalities} %")

    return absolute_alcohol_causalities, relative_alcohol_causalities


def generate_highest_alcohol_days_table(df: pd.DataFrame, verbose: bool = False):
    """Generate table of days with the highest number of alcohol accidents in each year

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
    # get only accidents involving alcohol
    alcohol_mask = df["p11"].isin([1, 3, 5, 6, 7, 8, 9])
    df = df[alcohol_mask].copy()
    df["year"] = df["datum"].dt.year
    df["Počet nehod"] = 1

    result = df.groupby(["datum"]).agg({"Počet nehod": "sum"}).sort_values("Počet nehod", ascending=False).head(10)


    print(result.to_latex())


if __name__ == "__main__":
    dataframe = get_dataframe("accidents.pkl.gz")
    # plot_alcohol(dataframe, "alcohol.pdf", True)
    # calculate_alcohol_causalities(dataframe, verbose=True)
    generate_highest_alcohol_days_table(dataframe, verbose=True)
