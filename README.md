# La Canasta 🛒

**A daily, open supermarket price index for Argentina.**

*Un índice diario y abierto de precios de supermercados en Argentina.*

---

## What it is

Every day, La Canasta automatically collects the online prices of thousands of everyday products from Argentina's five biggest supermarket chains, and uses them to measure how fast prices are rising.

Official inflation (INDEC) is published once a month, about two weeks after the month ends. La Canasta measures supermarket prices **every day** and publishes its monthly figure **before** the official one.

## Supermarkets covered

| Chain | Collected since | In the index |
|---|---|---|
| Carrefour | 24 Oct 2026 | ✅ |
| Jumbo | 24 Oct 2026 | ✅ |
| ChangoMás | 24 Oct 2026 | ✅ |
| Día | 24 Oct 2026 | ✅ |
| Coto | 24 Oct 2026 | ⏳ Not yet (see below) |

About **10,500 prices a day**.

## The basket

The index follows **672 everyday products of 45 kinds** (up to five per kind and shop; widened on 1 and 6 November 2026, each time recalculated from the first day with the saved prices), listed in [`basket.csv`](basket.csv): beef, bread and cereals, dairy and eggs, oil, fruit and vegetables, chicken, sugar, yerba, coffee and tea, drinks, cleaning and personal care.

Each product is followed in its own shop, with its own code. Many are exactly the same item in every shop (same barcode); fresh fruit, vegetables, eggs and some milks are each shop's own version.

Each shop is only ever compared **with itself, over time**.

Products that could not be measured reliably across shops were left out. Meat cuts and chimichurri are being collected and will only be added once their prices prove reliable.

## Which price is used

1. **Main index: the price anyone pays on the website that day**, including promotions open to everyone.
2. **Not included:** discounts that only some people can get, such as bank card offers, loyalty cards, or "buy 2" deals (2x1, second unit off).
3. **Second index: the regular price** (before promotions), to show how much promotions change the picture.
4. **Out of stock:** the product is skipped that day. Prices are **never guessed**.
5. **Prices that look wrong are left out.**

## Why Coto is not in the index yet

Coto's website search system still contains **old prices for some products** (for example, a 1 kg yoghurt at $140). Until real and old prices can be told apart reliably, Coto's data is collected but **not used in the index**.

## How the index is calculated

1. Every day, each basket product's price is compared with the last day it was in stock. Same shop, same product.
2. The products of each kind are averaged (geometric mean, each shop counting the same), then the kinds are averaged inside each INDEC group (bread and cereals, dairy and eggs, fruit...).
3. Groups are combined using **INDEC's official weights**: how much households in Greater Buenos Aires spend on each group, from INDEC's 2004/05 household spending survey (the same one INDEC still uses for official inflation).
4. The days are chained together. **The average of the first full week (24 to 30 October 2026) = 100**, not a single day: 24 October was a Saturday full of weekend promotions.
5. A price that triples or falls to a third overnight is treated as a data error and left out. Every case is listed in [`index/checks.txt`](index/checks.txt).

**Monthly inflation:** the average of the month compared with the average of the month before, like INDEC. Because collection started on 24 October, the first full comparison is December vs November. For November only, each product's average price in the last 7 days of the month (24 to 30 November) is compared with the same days of October (24 to 30 October), so both sides have the same weekdays. Full method: https://lacanastaindex.com/metodo.html

**Results** are in the [`index`](index) folder: `daily.csv` (the index every day, overall and per shop), `groups.csv` (each group), `monthly.csv` (monthly inflation).

### Known limits

- **Meat:** only chicken is covered so far. Beef is not yet included.
- **Personal care** (shampoo, toothpaste, soap, toilet paper) is collected but left out of the headline number until INDEC's official weight for it is found.
- **Newer weights:** a second version using INDEC's 2017/18 spending survey will be added once the official figures are found.

## The data is open

Every day's prices are in the [`data`](data) folder, one file per day (`YYYY-MM-DD.csv.gz`). Anyone can download and use them.

| Column | Meaning |
|---|---|
| `date` | Day the price was collected |
| `shop` | Supermarket |
| `sku_id` | The supermarket's own product ID |
| `ean` | Barcode (not available for Coto) |
| `name`, `brand` | Product |
| `price` | Price on the website that day, in Argentine pesos (promotions open to everyone included) |
| `list_price` | Regular price, before promotions. Empty for Jumbo from 4 Nov 2026; in older files Jumbo's value is NOT a list price (it is the price without VAT, times 100), so do not use it |
| `available` | In stock or not |
| `basket_type` | Which basket product this is (empty if not in the basket) |

For Coto, which prices each store separately, `price` is the typical (median) price across its stores.

## How it works

1. A script runs every day on GitHub, at 10:23 Argentina time.
2. It searches each supermarket's website for 42 product groups.
3. It checks every basket product directly, so none are missed.
4. It saves every result with its price and barcode.

## Status

- ✅ Daily collection from all 5 chains (since 24 October 2026)
- ✅ Daily index with 672 products, checked every day by an independent recalculation
- ✅ Website: https://lacanastaindex.com
- ✅ Open data on Kaggle and Zenodo (DOI [10.5281/zenodo.23856045](https://doi.org/10.5281/zenodo.23856045))
- 🔜 First monthly report: **1 December 2026** (November)
- ⏳ Coto: collected, not in the index yet

## Notes

- La Canasta is independent. It is not linked to any supermarket, INDEC or the government.
- It only collects publicly available prices, once a day, slowly.
- Built with the help of AI tools for parts of the code. All decisions, checks and analysis are my own.

---

Built by Ramon.
