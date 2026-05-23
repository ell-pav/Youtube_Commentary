from backend.services.nlp_service import (
    generate_comment
)

from backend.services.sentiment_service import (
    analyze_sentiment
)


def generate_valid_comment(
    summary: str,
    desired_sentiment: str,
    max_attempts: int = 5
):

    comment = ""

    for attempt in range(max_attempts):

        comment = generate_comment(
            summary,
            desired_sentiment
        )

        result = analyze_sentiment(
            comment
        )

        detected_sentiment = result[
            "label"
        ]

        print("=" * 50)

        print(
            f"Attempt: {attempt + 1}"
        )

        print(
            f"Desired: {desired_sentiment}"
        )

        print(
            f"Detected: {detected_sentiment}"
        )

        print(
            f"Comment: {comment}"
        )

        print("=" * 50)

        if (
            detected_sentiment
            ==
            desired_sentiment
        ):

            return {

                "comment": comment,

                "validated": True,

                "attempts": attempt + 1
            }

    return {

        "comment": comment,

        "validated": False,

        "attempts": max_attempts
    }