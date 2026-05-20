from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api.formatters import TextFormatter
from youtube_transcript_api._errors import NoTranscriptFound, TranscriptsDisabled

def get_transcript(video_id: str, lang: str = "fr") -> str:
    try:
        transcript = YouTubeTranscriptApi().fetch(video_id, languages=[lang])
        transcript_text = " ".join([snippet.text for snippet in transcript])
        formatter = TextFormatter()
        transcript_text = formatter.format_transcript(transcript)
        return transcript_text
    except NoTranscriptFound:
        print(f"[ERREUR] Aucun transcript trouvé pour la langue : {lang}")
        return ""
    except TranscriptsDisabled:
        print("[ERREUR] Les transcriptions sont désactivées pour cette vidéo.")
        return ""
    except Exception as e:
        print(f"[ERREUR] Erreur inattendue : {e}")
        return ""
    
def list_available_languages(video_id: str):
    ytt_api = YouTubeTranscriptApi()
    transcript_list = ytt_api.list(video_id)
    print("[INFO] Langues disponibles :", transcript_list)
