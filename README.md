# Ofertómetro — datos

Precios diarios de supermercados de Argentina que usa [ofertometro.com.ar](https://ofertometro.com.ar).

- `productos.json`: ~1.000 productos con el precio en cada cadena (mediana entre sucursales), rango, promos y precio por provincia.
- `cadenas.json`: cadenas, sucursales por provincia e índice de precios (100 = precio típico).
- `canasta.json`: canasta fija de 25 productos y su total en cada cadena y provincia.
- `historial.json`: mediana nacional de cada producto y total de la canasta, día por día.
- `meta.json`: fecha de los datos.

Fuente: SEPA – Precios Claros, Secretaría de Comercio de la Nación ([datos.produccion.gob.ar](https://datos.produccion.gob.ar/dataset/sepa-precios)), licencia CC-BY 4.0. Procesado con `pipeline/actualizar.py`.
