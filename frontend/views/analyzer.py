import streamlit as st

import requests


def analyzer_page():

    st.title(
        "YouTube NLP Analyzer"
    )

    if st.button("Logout"):

        st.session_state.logged_in = False

        st.rerun()

    url = st.text_input(
        "YouTube URL"
    )

    sentiment = st.selectbox(
        "Choose sentiment",
        [
            "positive",
            "negative"
        ]
    )

    if st.button("Analyze"):

        headers = {
            "Authorization":
            f"Bearer {st.session_state.token}"
        }

        response = requests.post(
            "http://localhost:8000/analyze",
            json={
                "url": url,
                "sentiment": sentiment
            },
            headers=headers
        )

        data = response.json()

        if "error" in data:

            st.error(
                data["error"]
            )

        else:

            st.subheader("Summary")

            st.write(
                data["summary"]
            )

            st.subheader(
                "Generated Comment"
            )

            st.write(
                data["generated_comment"]
            )