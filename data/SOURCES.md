# Sources

**`prijsarchief.csv`**
- Content: Dutch day-ahead (EPEX) market price per hour, 1 Jan 2023 – 15 Oct 2026, in EUR/kWh excluding tax.
- Downloaded on 15 Oct 2026 from https://www.salderingswijzer.nl/prijsarchief.csv.
- Reuse is allowed with attribution: "Bron: Salderingswijzer, prijsarchief EPEX day-ahead Nederland (2023–2026), https://www.salderingswijzer.nl/prijsarchief".

**`knmi_uurgegevens_344.txt`**
- Content: hourly global radiation Q in J/cm² per hour, KNMI station 344 Rotterdam (about 8 km from Delft), 1 Jan 2023 – 13 Oct 2026. HH is the hour ending, in UT.
- Downloaded on 15 Oct 2026 from https://www.daggegevens.knmi.nl/klimatologie/uurgegevens (POST `stns=344`, `vars=Q`, `start=2023010101`, `end=2026101324`).
- Licence: CC BY 4.0, KNMI.

**DC load levels** (0.2 / 0.35 / 0.8 kW for 12 apartments, about 10 kWh a day) are rounded from these per-apartment figures:
- Router: 10 W, always on. Routers draw 5–20 W, 10 W typical ([EnergySage](https://www.energysage.com/electricity/house-watts/how-many-watts-does-a-wi-fi-router-use/)).
- Other standby: 5 W, always on. Assumption.
- LED lighting: 10 bulbs × 10 W (requirement ES8), used in the morning and evening. For comparison, the EU average for lighting is 239 kWh per dwelling ([ODYSSEE-MURE](https://odyssee-mure.eu/publications/efficiency-by-sector/households/electricity-consumption-dwelling-electrical-appliances-lighting.html)).
- Laptops: 25 W while in use. Notebooks use 28–55 kWh a year ([IEA 4E](https://www.iea-4e.org/wp-content/uploads/publications/2012/09/4E_Policy_Brief_MB5.pdf)).
- Phones: 10 W for 2 h a day. Assumption.

**Other inputs**
- Flow battery round-trip efficiency, 70 %: a 9 kW vanadium flow battery measured 62–70 % ([University of Padova preprint](https://www.research.unipd.it/bitstream/11577/3310857/1/Comparison%20of%20energy%20losses%20in%20a%209%20kW%20vanadium%20redox%20flow%20battery_preprint.pdf)).
- Tax of €0.10/kWh on bought electricity: 2026 energy tax of €0.09161/kWh excl. VAT ([Belastingdienst](https://www.belastingdienst.nl/wps/wcm/connect/bldcontentnl/belastingdienst/zakelijk/overige_belastingen/belastingen_op_milieugrondslag/energiebelasting)), rounded.
- Solar output = radiation × 50 m² × 17 % (20 % panels × 85 % for inverter, heat and dirt), treating the panels as flat. That gives about 8,850 kWh in 2024.
