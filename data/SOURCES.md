# Sources

**`prijsarchief.csv`**
- Content: Dutch day-ahead (EPEX) market price per hour, 1 Jan 2023 – 15 Oct 2026, in EUR/kWh excluding tax.
- Downloaded on 15 Oct 2026 from https://www.salderingswijzer.nl/prijsarchief.csv.
- Reuse is allowed with attribution: "Bron: Salderingswijzer, prijsarchief EPEX day-ahead Nederland (2023–2026), https://www.salderingswijzer.nl/prijsarchief".

**`knmi_uurgegevens_344.txt`**
- Content: hourly global radiation Q in J/cm² per hour, KNMI station 344 Rotterdam (about 8 km from Delft), 1 Jan 2023 – 13 Oct 2026. HH is the hour ending, in UT.
- Downloaded on 15 Oct 2026 from https://www.daggegevens.knmi.nl/klimatologie/uurgegevens (POST `stns=344`, `vars=Q`, `start=2023010101`, `end=2026101324`).
- Licence: CC BY 4.0, KNMI.

**`fluvius_load_2024.csv`**
- Content: average household electricity use in kW per local hour, 2024, built by `prep_load.py` from Fluvius quarter-hour digital meter data. Uses the 300 residential households without solar panels, heat pump or electric car (`P6269_Open_Data_geen_ZP.csv`). The timestamps are marked UTC but are local time (31 March misses 02:00–03:00, 27 October has it twice); the doubled hour is averaged.
- Downloaded on 20 Oct 2026 from https://fluvius.opendatasoft.com/api/v2/catalog/datasets/1_50-verbruiksprofielen-dm-elek-kwartierwaarden-voor-een-volledig-jaar/attachments/p6269_1_50_dmk_sample_elek_2024_deel_1_zip (dataset "Verbruiksprofielen digitale elektriciteitsmeters: kwartierwaarden voor een volledig jaar").
- Licence: Open data license - Fluvius, https://opendata.fluvius.be/p/licentieopendatafluvius.
- Average of 2,729 kWh per household per year. Flemish households, so the rise at 22:00 likely comes from the Belgian night tariff.

**DC load**: the hourly shape is the Fluvius profile, averaged per season and weekday/weekend, scaled so that the yearly average is 10 kWh a day for 12 apartments (8.4–12.6 kWh a day depending on scenario). The 10 kWh a day is rounded from these per-apartment figures:
- Router: 10 W, always on. Routers draw 5–20 W, 10 W typical ([EnergySage](https://www.energysage.com/electricity/house-watts/how-many-watts-does-a-wi-fi-router-use/)).
- Other standby: 5 W, always on. Assumption.
- LED lighting: 10 bulbs × 10 W (requirement ES8), used in the morning and evening. For comparison, the EU average for lighting is 239 kWh per dwelling ([ODYSSEE-MURE](https://odyssee-mure.eu/publications/efficiency-by-sector/households/electricity-consumption-dwelling-electrical-appliances-lighting.html)).
- Laptops: 25 W while in use. Notebooks use 28–55 kWh a year ([IEA 4E](https://www.iea-4e.org/wp-content/uploads/publications/2012/09/4E_Policy_Brief_MB5.pdf)).
- Phones: 10 W for 2 h a day. Assumption.

**Other inputs**
- Flow battery round-trip efficiency, 70 %: a 9 kW vanadium flow battery measured 62–70 % ([University of Padova preprint](https://www.research.unipd.it/bitstream/11577/3310857/1/Comparison%20of%20energy%20losses%20in%20a%209%20kW%20vanadium%20redox%20flow%20battery_preprint.pdf)).
- Tax of €0.10/kWh on bought electricity: 2026 energy tax of €0.09161/kWh excl. VAT ([Belastingdienst](https://www.belastingdienst.nl/wps/wcm/connect/bldcontentnl/belastingdienst/zakelijk/overige_belastingen/belastingen_op_milieugrondslag/energiebelasting)), rounded.
- Solar output = radiation × 50 m² × 20 %, treating the panels as flat and ignoring inverter, heat and dirt losses. That gives about 10,400 kWh in 2024.
