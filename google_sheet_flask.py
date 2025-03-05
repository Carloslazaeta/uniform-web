from flask import Flask, render_template, request, redirect, url_for
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import json
import os
import requests

app = Flask(__name__)

# 🟢 1. Cargar credenciales de la variable de entorno
try:
    service_account_info = json.loads(os.getenv("GOOGLE_CREDENTIALS", "{}"))
    creds = ServiceAccountCredentials.from_json_keyfile_dict(service_account_info, [
        "https://spreadsheets.google.com/feeds",
        "https://www.googleapis.com/auth/drive"
    ])
    client = gspread.authorize(creds)
    print("✅ Conexión exitosa con Google Sheets")
except Exception as e:
    print("❌ ERROR al cargar credenciales:", e)
    exit(1)  # Detener ejecución si no hay credenciales válidas

# 🟢 2. Verificar acceso a Google Sheets
SHEET_ID = "1zzVvvvZzo3Jp_WGwf-aQP_P8bBHluXX5e2Wssvd0XVg"
try:
    sheet = client.open_by_key(SHEET_ID).sheet1
    print("✅ Hoja de cálculo cargada correctamente")
except Exception as e:
    print("❌ ERROR al abrir la hoja de cálculo:", e)
    exit(1)

# 📌 Prueba de escritura en la celda B2
try:
    sheet.update("B2", [["Test de escritura"]])
    print("✅ Permisos de edición confirmados")
except Exception as e:
    print("⚠️ No se pudo escribir en la hoja. Verifica los permisos:", e)

# 🟢 3. Obtener datos de Google Sheets
def get_google_sheet_data():
    try:
        data = sheet.get_all_values()
        if not data:
            return [], []
        
        headers = data[0]  # Primera fila como encabezados
        records = data[1:]  # Datos desde la segunda fila

        return headers, records
    except Exception as e:
        print("❌ ERROR al obtener datos de Google Sheets:", e)
        return [], []

@app.route("/")
def home():
    _, records = get_google_sheet_data()
    names = [row[1] for row in records if len(row) > 1]  # Columna B (índice 1)
    return render_template("index.html", names=names)

@app.route("/details", methods=["GET", "POST"])
def details():
    name = request.args.get("name", "")
    headers, records = get_google_sheet_data()

    person_data = None
    row_index = None
    for index, row in enumerate(records, start=2):  # Empieza en fila 2
        if len(row) > 1 and row[1] == name:
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
    try:
        row_index = request.form["row_index"]
        updated_data = [request.form[f"data_{i}"] for i in range(10)]

        # Escribir en Google Sheets
        sheet.update(f"B{row_index}", [updated_data])
        print(f"✅ Datos actualizados en fila {row_index}: {updated_data}")

    except Exception as e:
        print(f"❌ ERROR al actualizar Google Sheets en fila {row_index}: {e}")
        return "<h2>Error al actualizar la hoja de cálculo.</h2>"

    return redirect(url_for("home"))

if __name__ == "__main__":
    app.run(debug=True)
