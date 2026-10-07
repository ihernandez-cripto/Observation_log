# Script: extrae_utrnno.py

Este script busca líneas de texto específicas dentro de archivos de logs de un módulo SVFE y genera un archivo CSV con la información asociada a cada coincidencia.

Su objetivo principal es localizar un error determinado y devolver, para cada aparición, el `orgdev`, el `utrnno`, la fecha/hora del contexto y la línea exacta del archivo donde se detectó el error.

## Requisitos

- Python 3.x
- Los archivos de log deben estar guardados en carpetas organizadas por módulo.
- No requiere librerías externas adicionales.

## Cómo ejecutar el script

Desde la carpeta donde está `extrae_utrnno.py`, ejecuta:

```bash
python extrae_utrnno.py
```

El programa mostrará un menú con los módulos disponibles y te pedirá:

1. El número del módulo que deseas revisar.
2. El texto del error que quieres buscar.

Entonces buscará ese texto en los archivos del módulo seleccionado.

## Estructura de carpetas que el usuario debe crear

El script asume que la carpeta del script contiene una serie de directorios, uno por cada módulo. La estructura es esta:

```text
Monitoring/
│
├── extrae_utrnno.py
├── atmi00/
│   ├── atmi00_08281.Oct1.1
│   ├── atmi00_08284.Oct1.1
│   ├── atmi00_08285.Oct1.1
│   └── ...
│
├── hostspec1/
│   ├── hostspec1_...txt
│   └── ...
│
├── OTRO/
│   ├── log_1.txt
│   ├── log_2.txt
│   └── ...
│
└── otros módulos...
```

### Convención importante

El script usa los nombres de carpeta y los prefijos de archivo para identificar cada módulo:

- Si eliges un módulo del menú, por ejemplo `atmi00_`, se espera que exista una carpeta llamada `atmi00`.
- Dentro de esa carpeta debe haber archivos cuyo nombre empiece con el prefijo del módulo, por ejemplo:
  - `atmi00_08281.Oct1.1`
  - `atmi00_08284.Oct1.1`
- Si seleccionas la opción `OTRO`, el script buscará todos los archivos que estén dentro de la carpeta `OTRO`.

### Módulos incluidos por defecto

El script ya define esta lista:

```python
MODULOS = [
    "atmi00_",
    "atmi_diebold_",
    "crout00.",
    "epayint_",
    "hostspec1_",
    "hstint_",
    "nwint_",
    "racal_",
    "stdauth_",
    "tcpcomms1.",
    "txrout_",
]
```

Esto significa que, para cada módulo, el usuario debe crear una carpeta con el nombre correspondiente sin el último caracter especial del prefijo:

- `atmi00_` -> carpeta `atmi00`
- `hostspec1_` -> carpeta `hostspec1`
- `crout00.` -> carpeta `crout00`
- `tcpcomms1.` -> carpeta `tcpcomms1`
- `OTRO` -> carpeta `OTRO`

### Ejemplo práctico

Si el usuario desea inspeccionar el módulo `atmi00_`, entonces debe crear esta estructura:

```text
Monitoring/
└── atmi00/
    ├── atmi00_08281.Oct1.1
    ├── atmi00_08282.Oct1.1
    └── atmi00_08283.Oct1.1
```

Y luego ejecutar el script. Al elegir el módulo `1`, el programa buscará en la carpeta `atmi00` y solo tomará los archivos que comiencen con `atmi00_`.

## ¿Qué hace exactamente la búsqueda?

La lógica del script es la siguiente:

### 1. Selección del módulo

El script presenta un menú con todos los módulos:

```python
print("Menú Módulos SVFE:")
for numero, modulo in enumerate(MODULOS, start=1):
    print(f"{numero}. {modulo}")
print(f"{len(MODULOS) + 1}. OTRO")
```

Después de que el usuario elige un número, el programa calcula la ruta física en la que debe buscar.

- Si la opción es `OTRO`, usa esta ruta:
  ```python
  ROOT = Path(__file__).resolve().parent / "OTRO"
  ```
- Si no es `OTRO`, construye el nombre de la carpeta eliminando el último carácter del prefijo:
  ```python
  nombre_modulo = modulo[:-1]
  ROOT = Path(__file__).resolve().parent / folder_name
  ```

Si la carpeta no existe, el script termina con un error:

```python
raise NotADirectoryError(f"No se encontró la carpeta del módulo: {ROOT}")
```

### 2. Búsqueda del texto del error

El usuario escribe la cadena de texto que desea localizar, por ejemplo:

```text
TIMEOUT
ERROR 0xA4
Invalid token
```

Ese texto se convierte en una expresión regular con búsqueda sin distinguir mayúsculas/minúsculas:

