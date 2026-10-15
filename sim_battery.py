from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

# ---------- inputs ----------
HERE = Path(__file__).parent
START, END = "2024-01-01", "2026-12-31"
PANEL_AREA = 50.0   # m2
PANEL_EFFICIENCY = 0.20 #idfk
CAPACITY = 20.0     # kWh
POWER = 5.0         # kW, charge and discharge
EFFICIENCY = 0.83   # both charge and discarge, NOT round trip
TAX = 0.10          # EUR/kWh added when buying


def dc_load(hour):  # kW, 12 apartments: routers, LED lighting, laptops, phones
    return np.select([hour < 7, hour < 17, hour < 23], [0.2, 1.35, 2.8], 0.2)


def radiation():   # W/m2 per local hour; KNMI gives Q in J/cm2 per hour, HH = hour ending, in UT
    k = pd.read_csv(HERE / "data" / "knmi_uurgegevens_344.txt", comment="#", header=None,
                    names=["STN", "YYYYMMDD", "HH", "Q"], skipinitialspace=True)
    t = pd.to_datetime(k.YYYYMMDD.astype(str), format="%Y%m%d") + pd.to_timedelta(k.HH - 1, unit="h")
    t = t.dt.tz_localize("UTC").dt.tz_convert("Europe/Amsterdam")
    r = pd.DataFrame({"datum": t.dt.strftime("%Y-%m-%d"), "uur": t.dt.hour, "radiation": k.Q * 1e4 / 3600})
    return r.groupby(["datum", "uur"], as_index=False).mean()


def load_data():
    df = pd.read_csv(HERE / "data" / "prijsarchief.csv", comment="#")
    df = df[(df.datum >= START) & (df.datum <= END)]
    df = df.merge(radiation(), on=["datum", "uur"], how="left").fillna({"radiation": 0})
    df["price"] = df.prijs_eur_kwh
    df["load"] = dc_load(df.uur)
    df["pv"] = PANEL_AREA * PANEL_EFFICIENCY * df.radiation / 1000     # kW
    return df


# ---------- discharge rules: kW per hour, + discharge, - charge ----------
def no_battery(df):
    return np.zeros(len(df))


def fixed_schedule(df):                     # M1
    return np.select([df.uur.between(1, 4), df.uur.between(17, 20)], [-POWER, POWER], 0.0)


def load_following(df):                     # M2
    return (df.load - df.pv).to_numpy()


def price_driven(df, rank_count):         # M3: n cheapest and n most expensive hours of each day
    rank = df.groupby("datum").price.rank(method="first")
    hours = df.groupby("datum").price.transform("size")
    return np.select([rank <= rank_count, rank > hours - rank_count], [-POWER, POWER], 0.0)


def price3(df):
    return price_driven(df, 3)


def price4(df):
    return price_driven(df, 4)


def price5(df):
    return price_driven(df, 5)


RULES = [no_battery, fixed_schedule, load_following, price3, price4, price5]


# ---------- model ----------
def simulate(rule, df, efficiency=EFFICIENCY, tax=TAX, sell=True):
    soc = 0
    price, pv, load = df.price.to_numpy(), df.pv.to_numpy(), df.load.to_numpy()
    cost, socs = np.zeros(len(df)), np.zeros(len(df))
    for i, want in enumerate(rule(df)):
        if want > 0:
            if not sell:
                want = min(want, max(load[i] - pv[i], 0))
            battery = min(want, POWER, soc * efficiency)
            soc -= battery / efficiency
        else:
            battery = -min(-want, POWER, (CAPACITY - soc) / efficiency)
            soc -= battery * efficiency
        grid = load[i] - pv[i] - battery            # + bought, - sold
        cost[i] = grid * (price[i] + tax) if grid > 0 else grid * price[i]
        socs[i] = soc
    return cost, socs


# ---------- run ----------
if __name__ == "__main__":
    df = load_data()
    days = pd.to_datetime(df.datum)
    results = {r.__name__: simulate(r, df) for r in RULES} | {f'{r.__name__}_nosell': simulate(r, df, sell=False) for r in RULES}
    base = results["no_battery"][0]

    fig, ax = plt.subplots(1, 1, figsize=(10, 6))
    for k, (name, (cost, socs)) in enumerate(results.items()):
        saving = pd.Series(base - cost).groupby(days).sum().cumsum()
        ax.plot(saving.index, saving, color=f"C{k}", label=name)
    ax.axhline(0, color="k", lw=0.8)
    ax.set_title(f"cumulative saving against no battery, {START} to {END}")
    ax.set_ylabel("EUR")
    ax.legend()
    fig.tight_layout()
    fig.savefig(HERE / "results" / "simulation.png", dpi=150)

    total = pd.DataFrame({n: {"cost (EUR)": c.sum(), "saving (EUR)": base.sum() - c.sum()}
                          for n, (c, _) in results.items()}).T.round(0)
    print(f"{START} to {END} ({df.datum.nunique()} days)\n{total}")
