from flask import Flask, render_template, request, redirect, url_for
import json
import os
from flask_cors import CORS  # Importation de Flask-CORS

app = Flask(__name__)
app.secret_key = "secret_key_ppv"

# Activation de Flask-CORS (si nécessaire)
CORS(app)

DATA_FILE = "ppv_data.json"

def save_to_file(data):
    """Sauvegarde les données dans un fichier JSON."""
    with open(DATA_FILE, "w") as file:
        json.dump(data, file, indent=4)

def load_from_file():
    """Charge les données depuis un fichier JSON."""
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as file:
            return json.load(file)
    return {}

@app.route("/", methods=["GET", "POST"])
@app.route("/entreprise", methods=["GET", "POST"])
def entreprise():
    """Collecte des données générales de l'entreprise."""
    data = load_from_file()

    if request.method == "POST":
        # Récupère les données saisies
        ca1 = float(request.form.get("chiffre_affaire_0", 0))
        ca2 = float(request.form.get("chiffre_affaire_1", 0))
        ca3 = float(request.form.get("chiffre_affaire_2", 0))
        montant_ppv = float(request.form.get("montant_ppv", 0))

        # Calculs
        ca_moyen = (ca1 + ca2 + ca3) / 3 if ca1 and ca2 and ca3 else 0
        seuil_max_prime = 0.01 * ca_moyen

        # Sauvegarde
        data["entreprise"] = {
            "chiffres_affaires": [ca1, ca2, ca3],
            "ca_moyen": ca_moyen,
            "seuil_max_prime": seuil_max_prime,
            "montant_ppv": montant_ppv
        }
        save_to_file(data)

        return redirect(url_for("employes"))

    return render_template("entreprise.html", data=data)

@app.route("/employes", methods=["GET", "POST"])
def employes():
    """Gère les données des employés et le mode de partage."""
    data = load_from_file()

    if request.method == "POST":
        mode = request.form.get("mode_partage")
        effectif = int(request.form.get("effectif", 0))

        employees = []
        if mode == "uniforme":
            salaire_moyen = float(request.form.get("salaire_moyen", 0))
            data["salaries"] = [{"salaire_moyen": salaire_moyen}]
        elif mode == "salaire":
            for i in range(effectif):
                salaire = float(request.form.get(f"salaire_{i}", 0))
                employees.append({"salaire": salaire})
            data["salaries"] = employees
        elif mode == "temps_travail":
            salaire_moyen = float(request.form.get("salaire_moyen", 0))
            for i in range(effectif):
                temps_travail = float(request.form.get(f"temps_travail_{i}", 0)) / 100
                employees.append({"temps_travail": temps_travail})
            data["salaries"] = {"salaire_moyen": salaire_moyen, "employees": employees}

        data["mode_partage"] = mode
        data["effectif"] = effectif
        save_to_file(data)
        return redirect(url_for("synthese"))

    return render_template("employes.html", data=data)

@app.route("/synthese", methods=["GET"])
def synthese():
    """Affiche la synthèse des calculs."""
    data = load_from_file()
    montant_total = data["entreprise"]["montant_ppv"]
    mode = data["mode_partage"]
    employees = []

    if mode == "uniforme":
        prime = montant_total / data["effectif"]
        employees = [{"employe": f"Employé {i+1}", "prime": round(prime, 2)} for i in range(data["effectif"])]
    elif mode == "salaire":
        salaire_total = sum(e["salaire"] for e in data["salaries"])
        for idx, e in enumerate(data["salaries"]):
            prime = montant_total * (e["salaire"] / salaire_total)
            employees.append({"employe": f"Employé {idx+1}", "prime": round(prime, 2)})
    elif mode == "temps_travail":
        salaire_moyen = data["salaries"]["salaire_moyen"]
        temps_total = sum(e["temps_travail"] for e in data["salaries"]["employees"])
        for idx, e in enumerate(data["salaries"]["employees"]):
            prime = montant_total * (e["temps_travail"] / temps_total)
            employees.append({"employe": f"Employé {idx+1}", "prime": round(prime, 2)})

    simulation = {"employees": employees}
    data["simulation"] = simulation
    save_to_file(data)

    return render_template("synthese.html", simulation=simulation, data=data)

if __name__ == "__main__":
    # Lancement du serveur Flask
    app.run(debug=True)
