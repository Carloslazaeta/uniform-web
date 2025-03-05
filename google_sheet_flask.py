import os
import json
import gspread
from flask import Flask, request, render_template, jsonify
from oauth2client.service_account import ServiceAccountCredentials

app = Flask(__name__)

# Conexión con Google Sheets
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
credentials_json = json.loads(os.getenv("GOOGLE_CREDENTIALS", "{}"))  # Leer credenciales desde variables de entorno
creds = ServiceAccountCredentials.from_json_keyfile_dict(credentials_json, scope)
client = gspread.authorize(creds)

# ID de la hoja de Google Sheets (Reemplázalo con el real o usa variables de entorno)
SHEET_ID = os.getenv("SHEET_ID", "TU_ID_DE_GOOGLE_SHEETS")
sheet = client.open_by_key(SHEET_ID).sheet1


def get_google_sheet_data():
    """Obtener los datos actuales de la hoja de Google Sheets"""
    try:
        records = sheet.get_all_records()
        return records
    except Exception as e:
        print(f"❌ Error obteniendo datos de Google Sheets: {str(e)}")
        return []


@app.route("/")
def index():
    """Página principal que muestra la lista de nombres"""
    records = get_google_sheet_data()
    names = [row["Name"] for row in records if "Name" in row]  # Validar existencia de columna "Name"
    return render_template("index.html", names=names)


@app.route("/details")
def details():
    """Muestra los detalles de un empleado"""
    name = request.args.get("name")
    records = get_google_sheet_data()

    person_data = next((row for row in records if row.get("Name") == name), None)

    if not person_data:
        return "No data found for this person.", 404

    headers = list(person_data.keys())
    values = list(person_data.values())

    # Se duplica values para mantener el formato de la tabla
    zipped_data = list(zip(headers, values, values))  

    return render_template("details.html", name=name, zipped_data=zipped_data)


@app.route("/update", methods=["POST"])
def update():
    """Guardar los cambios realizados en la tabla"""
    try:
        data = request.json
        name = data.get("name")
        values = data.get("values", [])
        status = data.get("status", [])

        records = get_google_sheet_data()
        row_index = None

        # Buscar la fila correspondiente al nombre
        for index, row in enumerate(records, start=2):  # Empieza en la fila 2 (1 es encabezado)
            if row.get("Name") == name:
                row_index = index
                break

        if row_index is None:
            return jsonify({"message": "Error: Name not found"}), 400

        # Guardar los valores en Google Sheets
        for i, value in enumerate(values):
            sheet.update_cell(row_index, i + 2, value)  # Columna de valores
            if i < len(status):
                sheet.update_cell(row_index, i + 3, status[i])  # Columna de estado

        return jsonify({"message": "Changes saved successfully!"})

    except Exception as e:
        return jsonify({"message": f"Error saving changes: {str(e)}"}), 500


if __name__ == "__main__":
    app.run(debug=True)
