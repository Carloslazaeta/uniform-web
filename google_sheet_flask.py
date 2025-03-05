from flask import Flask, render_template, request, redirect, url_for
from googleapiclient.discovery import build
from oauth2client.service_account import ServiceAccountCredentials
import gspread
import json
import os

app = Flask(__name__)

# 🔹 Cargar credenciales desde la variable de entorno
service_account_info = json.loads(os.getenv("GOOGLE_CREDENTIALS", "{}"))
creds = ServiceAccountCredentials.from_json_keyfile_dict(
    service_account_info,
    scopes=[
        "https://www.googleapis.com/auth/drive",
        "https://www.googleapis.com/auth/spreadsheets"
    ],
)
client = gspread.authorize(creds)
drive_service = build("drive", "v3", credentials=creds)

# 📂 **ID de la carpeta en Google Drive donde se guardarán los archivos**
FOLDER_ID = "17Nlf6VcoV7tsF0aNqN_PDXkzjvj0tkjG"
# 📊 **ID de la hoja de cálculo de Google Sheets**
SHEET_ID = "1zzVvvvZzo3Jp_WGwf-aQP_P8bBHluXX5e2Wssvd0XVg"
sheet = client.open_by_key(SHEET_ID).sheet1


### 🔍 **Función para obtener datos de Google Sheets**
def get_google_sheet_data():
    try:
        data = sheet.get_all_values()
        headers = data[0]  # Primera fila como encabezado
        records = data[1:]  # Resto de los registros
        return headers, records
    except Exception as e:
        print(f"⚠️ Error accediendo a Google Sheets: {e}")
        return [], []


### 📂 **Función para listar archivos en la carpeta de Google Drive**
def list_drive_files():
    query = f"'{FOLDER_ID}' in parents"
    results = drive_service.files().list(q=query, fields="files(id, name)").execute()
    files = results.get("files", [])
    
    if not files:
        print("📂 No hay archivos en la carpeta de Google Drive.")
    else:
        print("📁 Archivos en Google Drive:")
        for file in files:
            print(f"✅ {file['name']} ({file['id']})")


### 📝 **Función para crear un archivo en Google Drive**
def create_drive_file(filename, content):
    file_metadata = {
        "name": filename,
        "parents": [FOLDER_ID],
        "mimeType": "text/plain"
    }
    media = {
        "name": filename,
        "mimeType": "text/plain",
        "body": content
    }
    file = drive_service.files().create(body=file_metadata, media_body=media).execute()
    print(f"✅ Archivo creado en Google Drive: {filename} (ID: {file['id']})")


### 🔄 **Función para guardar los datos de cada persona en un archivo**
def save_person_data():
    headers, records = get_google_sheet_data()

    for record in records:
        if len(record) > 1:
            name = record[1]  # Suponiendo que la columna B contiene los nombres
            filename = f"{name}.txt"
            content = "\n".join([f"{headers[i]}: {record[i]}" for i in range(len(record))])
            create_drive_file(filename, content)

    print("✅ Todos los archivos han sido creados y guardados en Google Drive.")


@app.route("/")
def home():
    headers, records = get_google_sheet_data()
    names = [row[1] for row in records if len(row) > 1]  # Columna B con nombres
    return render_template("index.html", names=names)


@app.route("/details")
def details():
    name = request.args.get("name", "")
    headers, records = get_google_sheet_data()

    person_data = None
    for row in records:
        if len(row) > 1 and row[1] == name:  # Buscar por nombre en la columna B
            person_data = row
            break

    if not person_data:
        return "<h2>No data found for this person.</h2>"

    zipped_data = list(zip(headers, person_data))
    return render_template("details.html", data=zipped_data, name=name)


@app.route("/save", methods=["POST"])
def save():
    save_person_data()
    return redirect(url_for("home"))


if __name__ == "__main__":
    app.run(debug=True)
