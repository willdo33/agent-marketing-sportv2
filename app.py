#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
from flask import Flask, request, jsonify, render_template, send_file
from dotenv import load_dotenv
from openai import OpenAI
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
import io

# Charger .env ou apikey.env
load_dotenv("apikey.env")

# Initialiser le client OpenAI
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

app = Flask(__name__)

# ------------------------------
# PAGE D’ACCUEIL
# ------------------------------
@app.route("/")
def index():
    print("👉 index.html rendu")
    return render_template("index.html")

# ------------------------------
# GÉNÉRATION DES PROPOSITIONS
# ------------------------------
@app.route("/generate", methods=["POST"])
def generate():
    try:
        data = request.get_json()
        prompt = data.get("prompt", "")

        if not prompt:
            return jsonify({"error": "Prompt manquant"}), 400

        # CONTEXTE SYSTEM
                # ✅ Prompt enrichi
        system_prompt = (
            "Tu t'appelles Will.ia et tu es un expert en marketing et communication spécialisé dans le sport. Tu as 10 ans d'expérience. Tu as travaillé pour Take off, EA Sports, Classico sport, Elwing Boards et Sportall."
            "Ta mission est de proposer des activations marketing et communication CONCRÈTES et DÉTAILLÉES. "
            "Structure toujours tes réponses ainsi :\n\n"
            " 💻  *ACTIVATION* (titre en majuscules et italique)\n"

            "   → Décris le concept clairement.\n\n"

            " 🤳  *INFLUENCEURS / ATHLÈTES PERTINENTS* (titre en majuscules et italique)\n"

            "   → Donne au moins 3 exemples réalistes et cohérents avec la cible. Indiquer les chiffres clés de leur notoriété sur les réseaux sociaux.\n\n"

            " 📶  *IMPACT DE LA CAMPAGNE* (titre en majuscules et italique) \n"

            "   → Instagram (moyenne likes, engagement %)\n"
            "   → TikTok (moyenne vues, taux de partage)\n"
            "   → YouTube (moyenne vues, durée de visionnage)\n"
            "   → Spotify (streams moyens, abonnés mensuels)\n"
            "   → Twitch (moyenne viewers en live, abonnés)\n\n"
            "   → Résultat global de l'activation (chiffres clés)\n\n"

            " 💶  *ESTIMATION DU COÛT* (titre en majuscules et italique)\n"

            "   → Estime le coût avec les tendances du marché\n"
            "Évite tout langage trop vague. Donne des chiffres basés sur les benchmarks récents. "
            "Ne mets pas de # ou de markdown, le texte doit être propre et lisible."
        )


        # Appel à OpenAI
        completion = client.chat.completions.create(
            model="gpt-4.1-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ]
        )

        result = completion.choices[0].message.content

        # Stocker résultat en session (ou en variable globale pour PDF)
        request.environ['last_result'] = result  

        return jsonify({"propositions": result})

    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ------------------------------
# GÉNÉRATION DU PDF
# ------------------------------
@app.route("/download_pdf", methods=["POST"])
def download_pdf():
    try:
        data = request.get_json()
        content = data.get("content", "")

        if not content:
            return jsonify({"error": "Pas de contenu à exporter"}), 400

        # Création PDF
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter)
        styles = getSampleStyleSheet()
        story = []

        # Titre
        story.append(Paragraph("<b>Propositions Marketing Sport</b>", styles["Title"]))
        story.append(Spacer(1, 20))

        # Contenu
        for line in content.split("\n"):
            if line.strip():
                if line[0].isdigit() and "." in line[:3]:  # sous-titres numérotés
                    story.append(Paragraph(f"<b>{line}</b>", styles["Heading3"]))
                else:
                    story.append(Paragraph(line, styles["Normal"]))
                story.append(Spacer(1, 10))

        # Mention légale
        story.append(Spacer(1, 30))
        story.append(Paragraph(
            "Will Dorignac - Expert en marketing et communication - Tous droits réservés. Mail : wdorignac@gmail.com - Téléphone : 0601401791",
        
            styles["Italic"]
        ))

        doc.build(story)
        buffer.seek(0)

        return send_file(
            buffer,
            as_attachment=True,
            download_name="propositions.pdf",
            mimetype="application/pdf"
        )

    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ------------------------------
# LANCEMENT APP
# ------------------------------
if __name__ == "__main__":
    app.run(debug=True)