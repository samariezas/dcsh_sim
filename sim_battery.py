from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.lines import Line2D

# ---------- inputs ----------
HERE = Path(__file__).parent
OUT = HERE / "report" / "simulations" / "component"
PANEL_AREA = 50.0   # m2
PANEL_EFFICIENCY = 0.20 #idfk
DAILY_LOAD = 10.0   # kWh per day, yearly average
CAPACITY = 20.0     # kWh
POWER = 5.0         # kW, charge and discharge
EFFICIENCY = 0.83   # both charge and discarge, NOT round trip
TAX = 0.10          # EUR/kWh added when buying
SEASONS = {12: "winter", 1: "winter", 2: "winter", 6: "summer", 7: "summer", 8: "summer"}
WEATHER = ["bad", "average", "good"]
SCENARIOS = [(s, w, d) for s in ["winter", "summer"] for w in WEATHER for d in ["weekday", "weekend"]]
COLORS = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4"]
INK, MUTED = "#0b0b0b", "#52514e"
WIDTH = 5.94        # inch, \textwidth of the report


def labels(dates):
    t = pd.to_datetime(dates)
    return t.dt.month.map(SEASONS), np.where(t.dt.dayofweek >= 5, "weekend", "weekday")


def radiation():   # W/m2 per local hour; KNMI gives Q in J/cm2 per hour, HH = hour ending, in UT
    k = pd.read_csv(HERE / "data" / "knmi_uurgegevens_344.txt", comment="#", header=None,
                    names=["STN", "YYYYMMDD", "HH", "Q"], skipinitialspace=True)
    t = pd.to_datetime(k.YYYYMMDD.astype(str), format="%Y%m%d") + pd.to_timedelta(k.HH - 1, unit="h")
    t = t.dt.tz_localize("UTC").dt.tz_convert("Europe/Amsterdam")
    r = pd.DataFrame({"datum": t.dt.strftime("%Y-%m-%d"), "uur": t.dt.hour, "radiation": k.Q * 1e4 / 3600})
    return r.groupby(["datum", "uur"], as_index=False).mean()


def household_load():   # Fluvius 2024 profile, scaled to DAILY_LOAD
    l = pd.read_csv(HERE / "data" / "fluvius_load_2024.csv")
    l["season"], l["daytype"] = labels(l.datum)
    l["load"] = l.load_kw * DAILY_LOAD / l.groupby("datum").load_kw.sum().mean()
    return l.groupby(["season", "daytype", "uur"], as_index=False)["load"].mean()


def load_data():
    df = pd.read_csv(HERE / "data" / "prijsarchief.csv", comment="#").merge(radiation(), on=["datum", "uur"])
    df["season"], df["daytype"] = labels(df.datum)
    df = df.merge(household_load(), on=["season", "daytype", "uur"])
    df["price"] = df.prijs_eur_kwh
    df["pv"] = PANEL_AREA * PANEL_EFFICIENCY * df.radiation / 1000     # kW
    day = df.groupby("datum").agg(season=("season", "first"), daytype=("daytype", "first"), pv=("pv", "sum"))
    day["weather"] = day.groupby("season").pv.transform(lambda s: pd.qcut(s, [0, 0.25, 0.75, 1], labels=WEATHER))
    return df.merge(day.weather, left_on="datum", right_index=True), day


def profiles(df):
    p = df.groupby(["season", "weather", "daytype", "uur"], observed=True)[["price", "pv", "load"]].mean()
    return {sc: p.loc[sc].reset_index() for sc in SCENARIOS}


# ---------- discharge rules: kW per hour, + discharge, - charge ----------
def no_battery(day):
    return np.zeros(len(day))


def fixed_schedule(day):                    # M1
    return np.select([day.uur.between(1, 4), day.uur.between(17, 20)], [-POWER, POWER], 0.0)


def load_following(day):                    # M2
    return (day.load - day.pv).to_numpy()


def price_driven(day, rank_count):          # M3: n cheapest and n most expensive hours of the day
    rank = day.price.rank(method="first")
    return np.select([rank <= rank_count, rank > len(day) - rank_count], [-POWER, POWER], 0.0)


def price4(day):
    return price_driven(day, 4)


def price5(day):
    return price_driven(day, 5)


def price6(day):
    return price_driven(day, 6)


RULES = [no_battery, fixed_schedule, load_following, price4, price5, price6]
NAMES = {"no_battery": "no battery", "fixed_schedule": "fixed schedule", "load_following": "load following",
         "price4": "price-driven, 4 h", "price5": "price-driven, 5 h", "price6": "price-driven, 6 h"}


# ---------- model ----------
def simulate(rule, day, sell=True, repeat=3, efficiency=EFFICIENCY, tax=TAX):   # same day repeated, last one returned
    soc = 0
    price, pv, load, wants = (np.tile(x, repeat) for x in (day.price, day.pv, day.load, rule(day)))
    cost, socs = np.zeros(len(price)), np.zeros(len(price))
    for i, want in enumerate(wants):
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
    return cost[-len(day):], socs[-len(day):]


# ---------- charts ----------
plt.rcParams.update({"font.size": 9, "axes.spines.top": False, "axes.spines.right": False, "axes.grid": True,
                     "grid.color": "#e6e5e1", "grid.linewidth": 0.6, "axes.edgecolor": MUTED, "lines.linewidth": 1.5,
                     "axes.titlesize": 9, "legend.frameon": False, "savefig.dpi": 300, "savefig.bbox": "tight",
                     "figure.constrained_layout.use": True})


def hours(a):
    a.set_xlim(0, 24)
    a.set_xticks(range(0, 25, 3))


