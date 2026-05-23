import streamlit as st

from auth import sign_up


def register_page():

    st.title("Register")

    email = st.text_input(
        "Email"
    )

    password = st.text_input(
        "Password",
        type="password"
    )

    if st.button("Create account"):

        try:

            sign_up(
                email,
                password
            )

            st.success(
                "Account created"
            )

        except Exception as e:

            st.error(str(e))