from flask import Flask, request, jsonify, send_file, render_template_string
from openai import OpenAI
import os

# Pour PDF avec mise en page
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.pagesizes import letter

app = Flask(__name__)

# 🔑 Initialise OpenAI avec ta clé d’environnement
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# === Page principale ===
@app.route("/")
def index():
    return render_template_string(open("index.html").read())

# === Génération des propositions via OpenAI ===
@app.route("/generate", methods=["POST"])
def generate():
    data = request.json
    brief = data.get("brief", "")

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",  # rapide et optimisé
            messages=[
                {"role": "system", "content": (
                    "Tu es un expert en marketing sportif. "
                    "Propose 3 à 5 activations marketing CONCRÈTES et adaptées au marché : "
                    "1) description, 2) influenceurs sportifs pertinents (avec plateforme), "
                    "3) statistiques ou tendances (TikTok, Instagram, YouTube), "
                    "4) estimation simple de KPIs. "
                    "Présente les résultats avec des titres et listes claires."
                )},
                {"role": "user", "content": brief}
            ],
            max_tokens=700,
            temperature=0.7
        )

        proposals = response.choices[0].message.content.strip()

        # Sauvegarde pour PDF
        with open("last_output.txt", "w", encoding="utf-8") as f:
            f.write(proposals)

        return jsonify({"proposals": proposals})

    except Exception as e:
        return jsonify({"error": str(e)}), 500

# === Génération PDF avec mise en page ===
@app.route("/download_pdf", methods=["GET"])
def download_pdf():
    if not os.path.exists("last_output.txt"):
        return jsonify({"error": "Aucune proposition à exporter"}), 400

    with open("last_output.txt", "r", encoding="utf-8") as f:
        proposals = f.read()

    pdf_path = "propositions.pdf"
    doc = SimpleDocTemplate(pdf_path, pagesize=letter,
                            rightMargin=50, leftMargin=50,
                            topMargin=50, bottomMargin=50)

    styles = getSampleStyleSheet()
    story = []

    # Titre principal
    story.append(Paragraph("Propositions d'activations", styles["Title"]))
    story.append(Spacer(1, 20))

    # Mise en forme du contenu
    for line in proposals.split("\n"):
        if line.strip() == "":
            story.append(Spacer(1, 10))
        elif line.startswith("###"):  # titres niveau 3
            story.append(Paragraph(line.replace("###", "").strip(), styles["Heading3"]))
            story.append(Spacer(1, 6))
        elif line.startswith("**"):  # gras
            story.append(Paragraph(f"<b>{line.replace('**','')}</b>", styles["Normal"]))
        else:  # texte normal
            story.append(Paragraph(line.strip(), styles["Normal"]))
            story.append(Spacer(1, 6))

    # Mention légale en fin de document
    story.append(Spacer(1, 30))
    story.append(Paragraph(
        "Will Dorignac - Expert en marketing et communication Sport - Tous droits réservés.",
        styles["Italic"]
    ))

    doc.build(story)
    return send_file(pdf_path, as_attachment=True)

if __name__ == "__main__":
    app.run(debug=True)