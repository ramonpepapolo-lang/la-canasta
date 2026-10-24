# La Canasta 🛒

**A daily, open supermarket price index for Argentina.**

*Un índice diario y abierto de precios de supermercados en Argentina.*

---

## What it is

Every day, La Canasta automatically collects the online prices of thousands of everyday products from Argentina's five biggest supermarket chains, and uses them to measure how fast prices are rising.

Official inflation (INDEC) is published once a month, about two weeks after the month ends. La Canasta measures supermarket prices **every day** and publishes its monthly figure **before** the official one.

## Supermarkets covered

| Chain | Since |
|---|---|
| Carrefour | 24 Oct 2026 |
| Coto | 24 Oct 2026 |
| Jumbo | 24 Oct 2026 |
| ChangoMás | 24 Oct 2026 |
| Día | 24 Oct 2026 |

About **9,500 prices a day**, across 36 product groups: dairy, bread and cereals, basics, meat, fruit and veg, drinks, cleaning and personal care.

## The data is open

Every day's prices are in the [`data`](data) folder, one file per day (`YYYY-MM-DD.csv.gz`). Anyone can download and use them.

| Column | Meaning |
|---|---|
| `date` | Day the price was collected |
| `shop` | Supermarket |
| `sku_id` | The supermarket's own product ID |
| `ean` | Barcode (not available for Coto) |
| `name`, `brand` | Product |
| `price` | Shelf price in Argentine pesos |
| `list_price` | Price before discounts |
| `available` | In stock or not |

For Coto, which prices each store separately, `price` is the typical (median) price across its stores.

## How it works

1. A script runs every day on GitHub, at 10:23 Argentina time.
2. It searches each supermarket's website for the same 36 product groups.
3. It saves every result with its price and barcode.
4. Products out of stock are recorded but left out of the index.

## Status

- ✅ Daily collection from all 5 chains
- 🔜 The index (method will be published here)
- 🔜 First monthly report

## Notes

- La Canasta is independent. It is not linked to any supermarket, INDEC or the government.
- It only collects publicly available prices, once a day, slowly.
- Built with the help of AI tools for parts of the code. All decisions, checks and analysis are my own.

---

Built by Ramon.
