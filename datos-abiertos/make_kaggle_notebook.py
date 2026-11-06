# Builds the example notebook for the La Canasta dataset on Kaggle.
#   python datos-abiertos/make_kaggle_notebook.py      -> datos-abiertos/la-canasta-kaggle-notebook.ipynb
# On Kaggle it finds the files under /kaggle/input by itself. Elsewhere, set LC_DATA to the folder
# with the unzipped files (precios_diarios.csv, indice_diario.csv, ...).
import nbformat as nbf

md, code = nbf.v4.new_markdown_cell, nbf.v4.new_code_cell
NAVY, CELESTE, SUN = "#2B3B5C", "#7FB1C6", "#D98A2B"

cells = [
md("""# La Canasta: Argentine supermarket prices, day by day
*Precios de supermercados en Argentina, día por día*

**La Canasta** is an independent daily price index of Argentine supermarkets. Every day a program reads the online prices of **Carrefour, Jumbo, ChangoMás, Día and Coto**, and turns 672 everyday products (beef, milk, bread, yerba, oil, cleaning products and more) into one index, weighted with INDEC's official household spending weights.

This notebook shows what you can do with the data:

1. The daily index: the price people pay vs the list price
2. Each supermarket compared with itself
3. Which product groups moved most
4. How many products are on promotion, day by day
5. **Which supermarket is cheapest** for exactly the same products
6. The products whose prices changed most

Website, method and the latest data: **[lacanastaindex.com](https://lacanastaindex.com)** · DOI: [10.5281/zenodo.23856045](https://doi.org/10.5281/zenodo.23856045) · License: CC BY 4.0 (credit: "La Canasta, lacanastaindex.com")"""),
code("""import glob, os
import pandas as pd
import matplotlib.pyplot as plt

# Find the files (on Kaggle they are under /kaggle/input)
def find(name):
    roots = [os.environ.get("LC_DATA", ""), "/kaggle/input", "."]
    for r in roots:
        if r:
            hits = glob.glob(os.path.join(r, "**", name), recursive=True)
            if hits:
                return hits[0]
    raise FileNotFoundError(name)

prices = pd.read_csv(find("precios_diarios.csv"), dtype={"sku_id": str, "ean": str}, low_memory=False)
basket = pd.read_csv(find("canasta.csv"), dtype={"sku_id": str, "ean": str})
daily = pd.read_csv(find("indice_diario.csv"), parse_dates=["date"])
groups = pd.read_csv(find("indice_por_grupo.csv"), parse_dates=["date"])
prices["date"] = pd.to_datetime(prices["date"])

NAVY, CELESTE, SUN, RED, GREEN = "#2B3B5C", "#7FB1C6", "#D98A2B", "#C0392B", "#2E7D5B"
SHOP_NAME = {"Carrefour": "Carrefour", "Jumbo": "Jumbo", "ChangoMas": "ChangoMás", "Dia": "Día", "Coto": "Coto"}
plt.rcParams.update({"figure.figsize": (11, 4.5), "axes.spines.top": False, "axes.spines.right": False,
                     "axes.grid": True, "grid.alpha": 0.25, "font.size": 11})
print("Files loaded.")"""),
md("""## What is in the data
`precios_diarios.csv` has **every price collected, every day, at every shop**: the price paid that day (`price`, with the promotions open to everyone), the list price (`list_price`), the barcode (`ean`) and whether it was in stock. `canasta.csv` lists the products the index follows."""),
code("""in_stock = prices[prices["available"] == True]
summary = pd.DataFrame({
    "days": [prices["date"].nunique()],
    "first day": [prices["date"].min().date()],
    "last day": [prices["date"].max().date()],
    "prices collected": [len(prices)],
    "basket products": [len(basket)],
})
display(summary)
display(in_stock.groupby("shop").size().rename("prices in stock").to_frame().T)"""),
md("""## 1. The daily index
Two lines: **what people pay** (promotions included) and the **list price** (no promotions). The gap between them is the effect of promotions. Here both are shown with the **first full week = 100**, so the start does not depend on one day's offers (24 October 2026 was a Saturday full of weekend promotions).

Jumbo shows no real list price on its website (its `list_price` field is the price without VAT, times 100), so the list-price index uses Carrefour, ChangoMás and Día."""),
code("""first_week = daily["date"] < daily["date"].min() + pd.Timedelta(days=7)
idx = daily.set_index("date")[["index_paid", "index_regular"]]
idx = idx / idx[first_week.values].mean() * 100

ax = idx["index_paid"].plot(color=NAVY, lw=2.6, marker="o", ms=4, label="Price paid (promotions included)")
idx["index_regular"].plot(ax=ax, color="grey", lw=2, ls="--", label="List price (no promotions)")
ax.axhline(100, color=CELESTE, lw=1)
ax.set_title("La Canasta index (average of the first week = 100)", loc="left", color=NAVY, fontsize=14)
ax.set_xlabel(""); ax.legend(frameon=False)
plt.show()
print(f"Latest day: price paid {idx['index_paid'].iloc[-1]:.2f}, list price {idx['index_regular'].iloc[-1]:.2f}")"""),
md("""## 2. Each supermarket compared with itself
Each shop's index only compares that shop's prices with its own prices on earlier days. It says how fast prices move in each chain, not which chain is cheaper (that is section 5)."""),
code("""shop_cols = [c for c in daily.columns if c.endswith("_paid") and c != "index_paid"]
shops = daily.set_index("date")[shop_cols]
shops = shops / shops[first_week.values].mean() * 100
colors = [NAVY, SUN, CELESTE, GREEN, RED]
ax = None
for c, col in zip(shop_cols, colors):
    ax = shops[c].plot(ax=ax, lw=2.2, color=col, label=SHOP_NAME.get(c[:-5], c[:-5]))
ax.axhline(100, color="grey", lw=0.8)
ax.set_title("Price paid, each supermarket (first week = 100)", loc="left", color=NAVY, fontsize=14)
ax.set_xlabel(""); ax.legend(frameon=False, ncol=4)
plt.show()"""),
md("""## 3. Which product groups moved most
The groups are INDEC's (bread and cereals, dairy and eggs, chicken...). Change of the **last 7 days' average** against the **first week**."""),
code("""g = groups.pivot_table(index="date", columns="group_name", values="index_paid")
first = g[g.index < g.index.min() + pd.Timedelta(days=7)].mean()
last = g.tail(7).mean()
change = ((last / first - 1) * 100).sort_values()
ax = change.plot.barh(color=[RED if v > 0 else GREEN for v in change], figsize=(10, 5.5))
for i, v in enumerate(change):
    ax.text(v + (0.1 if v >= 0 else -0.1), i, f"{v:+.1f}%", va="center", ha="left" if v >= 0 else "right", fontsize=10)
ax.axvline(0, color="grey", lw=0.8)
pad = max(0.6, change.abs().max() * 0.25)
ax.set_xlim(min(0, change.min()) - pad, max(0, change.max()) + pad)
ax.set_title("Change by group: last 7 days vs first week (price paid)", loc="left", color=NAVY, fontsize=14)
ax.set_ylabel(""); plt.show()"""),
md("""## 4. How many products are on promotion, day by day
A basket product is "on promotion" when the price paid is at least 1% under its list price. Promotions switch on and off every week, which is why comparing single days misleads and La Canasta compares whole weeks."""),
code("""b = basket[["shop", "sku_id"]].assign(in_basket=True)
bp = in_stock.merge(b, on=["shop", "sku_id"])
bp = bp[(bp["shop"] != "Jumbo") & (bp["list_price"] > 0)]
bp["on_promo"] = bp["price"] < bp["list_price"] * 0.99
promo = bp.groupby(["date", "shop"])["on_promo"].mean().unstack() * 100
ax = None
for s, col in zip(promo.columns, [NAVY, SUN, CELESTE]):
    ax = promo[s].plot(ax=ax, lw=2.2, marker="o", ms=4, color=col, label=SHOP_NAME.get(s, s))
ax.set_ylabel("% of basket products on promotion")
ax.set_title("Share of basket products on promotion", loc="left", color=NAVY, fontsize=14)
ax.set_xlabel(""); ax.legend(frameon=False)
plt.show()
display(bp.assign(weekday=bp["date"].dt.day_name()).groupby("weekday")["on_promo"].mean().mul(100).round(1)
          .reindex(["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"]).dropna().rename("% on promotion").to_frame().T)"""),
md("""## 5. Which supermarket is cheapest?
The fairest comparison: **exactly the same products** (same barcode, sold by the unit) at the four shops in the index. Each shop's price is its **average over the last 7 days** (a product counts if every shop had it in stock at least half of those days), so one day's offers or a shop's bad day do not decide it."""),
code("""last_day = prices["date"].max()
week = in_stock[(in_stock["date"] > last_day - pd.Timedelta(days=7)) & in_stock["shop"].isin(["Carrefour", "Jumbo", "ChangoMas", "Dia"])
                & in_stock["ean"].notna() & (in_stock["unit"].str.lower() == "un") & (in_stock["unit_multiplier"] == 1)]
n_days = week["date"].nunique()
stats = week.groupby(["ean", "shop"])["price"].agg(["mean", "count"])
stats = stats[stats["count"] >= -(-n_days // 2)]
wide = stats["mean"].unstack().dropna()
day = week
wide = wide[wide.max(axis=1) <= 3 * wide.min(axis=1)]   # leave out obvious mismatches
totals = wide.sum().sort_values()
pct = (totals / totals.min() - 1) * 100
ax = totals.rename(SHOP_NAME).plot.bar(color=[GREEN] + [CELESTE] * (len(totals) - 1), rot=0, figsize=(9, 4.5))
for i, (t, p) in enumerate(zip(totals, pct)):
    ax.text(i, t, f"${t:,.0f}\\n" + ("cheapest" if p == 0 else f"+{p:.1f}%"), ha="center", va="bottom", fontsize=10)
ax.set_ylim(0, totals.max() * 1.15)
ax.set_title(f"The same {len(wide)} products at the 4 shops, average of the last 7 days (to {last_day.date()})", loc="left", color=NAVY, fontsize=13)
ax.set_ylabel("Total cost (ARS)"); plt.show()

names = day.drop_duplicates("ean").set_index("ean")["name"]
gap = (wide.max(axis=1) / wide.min(axis=1) - 1).mul(100).sort_values(ascending=False).head(8)
display(pd.DataFrame({"product": names.reindex(gap.index), "cheapest": wide.loc[gap.index].idxmin(axis=1).map(SHOP_NAME),
                      "most expensive": wide.loc[gap.index].idxmax(axis=1).map(SHOP_NAME), "gap %": gap.round(1)}))"""),
md("""## 6. The products whose prices changed most
Each basket product, first day vs latest day, same shop. When the list price did not move, the jump is a promotion starting or ending, not a real price rise."""),
code("""bk = in_stock.merge(basket[["shop", "sku_id", "product_type"]], on=["shop", "sku_id"])
f = bk[bk["date"] == bk["date"].min()].set_index(["shop", "sku_id"])
l = bk[bk["date"] == bk["date"].max()].set_index(["shop", "sku_id"])
both = f.join(l, lsuffix="_first", rsuffix="_last", how="inner")
both["change %"] = (both["price_last"] / both["price_first"] - 1) * 100
both["list price moved"] = (both["list_price_last"] - both["list_price_first"]).abs() > 1
cols = ["name_last", "price_first", "price_last", "change %", "list price moved"]
top = both.sort_values("change %")
print("Biggest rises"); display(top.tail(8)[::-1][cols].round(1))
print("Biggest falls"); display(top.head(8)[cols].round(1))"""),
md("""## Ideas for your own analysis
- How fast do prices react after a big change in the peso?
- Do promotions follow a weekly pattern? Which shop runs the most?
- How different are prices for the same barcode across chains, and does the gap last?
- Compare La Canasta with INDEC's official food inflation each month.

## How to cite
Pepa, R. (2026). *La Canasta: precios diarios de supermercados en Argentina* [Dataset]. https://doi.org/10.5281/zenodo.23856045 · https://lacanastaindex.com

Full method, weekly and monthly reports: **[lacanastaindex.com](https://lacanastaindex.com)**"""),
]

nb = nbf.v4.new_notebook(cells=cells, metadata={"kernelspec": {"name": "python3", "display_name": "Python 3", "language": "python"},
                                               "language_info": {"name": "python"}})
out = "datos-abiertos/la-canasta-kaggle-notebook.ipynb"
nbf.write(nb, out)
print("Wrote", out)
