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

The index follows **33 everyday products** (129 items across the shops), listed in [`basket.csv`](basket.csv): bread and cereals, dairy and eggs, oil, fruit and vegetables, chicken, sugar, yerba, coffee and tea, drinks, cleaning and personal care.

- **22 products are exactly the same item in every shop** (same barcode).
- **11 are each shop's own version** (for example fresh fruit, vegetables, eggs and milk), because these are sold under each shop's own codes.

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
| `list_price` | Regular price, before promotions |
| `available` | In stock or not |
| `basket_type` | Which basket product this is (empty if not in the basket) |

For Coto, which prices each store separately, `price` is the typical (median) price across its stores.

## How it works

1. A script runs every day on GitHub, at 10:23 Argentina time.
2. It searches each supermarket's website for 42 product groups.
3. It checks every basket product directly, so none are missed.
4. It saves every result with its price and barcode.

## Status

- ✅ Daily collection from all 5 chains
- ✅ Basket chosen
- 🔜 The index (method will be published here)
- 🔜 Website
- 🔜 First monthly report: **1 December 2026**

## Notes

- La Canasta is independent. It is not linked to any supermarket, INDEC or the government.
- It only collects publicly available prices, once a day, slowly.
- Built with the help of AI tools for parts of the code. All decisions, checks and analysis are my own.

---

Built by Ramon.
