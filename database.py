from supabase import create_client
from dotenv import load_dotenv
import os

# Charger variables d'environnement
load_dotenv()
url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_KEY_RLS")

supabase = create_client(url, key)


def creer_projet_ia(nom: str, description: str, type_modele: str, hyperparametres: dict):
    """
    Insérer un projet IA dans la table projets_ia
    """
    try:
        data = {
            "nom": nom,
            "description": description,
            "type_modele": type_modele,
            "hyperparametres": hyperparametres
        }
        response = supabase.table("projets_ia").insert(data).execute()
        print("Projet inséré :", response.data)
        return response.data
    except Exception as e:
        print("Erreur lors de l'insertion :", e)
        return None


def lister_projets():
    """
    Récupérer tous les projets IA et les afficher
    """
    try:
        response = supabase.table("projets_ia").select("*").execute()
        projets = response.data
        if not projets:
            print("Aucun projet trouvé.")
        else:
            print("Liste des projets IA :")
            for projet in projets:
                print(f"- {projet['id']}: {projet['nom']} ({projet['type_modele']})")
        return projets
    except Exception as e:
        print("Erreur lors de la récupération :", e)
        return []


def main():
    # Exemple de création d’un projet IA
    creer_projet_ia(
        nom="Analyse de sentiment",
        description="Un modèle NLP pour classifier des textes.",
        type_modele="NLP",
        hyperparametres={"epochs": 5, "batch_size": 16, "learning_rate": 0.001}
    )

    # Vérifier que l’insertion fonctionne
    lister_projets()


if __name__ == "__main__":
    main()