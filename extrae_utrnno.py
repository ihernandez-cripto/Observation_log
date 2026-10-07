import csv
import re
from pathlib import Path

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

print("Menú Módulos SVFE:")
for numero, modulo in enumerate(MODULOS, start=1):
    print(f"{numero}. {modulo}")
print(f"{len(MODULOS) + 1}. OTRO")
print(f"{len(MODULOS) + 2}. Cancelar")

while True:
    seleccion = input("Seleccione el módulo que desea verificar: ").strip()
    if seleccion.isdigit() and 1 <= int(seleccion) <= len(MODULOS) + 2:
        break
    print(f"Selección inválida. Ingrese un número entre 1 y {len(MODULOS) + 2}.")

if int(seleccion) == len(MODULOS) + 2:
    print("Operación cancelada.")
    raise SystemExit(0)

if int(seleccion) == len(MODULOS) + 1:
    nombre_modulo = "OTRO"
    ROOT = Path(__file__).resolve().parent / "OTRO"
else:
    modulo = MODULOS[int(seleccion) - 1]
    nombre_modulo = modulo[:-1]
    folder_name = nombre_modulo
    ROOT = Path(__file__).resolve().parent / folder_name

if not ROOT.is_dir():
    raise NotADirectoryError(f"No se encontró la carpeta del módulo: {ROOT}")

while True:
    linea_error = input("Ingrese el texto de error que desea buscar: ").strip()
    if linea_error:
        break
    print("El texto de error no puede estar vacío.")

TARGET_RE = re.compile(re.escape(linea_error), re.IGNORECASE)
ORGDEV_RE = re.compile(r"orgdev:\s*(\d+)", re.IGNORECASE)
UTRNNO_RE = re.compile(r"utrnno:\s*(\d+)", re.IGNORECASE)
DATE_RE = re.compile(r"Local date and time\s*:\s*(\d{2}/\d{2}/\d{4}\s+\d{2}:\d{2}:\d{2})", re.IGNORECASE)


def procesar_archivo(file_path: Path):
    filas = []
    ultimo_orgdev = ""
    ultimo_utrnno = ""
    ultima_fecha_hora = ""

    with file_path.open("r", encoding="latin-1", errors="replace") as fh:
        for line_no, line in enumerate(fh, start=1):
            m = ORGDEV_RE.search(line)
            if m:
                ultimo_orgdev = m.group(1).strip()

            m = UTRNNO_RE.search(line)
            if m:
                ultimo_utrnno = m.group(1).strip()

            m = DATE_RE.search(line)
            if m:
                ultima_fecha_hora = m.group(1).strip()

            if TARGET_RE.search(line):
                if ultimo_orgdev and ultimo_utrnno and ultima_fecha_hora:
                    filas.append({
                        "archivo": file_path.name,
                        "orgdev": ultimo_orgdev,
                        "utrnno": ultimo_utrnno,
                        "fecha_hora": ultima_fecha_hora,
                        "linea_error": line_no,
                    })

    return filas


if nombre_modulo == "OTRO":
    archivos = sorted(file_path for file_path in ROOT.iterdir() if file_path.is_file())
else:
    archivos = sorted(ROOT.glob(f"{modulo}*"))

filas = []
for file_path in archivos:
    if not file_path.is_file():
        continue
    filas.extend(procesar_archivo(file_path))

if not filas:
    print("No se encontraron coincidencias.")
else:
    filas = sorted(filas, key=lambda x: (x["fecha_hora"], x["archivo"], x["linea_error"]))
    csv_path = ROOT / f"{nombre_modulo}_resultado.csv"
    with csv_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["archivo", "orgdev", "utrnno", "fecha_hora", "linea_error"])
        writer.writeheader()
        writer.writerows(filas)

    print(f"Registros: {len(filas)}")
    print(f"CSV generado: {csv_path}")
    for row in filas[:10]:
        print(row)