```python
TARGET_RE = re.compile(re.escape(linea_error), re.IGNORECASE)
```

Esto significa que la búsqueda no es sensible a mayúsculas/minúsculas y que el texto se busca como una cadena literal, no como una expresión compleja.

### 3. Lectura de cada archivo

El script recorre cada archivo del directorio correspondiente. Hay dos casos:

- `OTRO`: toma todos los archivos del directorio `OTRO`.
- Módulo normal: toma solo los archivos que coinciden con el prefijo del módulo.

```python
if nombre_modulo == "OTRO":
    archivos = sorted(file_path for file_path in ROOT.iterdir() if file_path.is_file())
else:
    archivos = sorted(ROOT.glob(f"{modulo}*"))
```

### 4. Extracción de metadatos del contexto

Para cada línea del archivo, el script intenta encontrar tres valores que son relevantes para el análisis:

```python
ORGDEV_RE = re.compile(r"orgdev:\s*(\d+)", re.IGNORECASE)
UTRNNO_RE = re.compile(r"utrnno:\s*(\d+)", re.IGNORECASE)
DATE_RE = re.compile(r"Local date and time\s*:\s*(\d{2}/\d{2}/\d{4}\s+\d{2}:\d{2}:\d{2})", re.IGNORECASE)
```

- `orgdev` se busca con una línea que contenga `orgdev: 1234`
- `utrnno` se busca con una línea que contenga `utrnno: 5678`
- Fecha/hora se busca con texto como:
  ```text
  Local date and time : 28/10/2024 14:23:01
  ```

El script va guardando el último valor encontrado para cada uno de estos campos mientras recorre el archivo.

### 5. Cómo se decide que una coincidencia es válida

Cuando una línea del archivo coincide con el texto de error buscado, el script verifica si ya existen valores válidos de `orgdev`, `utrnno` y `fecha_hora` previamente capturados en ese mismo archivo:

```python
if TARGET_RE.search(line):
    if ultimo_orgdev and ultimo_utrnno and ultima_fecha_hora:
        filas.append({
            "archivo": file_path.name,
            "orgdev": ultimo_orgdev,
            "utrnno": ultimo_utrnno,
            "fecha_hora": ultima_fecha_hora,
            "linea_error": line_no,
        })
```

Esto significa que no se toma como coincidencia solo la línea del error; la línea debe ir acompañada de contexto válido previamente detectado en el archivo.

### 6. Salida generada

Si se encontraron coincidencias, se genera un CSV con el nombre:

```text
<nombre_modulo>_resultado.csv
```

Por ejemplo:

```text
atmi00_resultado.csv
```

O si el módulo es `OTRO`:

```text
OTRO_resultado.csv
```

El archivo CSV contiene estas columnas:

- `archivo`
- `orgdev`
- `utrnno`
- `fecha_hora`
- `linea_error`

Y luego se ordena por:

1. `fecha_hora`
2. `archivo`
3. `linea_error`

## Ejemplo de resultado

```csv
archivo,orgdev,utrnno,fecha_hora,linea_error
atmi00_08281.Oct1.1,123,456,28/10/2024 14:23:01,348
atmi00_08281.Oct1.1,123,456,28/10/2024 14:39:18,502
```

Cada fila indica:

- qué archivo tuvo la coincidencia,
- qué `orgdev` estaba activo en ese contexto,
- qué `utrnno` se estaba usando,
- en qué fecha y hora ocurrió,
- y en qué número de línea del archivo apareció el error.

## Notas importantes

- El archivo se abre con codificación `latin-1` y se usa `errors="replace"`, para tolerar caracteres especiales comunes en logs.
- La búsqueda es sensible a mayúsculas y minúsculas solamente si se elimina `re.IGNORECASE` en el código.
- Si un archivo no contiene valores de `orgdev`, `utrnno` o fecha antes del error, esa coincidencia se omite.
- Si no hay resultado, el script muestra:
  ```text
  No se encontraron coincidencias.
  ```

## Recomendación de uso

La forma más segura de usarlo es esta:

1. Crear una carpeta por módulo dentro de la misma ubicación del script.
2. Guardar los archivos de log en esa carpeta.
3. Ejecutar el script.
4. Elegir el módulo correspondiente.
5. Ingresar el texto exacto del error que se desea localizar.
6. Revisar el CSV generado para identificar la transacción y la fecha/hora del incidente.

## Resumen rápido

El script:

- pregunta qué módulo revisar,
- valida que exista la carpeta del módulo,
- busca un texto específico en todos los archivos del módulo,
- captura los datos de contexto (`orgdev`, `utrnno`, fecha/hora) previos a cada coincidencia,
- exporta los resultados en un CSV listo para revisar.
