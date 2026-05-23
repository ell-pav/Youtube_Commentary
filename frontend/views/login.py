import streamlit as st

from auth import sign_in


def login_page():

    st.title("Login")

    email = st.text_input(
        "Email"
    )

    password = st.text_input(
        "Password",
        type="password"
    )

    if st.button("Login"):

        try:

            result = sign_in(
                email,
                password
            )

            st.session_state.logged_in = True

            st.session_state.token = (
                result.session.access_token
            )

            st.success(
                "Connected"
            )

            st.rerun()

        except Exception as e:

            st.error(str(e))