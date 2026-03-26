from flask import Flask, render_template, request, send_file
import pandas as pd
import os
import tempfile

app = Flask(__name__)

df = pd.read_excel("master_data.xlsx")

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        emp_id = request.form.get("emp_id")

        if not emp_id:
            return "Invalid input"

        filtered = df[df["Employee Code"] == emp_id]

        if filtered.empty:
            return "No data found"

        # TEMP FILE (important for cloud)
        file_path = os.path.join(tempfile.gettempdir(), f"{emp_id}.xlsx")
        filtered.to_excel(file_path, index=False)

        return send_file(file_path, as_attachment=True)

    return render_template("index.html")


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)