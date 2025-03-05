from flask import Flask, render_template, request, redirect, url_for
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import json
import os

app = Flask(__name__)

# 🔹 Cargar credenciales desde la variable de entorno
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

# 🔹 ID de la hoja de cálculo
SHEET_ID = "1zzVvvvZzo3Jp_WGwf-aQP_P8bBHluXX5e2Wssvd0XVg"

try:
    sheet = client.open_by_key(SHEET_ID).worksheet("Data")
    print("✅ Acceso exitoso a la hoja de cálculo.")
except Exception as e:
    print(f"❌ Error accediendo a Google Sheets: {e}")

# 🔹 Verificar si la hoja "Backup" existe, o crearla
try:
    backup_sheet = client.open_by_key(SHEET_ID).worksheet("Backup")
    print("✅ Hoja de backup encontrada.")
except:
    print("⚠️ No se encontró la hoja de backup. Creando una nueva...")
    backup_sheet = client.open_by_key(SHEET_ID).add_worksheet(title="Backup", rows="100", cols="10")
    print("✅ Hoja de backup creada.")

# 🔹 Función para obtener datos desde Google Sheets
def get_google_sheet_data():
    try:
        records = sheet.get_all_values()
        headers = records[0]
        return headers, records[1:]
    except Exception as e:
        print(f"❌ Error obteniendo datos de Google Sheets: {e}")
        return [], []

@app.route("/")
def home():
    _, records = get_google_sheet_data()
    names = [row[1] for row in records if len(row) > 1]
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
    try:
        row_index = request.form["row_index"]
        updated_data = [request.form[f"data_{i}"] for i in range(10)]
        sheet.update(f"B{row_index}:K{row_index}", [updated_data])
        print(f"✅ Datos actualizados en la fila {row_index}.")
        return redirect(url_for("home"))
    except Exception as e:
        print(f"❌ Error al actualizar en Google Sheets: {e}")
        return f"<h2>Error al actualizar datos: {e}</h2>"

@app.route("/backup", methods=["POST"])
def backup():
    try:
        headers, records = get_google_sheet_data()
        if not records:
            print("⚠️ No hay datos para respaldar.")
            return "<h2>No hay datos para respaldar.</h2>"

        backup_sheet.clear()
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
