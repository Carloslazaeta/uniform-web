from flask import Flask, render_template, request, redirect, url_for
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import json
import os
import requests

app = Flask(__name__)

# Cargar credenciales desde la variable de entorno
try:
    service_account_info = json.loads(os.getenv("GOOGLE_CREDENTIALS", "{}"))
    
    creds = ServiceAccountCredentials.from_json_keyfile_dict(service_account_info, [
        "https://spreadsheets.google.com/feeds",
        "https://www.googleapis.com/auth/drive"
    ])
    client = gspread.authorize(creds)
    print("✅ Conexión con Google Sheets establecida correctamente.")
except Exception as e:
    print(f"❌ Error en la autenticación con Google Sheets: {e}")
    client = None

# ID de la hoja de cálculo
SHEET_ID = "1zzVvvvZzo3Jp_WGwf-aQP_P8bBHluXX5e2Wssvd0XVg"
GID = "945204493"
URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:json&gid={GID}"

# Verificar si se pudo autenticar correctamente antes de acceder a la hoja
sheet = None
if client:
    try:
        sheet = client.open_by_key(SHEET_ID).sheet1
        print("✅ Hoja de cálculo encontrada.")
    except Exception as e:
        print(f"❌ Error abriendo la hoja de cálculo: {e}")

def get_google_sheet_data():
    """Obtiene datos desde Google Sheets."""
    if not sheet:
        print("❌ No hay conexión con la hoja de cálculo.")
        return [], []

    try:
        response = requests.get(URL)
        if response.status_code != 200:
            print("❌ Error: No se pudo obtener datos de Google Sheets.")
            return [], []

        text = response.text[47:-2]  # Limpiar el JSON devuelto por Google Sheets
        data = json.loads(text)

        if "table" not in data or "rows" not in data["table"]:
            print("❌ Error: Formato inesperado en la respuesta de Google Sheets.")
            return [], []

        headers = [col["label"] for col in data["table"]["cols"] if "label" in col]
        records = [[cell["v"] if cell else "" for cell in row["c"]] for row in data["table"]["rows"][1:]]

        return headers, records
    except Exception as e:
        print(f"❌ Error inesperado al obtener datos de Google Sheets: {e}")
        return [], []

@app.route("/")
def home():
    """Página principal que muestra la lista de nombres."""
    headers, records = get_google_sheet_data()
    names = [row[1] for row in records if len(row) > 1]  # Columna B contiene los nombres
    return render_template("index.html", names=names)

@app.route("/details", methods=["GET"])
def details():
    """Página de detalles de un empleado."""
    name = request.args.get("name", "")
    headers, records = get_google_sheet_data()

    person_data = None
    row_index = None
    for index, row in enumerate(records, start=2):  # Empezar desde fila 2
        if len(row) > 1 and row[1] == name:  # Columna B contiene los nombres
            person_data = row
            row_index = index
            break

    if not person_data:
        return "<h2>No data found for this person.</h2>"

    headers_filtered = headers[1:11]  # Mostrar solo columnas B-K
    person_data_filtered = person_data[1:11]
    zipped_data = list(enumerate(zip(headers_filtered, person_data_filtered)))

    return render_template("details.html", headers=headers_filtered, data=person_data_filtered, zipped_data=zipped_data, name=name, row_index=row_index)

@app.route("/update", methods=["POST"])
def update():
    """Actualiza la información de un empleado en Google Sheets."""
    if not sheet:
        return "<h2>No se puede actualizar porque no hay conexión con Google Sheets.</h2>"

    row_index = request.form["row_index"]
    updated_data = [request.form[f"data_{i}"] for i in range(10)]

    try:
        sheet.update(f"B{row_index}:K{row_index}", [updated_data])
        print(f"✅ Datos actualizados en la fila {row_index}.")
    except Exception as e:
        print(f"❌ Error al actualizar los datos: {e}")
    
    return redirect(url_for("home"))

@app.route("/backup", methods=["POST"])
def backup():
    """Guarda los datos actuales en la hoja de Backup."""
    if not sheet or not client:
        return "<h2>No se puede hacer backup porque no hay conexión con Google Sheets.</h2>"

    try:
        headers, records = get_google_sheet_data()
        if not records:
            return "<h2>No hay datos para respaldar.</h2>"

        # Crear hoja de backup si no existe
        try:
            backup_sheet = client.open_by_key(SHEET_ID).worksheet("Backup")
        except gspread.WorksheetNotFound:
            backup_sheet = client.open_by_key(SHEET_ID).add_worksheet(title="Backup", rows="1000", cols="10")

        # Limpiar hoja antes de guardar nuevos datos
        backup_sheet.clear()

        # Guardar encabezados y datos
        backup_sheet.append_row(headers)
        for row in records:
            backup_sheet.append_row(row)

        print("✅ Backup guardado exitosamente.")
        return "<h2>Backup guardado exitosamente.</h2>"
    except Exception as e:
        print(f"❌ Error al guardar backup: {e}")
        return f"<h2>Error al guardar backup: {e}</h2>"

if __name__ == "__main__":
    app.run(debug=True)
