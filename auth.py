from database import create_client
import os
from dotenv import load_dotenv

load_dotenv()
url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_KEY_RLS")

supabase = create_client(url, key)

# Créer un utilisateur avec email + mot de passe
auth_response = supabase.auth.admin.create_user({
    "email": "testuser@example.com",
    "password": "MotDePasseUltraSecret123!",
    "email_confirm": True  # utile pour éviter la confirmation par mail
})

print(auth_response)