from flask import Flask, render_template, request, redirect, url_for
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import json
import os
import requests
from datetime import datetime
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

app = Flask(__name__)

# Cargar credenciales desde la variable de entorno
service_account_info = json.loads(os.getenv("GOOGLE_CREDENTIALS", "{}"))
creds = ServiceAccountCredentials.from_json_keyfile_dict(service_account_info, [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/drive"
])
client = gspread.authorize(creds)

drive_service = build('drive', 'v3', credentials=creds)

# ID de la hoja de cálculo
SHEET_ID = "1zzVvvvZzo3Jp_WGwf-aQP_P8bBHluXX5e2Wssvd0XVg"
GID = "945204493"
URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:json&gid={GID}"

# Abrir la hoja
sheet = client.open_by_key(SHEET_ID).sheet1

def get_google_sheet_data():
    try:
        response = requests.get(URL)
        if response.status_code != 200:
            print("Error: No se pudo obtener datos de Google Sheets.")
            return [], []
        text = response.text[47:-2]  # Limpiar el JSON devuelto por Google Sheets
        data = json.loads(text)
        headers = [col["label"] for col in data["table"]["cols"] if "label" in col]
        records = []
        for row in data["table"]["rows"]:
            records.append([cell["v"] if cell else "" for cell in row["c"]])
        return headers, list(set(tuple(i) for i in records))  # Eliminar duplicados
    except Exception as e:
        print("Error inesperado:", e)
        return [], []

@app.route("/")
def home():
    names = list(set(row[1] for row in get_google_sheet_data()[1] if len(row) > 1))  # Eliminar duplicados
    return render_template("index.html", names=names)

@app.route("/details")
def details():
    name = request.args.get("name", "")
    headers, records = get_google_sheet_data()
    person_data = next((row for row in records if len(row) > 1 and row[1] == name), None)
    if not person_data:
        return "<h2>No data found for this person.</h2>"
    headers_filtered = headers[1:11]
    person_data_filtered = person_data[1:11]
    zipped_data = list(enumerate(zip(headers_filtered, person_data_filtered)))
    return render_template("details.html", headers=headers_filtered, data=person_data_filtered, zipped_data=zipped_data, name=name)

@app.route("/update", methods=["POST"])
def update():
    row_index = request.form["row_index"]
    updated_data = [request.form[f"data_{i}"] for i in range(10)]
    sheet.update(f"B{row_index}:K{row_index}", [updated_data])
    return redirect(url_for("home"))

@app.route("/backup", methods=["POST"])
def backup():
    headers, records = get_google_sheet_data()
    if not records:
        return "No hay datos para respaldar."
    filename = f"backup_{datetime.now().strftime('%Y%m%d%H%M%S')}.csv"
    filepath = f"/tmp/{filename}"
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(",".join(headers) + "\n")
        for row in records:
            f.write(",".join(row) + "\n")
    file_metadata = {'name': filename, 'parents': ['17Nlf6VcoV7tsF0aNqN_PDXkzjvj0tkjG']}
    media = MediaFileUpload(filepath, mimetype='text/csv')
    drive_service.files().create(body=file_metadata, media_body=media, fields='id').execute()
    return "Backup guardado exitosamente en Google Drive."

if __name__ == "__main__":
    app.run(debug=True)
