# Builds the Kaggle notebook "Which supermarket is cheapest in Argentina?" from the La Canasta open data.
#   python datos-abiertos/make_kaggle_cheapest.py   -> datos-abiertos/kaggle-cheapest/cheapest-supermarket-argentina.ipynb
# Published on Kaggle by the "Kaggle notebooks" workflow. On Kaggle it finds the files under /kaggle/input.
import json, os
import nbformat as nbf

md, code = nbf.v4.new_markdown_cell, nbf.v4.new_code_cell
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "kaggle-cheapest")

cells = [
md("""# Which supermarket is cheapest in Argentina?
### ¿Qué supermercado es más barato en Argentina?

*By Ramon Pepa, founder of [La Canasta](https://lacanastaindex.com), the daily supermarket price index for Argentina.*

Every day La Canasta reads the online prices of **Carrefour, Jumbo, ChangoMás and Día**. This notebook answers one question with that data: **if you buy exactly the same products, which shop charges you least?**

The comparison is strict: the **same barcode** at every shop, sold by the unit, in stock, and averaged over each week so that a one-day promotion does not decide the result.

*Cada día La Canasta lee los precios online de Carrefour, Jumbo, ChangoMás y Día. Este notebook compara **exactamente los mismos productos** (mismo código de barras) en los cuatro súper, semana por semana.*

Data: [La Canasta: Argentina Daily Supermarket Prices](https://www.kaggle.com/datasets/ramonpepa/la-canasta-daily-supermarket-prices) · Weekly ranking online: [lacanastaindex.com/precios/supermercado-mas-barato.html](https://lacanastaindex.com/precios/supermercado-mas-barato.html) · DOI [10.5281/zenodo.23856045](https://doi.org/10.5281/zenodo.23856045)"""),
code("""import glob, os
import pandas as pd
import matplotlib.pyplot as plt

def find(name):
    for r in [os.environ.get("LC_DATA", ""), "/kaggle/input", "."]:
        if r:
            hits = glob.glob(os.path.join(r, "**", name), recursive=True)
            if hits:
                return hits[0]
    raise FileNotFoundError(name)

prices = pd.read_csv(find("precios_diarios.csv"), dtype={"sku_id": str, "ean": str}, low_memory=False,
                     usecols=["date", "shop", "ean", "name", "unit", "unit_multiplier", "price", "available"])
prices["date"] = pd.to_datetime(prices["date"])

SHOPS = ["Carrefour", "Jumbo", "ChangoMas", "Dia"]
NAME = {"Carrefour": "Carrefour", "Jumbo": "Jumbo", "ChangoMas": "ChangoMás", "Dia": "Día"}
COLOR = {"Carrefour": "#2B3B5C", "Jumbo": "#C0392B", "ChangoMas": "#D98A2B", "Dia": "#2D7A57"}
plt.rcParams.update({"axes.spines.top": False, "axes.spines.right": False, "font.size": 11})

# Strict comparison: same barcode, sold by the unit, in stock, at the four shops in the index
p = prices[prices["shop"].isin(SHOPS) & prices["available"].astype(str).eq("True") & prices["ean"].notna()
           & prices["unit"].astype(str).str.lower().eq("un") & (prices["unit_multiplier"] == 1) & (prices["price"] > 0)].copy()
p["week"] = p["date"].dt.to_period("W-THU").dt.start_time   # weeks Friday to Thursday, like the La Canasta index
print(f"{p['date'].min().date()} to {p['date'].max().date()}: {len(p):,} prices, {p['ean'].nunique():,} barcodes")"""),
md("""## How the comparison works

For each week:

1. Average each product's price at each shop over the days it was in stock (at least half the days of that week).
2. Keep only the products found at **all four shops** that week.
3. Leave out obvious mismatches (one shop more than 3 times another: usually a different pack size under the same barcode).
4. Add up the bill at each shop. Same products, same quantities, so the only difference is the price."""),
code("""def compare(week_prices):
    n_days = week_prices["date"].nunique()
    s = week_prices.groupby(["ean", "shop"])["price"].agg(["mean", "count"])
    s = s[s["count"] >= -(-n_days // 2)]
    wide = s["mean"].unstack().reindex(columns=SHOPS).dropna()
    return wide[wide.max(axis=1) <= 3 * wide.min(axis=1)]

weeks = []
for w, g in p.groupby("week"):
    if g["date"].nunique() < 3:          # skip weeks with fewer than 3 days of data
        continue
    wide = compare(g)
    totals = wide.sum()
    row = (totals / totals.min() - 1) * 100
    row["products"] = len(wide)
    row["days"] = g["date"].nunique()
    row["week"] = g["date"].min()   # first day with data that week
    weeks.append(row)
weekly = pd.DataFrame(weeks).set_index("week")
weekly.index = weekly.index.strftime("%d %b")
show = weekly[SHOPS].rename(columns=NAME).round(1)
show["products compared"] = weekly["products"].astype(int)
show"""),
md("""Each number is **how much more expensive than the cheapest shop** that week, for the same products (0 = cheapest)."""),
code("""last = p[p["date"] > p["date"].max() - pd.Timedelta(days=7)]
wide = compare(last)
totals = wide.sum().sort_values()
pct = (totals / totals.min() - 1) * 100

fig, ax = plt.subplots(figsize=(9, 4.6))
ax.bar(range(len(totals)), totals.values, color=[COLOR[s] for s in totals.index])
ax.set_xticks(range(len(totals)), [NAME[s] for s in totals.index])
for i, (t, v) in enumerate(zip(totals, pct)):
    ax.text(i, t, f"${t:,.0f}\\n" + ("cheapest" if v == 0 else f"+{v:.1f}%"), ha="center", va="bottom")
ax.set_ylim(0, totals.max() * 1.18)
ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda v, _: f"${v / 1e6:.1f}M"))
ax.set_ylabel("Bill for the same products (ARS)")
ax.set_title(f"The same {len(wide)} products at the four shops, last 7 days to {last['date'].max().date()}", loc="left")
plt.show()

print(f"Cheapest: {NAME[totals.index[0]]}. Most expensive: {NAME[totals.index[-1]]}, "
      f"{pct.iloc[-1]:.1f}% more for exactly the same {len(wide)} products.")"""),
md("""## Is it the same every week?

A one-week result could be luck (a big promotion, a stock problem). The line chart shows every week since the index started."""),
code("""fig, ax = plt.subplots(figsize=(10, 4.6))
for s in SHOPS:
    ax.plot(range(len(weekly)), weekly[s].values, marker="o", lw=2.2, color=COLOR[s], label=NAME[s])
ax.set_xticks(range(len(weekly)), [f"week of {d}" for d in weekly.index])
ax.set_ylabel("% more expensive than the cheapest shop")
ax.axhline(0, color="grey", lw=0.8)
ax.set_ylim(-1.5, weekly[SHOPS].values.max() + 3)
ax.legend(frameon=False, ncol=4, loc="upper center", bbox_to_anchor=(0.5, -0.12))
ax.set_title("Same products, week by week", loc="left")
plt.show()"""),
md("""## Which shop wins product by product?

The total bill hides something: no shop is cheapest for everything. Here is how many of the compared products each shop sells at the lowest price (last 7 days)."""),
code("""wins = wide.idxmin(axis=1).value_counts().reindex(SHOPS).fillna(0).sort_values(ascending=False)
fig, ax = plt.subplots(figsize=(9, 4))
ax.bar(range(len(wins)), wins.values, color=[COLOR[s] for s in wins.index])
ax.set_xticks(range(len(wins)), [NAME[s] for s in wins.index])
for i, v in enumerate(wins.values):
    ax.text(i, v, f"{int(v)} ({v / len(wide):.0%})", ha="center", va="bottom")
ax.set_ylim(0, wins.max() * 1.15)
ax.set_ylabel("Products where it is the cheapest")
ax.set_title("Number of products each shop sells cheapest", loc="left")
plt.show()"""),
md("""## The biggest gaps for the same product

Same barcode, same week, very different prices. These are the products where shopping around matters most."""),
code("""names = last.drop_duplicates("ean").set_index("ean")["name"]
gap = (wide.max(axis=1) / wide.min(axis=1) - 1).mul(100).sort_values(ascending=False).head(10)
pd.DataFrame({
    "product": names.reindex(gap.index).values,
    "cheapest at": wide.loc[gap.index].idxmin(axis=1).map(NAME).values,
    "lowest price (ARS)": wide.loc[gap.index].min(axis=1).round(0).values,
    "most expensive at": wide.loc[gap.index].idxmax(axis=1).map(NAME).values,
    "highest price (ARS)": wide.loc[gap.index].max(axis=1).round(0).values,
    "gap %": gap.round(1).values,
})"""),
md("""## Día against Jumbo, head to head

With only two shops the set of products in common is bigger, so the comparison covers more of the shelf."""),
code("""n_days = last["date"].nunique()
s = last[last["shop"].isin(["Dia", "Jumbo"])].groupby(["ean", "shop"])["price"].agg(["mean", "count"])
s = s[s["count"] >= -(-n_days // 2)]["mean"].unstack().dropna()
s = s[s.max(axis=1) <= 3 * s.min(axis=1)]
ratio = (s["Jumbo"] / s["Dia"] - 1) * 100
print(f"{len(s)} products sold at both Día and Jumbo (last 7 days).")
print(f"Same bill: Día ${s['Dia'].sum():,.0f}, Jumbo ${s['Jumbo'].sum():,.0f}, "
      f"Jumbo {(s['Jumbo'].sum() / s['Dia'].sum() - 1) * 100:.1f}% more expensive.")
print(f"Jumbo is more expensive on {(ratio > 0).mean():.0%} of them; the median product costs {ratio.median():.1f}% more at Jumbo.")"""),
md("""## What this does and does not say

- It compares **online prices** of the chains' websites, with the promotions anyone can get. It does not include card or loyalty discounts that depend on who you are.
- It uses only products sold at all the shops compared, by barcode. A shop's own brand cannot be compared this way.
- Prices are mostly those of **Greater Buenos Aires**; shops in other provinces can differ.
- Jumbo usually sells in larger, richer neighbourhoods, and the gap is about price, not about quality: the products are identical.

---

**La Canasta** publishes this ranking every week, and a daily price index weighted with INDEC's official weights, about two weeks before the official figure: **[lacanastaindex.com](https://lacanastaindex.com)**

If you use the data, please credit *"La Canasta, by Ramon Pepa (lacanastaindex.com)"*. License CC BY 4.0."""),
]
nb = nbf.v4.new_notebook(cells=cells, metadata={"kernelspec": {"name": "python3", "display_name": "Python 3", "language": "python"},
                                                 "language_info": {"name": "python"}})
os.makedirs(OUT, exist_ok=True)
nbf.write(nb, os.path.join(OUT, "cheapest-supermarket-argentina.ipynb"))
json.dump({
    "id": "ramonpepa/which-supermarket-is-cheapest-in-argentina",
    "title": "Which supermarket is cheapest in Argentina?",
    "code_file": "cheapest-supermarket-argentina.ipynb",
    "language": "python",
    "kernel_type": "notebook",
    "is_private": False,
    "enable_gpu": False,
    "enable_internet": False,
    "dataset_sources": ["ramonpepa/la-canasta-daily-supermarket-prices"],
    "competition_sources": [],
    "kernel_sources": [],
    "keywords": ["economics", "retail and shopping", "food", "data visualization"],
}, open(os.path.join(OUT, "kernel-metadata.json"), "w"), indent=1)
print("Wrote", OUT)
