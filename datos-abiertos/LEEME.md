# La Canasta: precios diarios de supermercados en Argentina

**Web:** https://lacanastaindex.com
**Datos actualizados todos los días:** https://lacanastaindex.com/metodo.html#datos
**DOI:** https://doi.org/10.5281/zenodo.23856045
**Autor:** Ramon Pepa
**Licencia:** CC BY 4.0 (uso libre, citando la fuente: "La Canasta, lacanastaindex.com")

*English below.*

## Qué es

La Canasta es un índice diario e independiente de precios de supermercados en Argentina. Todos los días, un programa lee los precios online de Carrefour, Jumbo, ChangoMás, Día y Coto. Con 1.111 productos de 45 tipos básicos (carne, leche, pan, yerba, aceite, limpieza y más) calcula un índice ponderado con las ponderaciones oficiales del INDEC (ENGHo 2004/05, Gran Buenos Aires).

Esta versión cubre del **{FIRST}** al **{LAST}** ({DAYS} días, {ROWS} precios).

## Archivos

| Archivo | Qué tiene |
|---|---|
| `precios_diarios.csv` | Todos los precios recolectados, todos los días, en todos los súper. |
| `canasta.csv` | Los productos que sigue el índice, con su código de barras (EAN) y desde qué día cuentan. |
| `ponderaciones.csv` | Los grupos del INDEC, su gasto en la ENGHo 2004/05 y qué tipos de producto incluye cada uno. |
| `indice_diario.csv` | El índice de cada día (promedio del 24 al 30/10/2026 = 100), en total y por supermercado, con precio pagado y precio de lista. |
| `indice_por_grupo.csv` | El índice de cada grupo de productos, cada día. |
| `inflacion_mensual.csv` | Promedios mensuales y la variación de cada mes. |
| `precios_excluidos.csv` | Precios que la revisión diaria dejó afuera del índice, con el motivo. |

## Columnas de `precios_diarios.csv`

| Columna | Qué es |
|---|---|
| `date` | Fecha en Argentina (AAAA-MM-DD). |
| `shop` | Supermercado: Carrefour, Jumbo, ChangoMas, Dia, Coto. |
| `search` | Búsqueda con la que se encontró el producto ("basket" = buscado directo por ser de la canasta). |
| `sku_id` | Código del producto en la web de ese súper. |
| `ean` | Código de barras. El mismo EAN en dos súper es el mismo producto. |
| `name`, `brand`, `category` | Nombre, marca y categoría, tal como los muestra el súper. |
| `unit`, `unit_multiplier` | Unidad de venta y multiplicador (por ejemplo, productos por kg). |
| `price` | Precio que paga cualquiera en la web ese día, con las promociones abiertas a todos. Sin descuentos bancarios ni de tarjetas. |
| `list_price` | Precio de lista (sin promoción). Vacío en Jumbo, porque su web no muestra un precio de lista real; por eso el índice sin promociones usa Carrefour, ChangoMás y Día. |
| `available` | True si había stock. |
| `basket_type` | Tipo de producto si está en la canasta del índice; "watch:..." si está en observación. |
| `extra` | Datos adicionales de algunos súper (JSON). |

## Cómo se calcula el índice

1. Cada día, el precio de cada producto se compara con el último día en que tuvo stock. Mismo súper, mismo producto.
2. Se promedian los productos de cada tipo (media geométrica, cada súper con el mismo peso).
3. Se promedian los tipos dentro de cada grupo del INDEC.
4. Los grupos se combinan con las ponderaciones del INDEC.
5. Los días se encadenan. Un precio que se triplica o cae a un tercio de un día al otro se trata como error.

La canasta tiene 1.111 productos de 45 tipos (hasta diez por tipo y súper). Se ampliaron el 1/11/2026 y el 6/11/2026 (carne vacuna, yogur, galletitas, suprema de pollo, y de cinco a diez productos por tipo y súper) y cada vez el índice se recalculó desde el primer día con los precios guardados. Coto se recolecta pero todavía no cuenta en el índice. Metodología completa: https://lacanastaindex.com/metodo.html

## Cómo citarlo

Pepa, R. (2026). *La Canasta: precios diarios de supermercados en Argentina* [Dataset]. https://doi.org/10.5281/zenodo.23856045 · https://lacanastaindex.com

---

# La Canasta: daily supermarket prices in Argentina

**Website:** https://lacanastaindex.com
**Data, updated every day:** https://lacanastaindex.com/metodo.html#datos
**DOI:** https://doi.org/10.5281/zenodo.23856045
**Author:** Ramon Pepa
**License:** CC BY 4.0 (free to use with credit: "La Canasta, lacanastaindex.com")

## What it is

La Canasta is an independent daily price index of Argentine supermarkets. Every day a program reads the online prices of Carrefour, Jumbo, ChangoMás, Día and Coto. Using 1,111 products of 45 basic kinds (beef, milk, bread, yerba, oil, cleaning and more) it calculates an index weighted with INDEC's official weights (ENGHo 2004/05, Greater Buenos Aires).

This version covers **{FIRST}** to **{LAST}** ({DAYS} days, {ROWS_EN} prices).

## Files

- `precios_diarios.csv`: every price collected, every day, at every shop (columns explained above: `price` is the price anyone pays online that day with open promotions; `list_price` is the regular price, empty for Jumbo because its site shows no real list price; `ean` is the barcode).
- `canasta.csv`: the products the index follows, with barcode and the day they start counting.
- `ponderaciones.csv`: INDEC groups, their 2004/05 spending and the product kinds in each.
- `indice_diario.csv`: daily index (average of 24 to 30 Oct 2026 = 100), overall and per shop, price paid and regular price.
- `indice_por_grupo.csv`: each group's index, every day.
- `inflacion_mensual.csv`: monthly averages and each month's change.
- `precios_excluidos.csv`: prices the daily review left out of the index, with the reason.

## Method

Each product's price is compared with the last day it was in stock (same shop, same product). Products are averaged within each kind (geometric mean, each shop weighted equally), kinds within each INDEC group, and groups with INDEC's weights. Days are chained. The basket has 1,111 products of 45 kinds (up to ten per kind and shop); it was widened on 1 Nov 2026 and 6 Nov 2026 (beef, yoghurt, biscuits, chicken fillets, and from five to ten products per kind and shop) and each time the index was recalculated from the first day with the saved prices. Coto is collected but not yet in the index. Full method: https://lacanastaindex.com/metodo.html

## How to cite

Pepa, R. (2026). *La Canasta: daily supermarket prices in Argentina* [Dataset]. https://doi.org/10.5281/zenodo.23856045 · https://lacanastaindex.com
