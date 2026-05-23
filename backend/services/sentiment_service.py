from transformers import pipeline


classifier = pipeline(
    "sentiment-analysis",
    model="distilbert-base-uncased-finetuned-sst-2-english"
)


def normalize_sentiment(label: str):

    label = label.lower()

    if "positive" in label:
        return "positive"

    if "negative" in label:
        return "negative"

    return "neutral"


def analyze_sentiment(text: str):

    result = classifier(text)[0]

    label = normalize_sentiment(
        result["label"]
    )

    score = result["score"]

    return {
        "label": label,
        "score": score
    }