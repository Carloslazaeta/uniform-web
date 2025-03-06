from flask import Flask, render_template, request, redirect, url_for, jsonify
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import json
import os

app = Flask(__name__)

# Cargar credenciales de Google desde variables de entorno
service_account_info = json.loads(os.getenv("GOOGLE_CREDENTIALS", "{}"))
creds = ServiceAccountCredentials.from_json_keyfile_dict(service_account_info, [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/drive"
])
client = gspread.authorize(creds)

# ID de Google Sheets
SHEET_ID = "1zzVvvvZzo3Jp_WGwf-aQP_P8bBHluXX5e2Wssvd0XVg"
sheet = client.open_by_key(SHEET_ID).sheet1

@app.route("/")
def home():
    records = sheet.get_all_records()
    names = [row["Name"] for row in records]
    return render_template("index.html", names=names)

@app.route("/details")
def details():
    name = request.args.get("name", "")
    records = sheet.get_all_records()

    person_data = next((row for row in records if row["Name"] == name), None)
    if not person_data:
        return "<h2>No data found for this person.</h2>"

    headers = list(person_data.keys())
    values = list(person_data.values())
    zipped_data = list(zip(headers, values))

    return render_template("details.html", name=name, zipped_data=zipped_data)

if __name__ == "__main__":
    app.run(debug=True)
