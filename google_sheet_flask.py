from flask import Flask, render_template, request, redirect, url_for
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import json
import os

app = Flask(__name__)

# Cargar credenciales desde la variable de entorno
service_account_info = json.loads(os.getenv("GOOGLE_CREDENTIALS", "{}"))
creds = ServiceAccountCredentials.from_json_keyfile_dict(service_account_info, [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/drive"
])
client = gspread.authorize(creds)

# ID de la hoja de cálculo
SHEET_ID = "1zzVvvvZzo3Jp_WGwf-aQP_P8bBHluXX5e2Wssvd0XVg"

# Abrir la hoja
sheet = client.open_by_key(SHEET_ID).sheet1

@app.route("/")
def home():
    names = [row[1] for row in sheet.get_all_values()[1:] if len(row) > 1]
    return render_template("index.html", names=names)

@app.route("/details", methods=["GET", "POST"])
def details():
    name = request.args.get("name", "")
    all_records = sheet.get_all_values()
    headers = all_records[0]  # Encabezados
    records = all_records[1:]  # Datos

    person_data = None
    row_index = None
    for index, row in enumerate(records, start=2):  # Comenzar desde la fila 2
        if len(row) > 1 and row[1] == name:  # La columna B tiene los nombres
            person_data = row
            row_index = index
            break

    if not person_data:
        return "<h2>No se encontraron datos para esta persona.</h2>"

    # Limitar a columnas B-K
    headers_filtered = headers[1:11]
    person_data_filtered = person_data[1:11]

    zipped_data = list(enumerate(zip(headers_filtered, person_data_filtered)))

    return render_template("details.html", headers=headers_filtered, data=person_data_filtered, zipped_data=zipped_data, name=name, row_index=row_index)

@app.route("/update", methods=["POST"])
def update():
    row_index = request.form["row_index"]
    updated_data = [request.form[f"data_{i}"] for i in range(10)]  # Extraer datos

    # Escribir en Google Sheets
    sheet.update(f"B{row_index}:K{row_index}", [updated_data])

    return "Success", 200

if __name__ == "__main__":
    app.run(debug=True)
