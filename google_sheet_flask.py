from flask import Flask, render_template, request, jsonify
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import os

app = Flask(__name__)

# Autenticación con Google Sheets
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_name("credentials.json", scope)
client = gspread.authorize(creds)

# ID de tu hoja de Google Sheets
SHEET_ID = "TUID_DE_HOJA_DE_GOOGLE_SHEETS"
sheet = client.open_by_key(SHEET_ID).sheet1


def get_google_sheet_data():
    """Obtener los datos actuales de la hoja de Google Sheets"""
    records = sheet.get_all_records()
    return records


@app.route("/")
def index():
    """Página principal que muestra la lista de nombres"""
    records = get_google_sheet_data()
    names = [row["Name"] for row in records]  # Asegurar que la columna "Name" exista
    return render_template("index.html", names=names)


@app.route("/details")
def details():
    """Muestra los detalles de un empleado"""
    name = request.args.get("name")
    records = get_google_sheet_data()

    person_data = None
    for row in records:
        if row["Name"] == name:
            person_data = row
            break

    if not person_data:
        return "No data found for this person.", 404

    headers = list(person_data.keys())
    values = list(person_data.values())

    zipped_data = list(zip(headers, values, values))  # Se agrega dos veces values para mantener el status

    return render_template("details.html", name=name, zipped_data=zipped_data)


@app.route("/update", methods=["POST"])
def update():
    """Guardar los cambios realizados en la tabla"""
    try:
        data = request.json
        name = data["name"]
        values = data["values"]
        status = data["status"]

        records = get_google_sheet_data()
        row_index = None

        # Buscar la fila correspondiente
        for index, row in enumerate(records, start=2):  # Empieza en 2 porque la fila 1 es de encabezados
            if row["Name"] == name:
                row_index = index
                break

        if row_index is None:
            return jsonify({"message": "Error: Name not found"}), 400

        # Guardar los valores en la hoja de Google Sheets
        for i, value in enumerate(values):
            sheet.update_cell(row_index, i + 2, value)  # Actualiza valores
            sheet.update_cell(row_index, i + 3, status[i])  # Actualiza estado

        return jsonify({"message": "Changes saved successfully!"})
    except Exception as e:
        return jsonify({"message": f"Error saving changes: {str(e)}"}), 500


if __name__ == "__main__":
    app.run(debug=True)
