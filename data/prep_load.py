import sys, zipfile
from pathlib import Path

import pandas as pd

parts = []
for c in pd.read_csv(zipfile.ZipFile(sys.argv[1]).open("P6269_Open_Data_geen_ZP.csv"), chunksize=2_000_000,
                     usecols=["Datum_Startuur", "Volume_Afname_KWh", "Elektrisch_Voertuig_Indicator", "Contract_Categorie"]):
    c = c[(c.Elektrisch_Voertuig_Indicator == 0) & (c.Contract_Categorie == "Residentieel")]
    parts.append(c.groupby("Datum_Startuur").Volume_Afname_KWh.agg(["sum", "count"]))
q = pd.concat(parts).groupby(level=0).sum()
t = pd.to_datetime(q.index.str[:19])
q = pd.DataFrame({"datum": t.strftime("%Y-%m-%d"), "uur": t.hour, "load_kw": 4 * q["sum"].to_numpy() / q["count"].to_numpy()})
q.groupby(["datum", "uur"]).load_kw.mean().round(4).to_csv(Path(__file__).parent / "fluvius_load_2024.csv")
