from flask import Flask, render_template, request, redirect, url_for
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import json
import os
import requests

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
sheet = client.open_by_key(SHEET_ID).sheet1
backup_sheet = client.open_by_key(SHEET_ID).add_worksheet(title="Backup", rows="100", cols="10")

def get_google_sheet_data():
    try:
        records = sheet.get_all_values()
        headers = records[0]  # Primera fila como encabezado
        data = records[1:]  # Datos restantes
        return headers, data
    except Exception as e:
        print("Error obteniendo datos:", e)
        return [], []

@app.route("/")
def home():
    names = [row[1] for row in get_google_sheet_data()[1] if len(row) > 1]
    return render_template("index.html", names=names)

@app.route("/details", methods=["GET", "POST"])
def details():
    name = request.args.get("name", "")
    headers, records = get_google_sheet_data()
    person_data = None
    row_index = None
    
    for index, row in enumerate(records, start=2):
        if len(row) > 1 and row[1] == name:
            person_data = row
            row_index = index
            break
    
    if not person_data:
        return "<h2>No data found for this person.</h2>"
    
    headers_filtered = headers[1:11]
    person_data_filtered = person_data[1:11]
    zipped_data = list(enumerate(zip(headers_filtered, person_data_filtered)))
    
    return render_template("details.html", headers=headers_filtered, data=person_data_filtered, zipped_data=zipped_data, name=name, row_index=row_index)

@app.route("/update", methods=["POST"])
def update():
    row_index = request.form["row_index"]
    updated_data = [request.form[f"data_{i}"] for i in range(10)]
    sheet.update(f"B{row_index}:K{row_index}", [updated_data])
    return redirect(url_for("home"))

@app.route("/save_backup", methods=["POST"])
def save_backup():
    headers, records = get_google_sheet_data()
    backup_sheet.append_rows(records)
    return "<h2>Backup saved successfully!</h2><a href='/'>Go back</a>"

if __name__ == "__main__":
    app.run(debug=True)
