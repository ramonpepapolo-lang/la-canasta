# Revisión diaria de precios dudosos

Cada noche un agente corre `python revisar.py` y mira los precios que cambiaron más de 25% o que movieron
el índice más de 0,25 puntos. Decide con estas reglas. **Ante la duda, NO se excluye.**

## Reglas

**A. Error de dato** → excluir `both` (pagado y lista) esos días.
- El nombre cambió a otro producto, otro tamaño u otra marca.
- El precio salta x10 o /10, x100 o /100.
- Pasó de precio por kilo a precio por unidad (o al revés).

**B. Promo que el súper no marcó** → excluir solo `regular` esos días (el precio pagado sí cuenta, porque es real).
- El precio de lista es igual al pagado (el súper no muestra precio tachado), y
- ese precio sale de su nivel durante 1 a 3 días (típico fin de semana) y después vuelve, o queda en otro nivel estable, y
- los mismos productos en los otros súper no se movieron igual.

**C. Todo lo demás es un cambio real** → no se toca. Las promos marcadas (lista ≠ pagado) que empiezan o terminan son reales.

## Cómo se registra

Una línea por día y producto en `notas/excluir.csv`:

`date,shop,sku_id,kind,reason`

- `kind`: `paid`, `regular` o `both`.
- `reason`: en español, con los precios y por qué se aplicó la regla.

Nunca se borra una línea vieja. Nunca se inventa ni se reemplaza un precio: el producto simplemente no se compara ese día.

## Cosas conocidas

- Jumbo: el campo de "precio de lista" no es un precio de lista real (es el precio sin IVA multiplicado por 100). Para Jumbo, "sin promociones" = precio pagado. No es un error a excluir.
- Frutas y verduras se mueven mucho: un cambio grande en papa, tomate o banana suele ser real.
