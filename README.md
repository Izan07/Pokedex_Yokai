# Pokédex Yo-kai Watch

Aplicación web con Flask que lee la colección desde `data/yokais.json`. No necesita MongoDB Atlas, PokeAPI ni acceso a Internet para cargar los datos.

## Requisitos

- Python 3.10 o posterior

## Preparar y ejecutar en Windows PowerShell

Desde la carpeta del proyecto:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe app.py
```

Abre <http://127.0.0.1:5000/> en el navegador.

## Datos e imágenes

- La colección se guarda en `data/yokais.json`.
- La aplicación genera el identificador de ruta a partir del nombre. Si hay nombres repetidos, añade un sufijo numérico estable según el orden del JSON (`-2`, `-3`, etc.).
- Cada imagen se sirve en `/public/images/yokais/{slug}.jpg` y se guarda en `static/images/yokais/` con el nombre limpio del Yo-kai; los espacios se sustituyen por `_` y se eliminan prefijos numéricos.
- La lista de nombres, slugs, rutas esperadas y estado de las imágenes está en `data/yokai_images.csv`.
- El formulario de crear, editar y eliminar guarda cambios en el JSON local.

## Funciones

- Búsqueda por nombre, insensible a mayúsculas y acentos.
- Filtros por tipo, cantidad de tipos y rareza (incluida la opción sin categoría especial).
- Página de detalle accesible en `/yokai/{slug}`.
- La sección de debilidades y resistencias de cada ficha calcula los multiplicadores combinados de sus tipos desde la tabla estática `data/type_effectiveness.json`. En esa tabla se listan las relaciones no neutrales por tipo atacante; las relaciones omitidas equivalen a x1.
- Gráfico circular de apariciones por tipo en `/stats`, calculado con los tipos distintos de cada Yo-kai; un tipo repetido en `tipo1` y `tipo2` cuenta una sola vez. La leyenda muestra cantidades y las porciones, porcentajes.
- Rareza opcional en `data/yokais.json`: los únicos valores admitidos son `Clásicos`, `Merican`, `Leyenda Merican`, `Legendarios`, `Mítico` y `Leyenda Mística`. El campo puede omitirse o ser `null` para el resto; respeta mayúsculas, espacios y tildes.
- Cada entrada contiene `caracteristicas` con `PS`, `Ataque`, `Defensa`, `Ataque Especial`, `Defensa Especial` y `Velocidad`. Son enteros de 0 a 255; las entradas actuales empiezan en 0 y se pueden rellenar a mano o desde el formulario de edición.
- La ficha muestra cada característica con una barra proporcional a su valor. El bloque y la validación están en `templates/detail.html` y `app.py` (`STAT_FIELDS` y `normalize_characteristics`).

El gráfico se dibuja como SVG sin dependencia de una librería adicional. Sus cálculos y paleta están en `app.py` (`make_pie_slices` y `TYPE_COLORS`); su estructura y tooltip, en `templates/stats.html`.