def plot_inputs(prof):
    fig, ax = plt.subplots(3, 2, figsize=(WIDTH, 6), sharex=True, sharey="row")
    for (s, w, d), day in prof.items():
        a, ls, x = ax[:, ["winter", "summer"].index(s)], "-" if d == "weekday" else "--", day.uur + 0.5
        a[0].plot(x, day.price, color=COLORS[WEATHER.index(w)], ls=ls)
        a[1].plot(x, day.pv, color=COLORS[WEATHER.index(w)], ls=ls)
        if w == "average":
            a[2].plot(x, day.load, color=INK, ls=ls)
        a[0].set_title(s)
        a[2].set_xlabel("hour of day")
        hours(a[2])
    for a, label in zip(ax[:, 0], ["price (EUR/kWh)", "PV generation (kW)", "load (kW)"]):
        a.set_ylabel(label)
    handles = [Line2D([], [], color=c, label=f"{w} weather") for c, w in zip(COLORS, WEATHER)]
    handles += [Line2D([], [], color=MUTED, ls=ls, label=d) for ls, d in [("-", "weekday"), ("--", "weekend")]]
    fig.legend(handles=handles, loc="outside lower center", ncol=5)
    fig.savefig(OUT / "inputs.png")


def plot_weather(day):
    fig, ax = plt.subplots(1, 2, figsize=(WIDTH, 2.4), sharey=True)
    for a, s in zip(ax, ["winter", "summer"]):
        pv = day[day.season == s].pv
        a.hist(pv, bins=30, color=COLORS[0], edgecolor="white", linewidth=0.5)
        edges = [pv.min(), *pv.quantile([0.25, 0.75]), pv.max()]
        for x in edges[1:3]:
            a.axvline(x, color=INK, ls="--", lw=0.8)
        for x0, x1, w in zip(edges, edges[1:], WEATHER):
            a.text((x0 + x1) / 2, 1.02, w, transform=a.get_xaxis_transform(), ha="center", color=MUTED, fontsize=8)
        a.set(xlabel="PV generation (kWh/day)")
        a.set_title(s, pad=14)
    ax[0].set_ylabel("days")
    fig.savefig(OUT / "weather_split.png")


def plot_soc(prof, sell):
    fig, ax = plt.subplots(4, 3, figsize=(WIDTH, 7), sharex=True, sharey=True)
    for (s, w, d), day in prof.items():
        a = ax[2 * ["winter", "summer"].index(s) + ["weekday", "weekend"].index(d), WEATHER.index(w)]
        for r in [load_following, price5]:
            soc = simulate(r, day, sell)[1]
            a.plot(np.r_[0, day.uur + 1], np.r_[soc[-1], soc], color=COLORS[RULES.index(r) - 1], label=NAMES[r.__name__])
        if s == "winter" and d == "weekday":
            a.set_title(f"{w} weather")
        if w == "bad":
            a.set_ylabel(f"{s}, {d}\nSoC (kWh)")
    for a in ax[-1]:
        a.set_xlabel("hour of day")
        hours(a)
    ax[0, 0].set_ylim(0, CAPACITY * 1.05)
    fig.legend(*ax[0, 0].get_legend_handles_labels(), loc="outside lower center", ncol=3)
    fig.savefig(OUT / f"soc_{'sell' if sell else 'nosell'}.png")


def plot_savings(saving, sell):
    fig, ax = plt.subplots(2, 1, figsize=(WIDTH, 4.8), sharey=True)
    for a, s in zip(ax, ["winter", "summer"]):
        g = saving.loc[s]
        x = np.arange(len(g))
        for k, (r, c) in enumerate(zip(g.columns, COLORS)):
            a.bar(x + (k - 2) * 0.16, g[r], width=0.16, color=c, edgecolor="white", linewidth=0.5, label=NAMES[r])
        a.set_xticks(x, [f"{w}\n{d}" for w, d in g.index])
        a.axhline(0, color=INK, lw=0.6)
        a.set(title=s, ylabel="saving (EUR/day)")
    ax[1].set_xlabel("weather and day type")
    fig.legend(*ax[0].get_legend_handles_labels(), loc="outside lower center", ncol=3)
    fig.savefig(OUT / f"savings_{'sell' if sell else 'nosell'}.png")


# ---------- run ----------
if __name__ == "__main__":
    df, day = load_data()
    prof = profiles(df)
    plot_inputs(prof)
    plot_weather(day)
    days = day.groupby(["season", "weather", "daytype"], observed=True).size()
    counts = days.unstack().reindex(["winter", "summer"], level=0).assign(total=lambda t: t.sum(axis=1))
    counts.rename_axis(columns=None).to_latex(OUT / "scenario_days.tex", index_names=False)
    print(f"days per scenario\n{counts}")
    for sell in [True, False]:
        cost = pd.DataFrame({r.__name__: [simulate(r, prof[sc], sell)[0].sum() for sc in SCENARIOS] for r in RULES},
                            index=pd.MultiIndex.from_tuples(SCENARIOS))
        saving = cost.drop(columns="no_battery").rsub(cost.no_battery, axis=0)
        plot_savings(saving, sell)
        plot_soc(prof, sell)
        table = saving.rename(columns=NAMES).round(2) + 0.0
        table.style.format("{:.2f}").highlight_max(axis=1, props="textbf:--rwrap;").to_latex(
            OUT / f"savings_{'sell' if sell else 'nosell'}.tex", hrules=True, clines="skip-last;data")
        print(f"\nsaving per day (EUR), {'with' if sell else 'without'} selling from battery\n{table.round(2)}")
