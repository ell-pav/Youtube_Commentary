from supabase import create_client

from dotenv import load_dotenv

import os


load_dotenv()


supabase = create_client(
    os.getenv("SUPABASE_URL"),
    os.getenv("SUPABASE_KEY")
)


def sign_up(
    email,
    password
):

    return supabase.auth.sign_up(
        {
            "email": email,
            "password": password
        }
    )


def sign_in(
    email,
    password
):

    return supabase.auth.sign_in_with_password(
        {
            "email": email,
            "password": password
        }
    )