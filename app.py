import streamlit as st
from database import create_client
from dotenv import load_dotenv
import os
import streamlit.components.v1 as components


load_dotenv()
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

st.set_page_config(page_title="Gestion utilisateurs", page_icon="👤")
st.title("👤 Gestion utilisateurs métiers")

# Initialisation de la session
if "user" not in st.session_state:
    st.session_state.user = None

# ---------------------------------
# INSCRIPTION
# ---------------------------------
st.header("Inscription")
with st.form("signup"):
    email = st.text_input("Email")
    password = st.text_input("Mot de passe", type="password")
    username = st.text_input("Nom d'utilisateur")
    submit = st.form_submit_button("Créer mon compte")

    if submit:
        try:
            auth_response = supabase.auth.sign_up({"email": email, "password": password})
            user = auth_response.user
            if user:
                st.success(f"✅ Utilisateur {email} créé. Vérifiez vos emails pour confirmation.")
            else:
                st.error("❌ Impossible de créer l'utilisateur")
        except Exception as e:
            st.error(f"❌ Erreur lors de l'inscription : {e}")

# ---------------------------------
# CONNEXION EMAIL/PASSWORD
# ---------------------------------
st.header("Connexion")
with st.form("login"):
    email_login = st.text_input("Email (connexion)")
    password_login = st.text_input("Mot de passe (connexion)", type="password")
    login_btn = st.form_submit_button("Se connecter")

    if login_btn:
        try:
            auth_response = supabase.auth.sign_in_with_password({
                "email": email_login,
                "password": password_login
            })
            user = auth_response.user
            if user:
                st.session_state.user = user
                st.success(f"✅ Connecté en tant que {user.email}")
                # Créer profil si absent
                profile = supabase.table("profiles").select("*").eq("id", user.id).execute()
                if not profile.data:
                    supabase.table("profiles").insert({
                        "id": user.id,
                        "username": user.email.split("@")[0]
                    }).execute()
                    st.info("Profil créé automatiquement ✅")
            else:
                st.error("❌ Email ou mot de passe incorrect")
        except Exception as e:
            st.error(f"Erreur : {e}")

# ---------------------------------
# Récupération tokens OAuth depuis query params
# ---------------------------------
params = st.query_params
if "access_token" in params and "refresh_token" in params:
    access_token = params["access_token"][0]
    refresh_token = params["refresh_token"][0]
    try:
        session = supabase.auth.set_session(access_token, refresh_token)
        if session.user:
            st.session_state.user = session.user
            st.success(f"✅ Connecté via OAuth : {session.user.email}")
            # Créer profil si absent
            profile = supabase.table("profiles").select("*").eq("id", session.user.id).execute()
            if not profile.data:
                supabase.table("profiles").insert({
                    "id": session.user.id,
                    "username": session.user.email.split("@")[0]
                }).execute()
                st.info("Profil créé automatiquement ✅")
    except Exception as e:
        st.error(f"Erreur OAuth : {e}")

# ---------------------------------
# Boutons OAuth
# ---------------------------------
st.header("Connexion via OAuth")
col1, col2 = st.columns(2)

with col1:
    if st.button("🔑 Google Login"):
        res = supabase.auth.sign_in_with_oauth({
            "provider": "google",
            "options": {"redirect_to": "http://localhost:8502/oauth_redirect.html"}
        })
        st.write("👉 Cliquez :", res.url)

with col2:
    if st.button("🐙 GitHub Login"):
        res = supabase.auth.sign_in_with_oauth({
            "provider": "github",
            "options": {"redirect_to": "http://localhost:8502/oauth_redirect.html"}
        })
        st.write("👉 Cliquez :", res.url)

# ---------------------------------
# Déconnexion
# ---------------------------------
if st.session_state.user:
    st.subheader("Mon compte")
    st.write(f"Email : {st.session_state.user.email}")
    st.write(f"ID : {st.session_state.user.id}")

    if st.button("Se déconnecter"):
        supabase.auth.sign_out()
        st.session_state.user = None
        st.info("Déconnecté ✅")