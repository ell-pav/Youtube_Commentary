# main.py
from transcript import get_transcript, list_available_languages

video_id = "4M32ZL369AY"

# (Optionnel) Voir les langues disponibles
list_available_languages(video_id)

# Obtenir la transcription
transcript = get_transcript(video_id, lang="fr")

if transcript:
    print("[TRANSCRIPT RÉSUMÉ]")
    print(transcript[:500])  # Pour tester
else:
    print("⚠️ Aucune transcription disponible.")