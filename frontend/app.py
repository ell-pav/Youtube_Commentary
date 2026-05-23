import streamlit as st
from views.login import login_page
from views.register import register_page
from views.analyzer import analyzer_page


st.set_page_config(
    page_title="YouTube NLP Analyzer"
)


if "logged_in" not in st.session_state:

    st.session_state.logged_in = False


if st.session_state.logged_in:

    analyzer_page()

else:

    page = st.sidebar.selectbox(
        "Navigation",
        [
            "Login",
            "Register"
        ]
    )

    if page == "Login":

        login_page()

    else:

        register_page()