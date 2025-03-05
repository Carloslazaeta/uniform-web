from flask import Flask, render_template, request, redirect, url_for
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import requests
import json

app = Flask(__name__)

# Configurar credenciales de Google Sheets
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_name("service_account.json", scope)
client = gspread.authorize(creds)

# ID de la hoja de cálculo
SHEET_ID = "1zzVvvvZzo3Jp_WGwf-aQP_P8bBHluXX5e2Wssvd0XVg"
GID = "945204493"
URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:json&gid={GID}"

# Abrir hoja
sheet = client.open_by_key(SHEET_ID).sheet1

def get_google_sheet_data():
    try:
        response = requests.get(URL)
        if response.status_code != 200:
            print("Error: No se pudo obtener datos de Google Sheets.")
            return [], []
        
        text = response.text[47:-2]  # Limpiar el JSON devuelto por Google Sheets
        data = json.loads(text)
        
        if "table" not in data or "rows" not in data["table"]:
            print("Error: Formato inesperado en la respuesta de Google Sheets.")
            return [], []
        
        rows = data["table"]["rows"]
        
        # Extraer encabezados
        headers = [col["label"] for col in data["table"]["cols"] if "label" in col]
        
        # Extraer todas las filas
        records = []
        for row in rows[1:]:  # Ignorar la primera fila (encabezados)
            records.append([cell["v"] if cell else "" for cell in row["c"]])
        
        return headers, records
    except Exception as e:
        print("Error inesperado:", e)
        return [], []

@app.route("/")
def home():
    names = [row[1] for row in get_google_sheet_data()[1] if len(row) > 1]
    return render_template("index.html", names=names)

@app.route("/details", methods=["GET", "POST"])
def details():
    name = request.args.get("name", "")
    headers, records = get_google_sheet_data()
    
    # Buscar la fila correspondiente al nombre seleccionado
    person_data = None
    row_index = None
    for index, row in enumerate(records, start=2):  # Empezar desde la fila 2 en Sheets
        if len(row) > 1 and row[1] == name:  # Columna B contiene los nombres
            person_data = row
            row_index = index
            break

    if not person_data:
        return "<h2>No data found for this person.</h2>"

    # Mostrar solo columnas B a K (índices 1 a 10)
    headers_filtered = headers[1:11]
    person_data_filtered = person_data[1:11]

    zipped_data = list(enumerate(zip(headers_filtered, person_data_filtered)))

    return render_template("details.html", headers=headers_filtered, data=person_data_filtered, zipped_data=zipped_data, name=name, row_index=row_index)

@app.route("/update", methods=["POST"])
def update():
    row_index = request.form["row_index"]  # Fila a actualizar en Google Sheets
    updated_data = [request.form[f"data_{i}"] for i in range(10)]  # Extraer datos del formulario
    
    # Escribir en Google Sheets
    sheet.update(f"B{row_index}:K{row_index}", [updated_data])
    
    return redirect(url_for("home"))

if __name__ == "__main__":
    app.run(debug=True)
