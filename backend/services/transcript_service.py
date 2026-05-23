from youtube_transcript_api import YouTubeTranscriptApi
import re


def clean_text(text: str) -> str:

    text = text.replace("\n", " ")

    text = re.sub(r"\[.*?\]", "", text)

    text = re.sub(r"\s+", " ", text)

    return text.strip()


def get_video_transcript(video_id: str) -> str:

    ytt_api = YouTubeTranscriptApi()

    transcript = None

    try:
        transcript = ytt_api.fetch(
            video_id,
            languages=["en"]
        )

    except Exception:
        pass

    if transcript is None:

        try:
            transcript = ytt_api.fetch(
                video_id,
                languages=["fr"]
            )

        except Exception:
            pass

    if transcript is None:

        try:

            transcript_list = ytt_api.list(video_id)

            available_languages = [
                t.language_code
                for t in transcript_list
            ]

            transcript = transcript_list.find_transcript(
                available_languages
            ).fetch()

        except Exception:

            raise Exception(
                "No transcript available for this video."
            )

    text = " ".join([x.text for x in transcript])

    cleaned_text = clean_text(text)

    return cleaned_text