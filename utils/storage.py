from datetime import datetime, timezone

import firebase_admin
import streamlit as st
from firebase_admin import credentials, db


@st.cache_resource
def initialize_firebase(service_account_path: str, database_url: str):
    """Inicializa o Firebase Admin SDK se ainda não foi inicializado."""
    try:
        if not firebase_admin._apps:
            print("Inicializando Firebase Admin SDK...")
            cred = credentials.Certificate(service_account_path)
            firebase_admin.initialize_app(cred, {
                'databaseURL': database_url
            })
            print("Firebase Admin SDK inicializado com sucesso.")
            return True
        else:
            print("Firebase Admin SDK já estava inicializado.")
            return True
    except ValueError as ve:
        if "The default Firebase app already exists" in str(ve):
            print("Firebase Admin SDK já estava inicializado (capturado por ValueError).")
            return True
        else:
            print(f"Erro de valor ao inicializar Firebase: {ve}")
            st.error(f"Erro de configuração do Firebase: {ve}")
            return False
    except FileNotFoundError:
        print(f"Erro: Arquivo de credenciais não encontrado em '{service_account_path}'")
        st.error(
            f"Erro Crítico: Arquivo de credenciais do Firebase não encontrado em '{service_account_path}'. Verifique o caminho no .env.")
        return False
    except Exception as e:
        print(f"Erro inesperado ao inicializar Firebase: {e}")
        st.error(f"Erro inesperado ao conectar com o Firebase: {e}")
        return False


def save_user_profile_rtdb(user_data: dict) -> bool:
    """Salva o perfil do usuário no Firebase Realtime Database."""
    try:
        ref = db.reference('users')

        payload = {
            "first_name": user_data.get("first_name"),
            "last_name": user_data.get("last_name"),
            "city": user_data.get("city"),
            "fav_game": user_data.get("fav_game"),
            "nickname": user_data.get("nickname"),
            "role": user_data.get("role"),
            "playstyle_desc": user_data.get("playstyle_desc"),
            "watched_champs": user_data.get("watched_champs"),
            "instagram_handle": user_data.get("instagram_handle") if user_data.get("instagram_handle") else None,
            "verification_status": user_data.get("verification_status"),
            "created_at": datetime.now(timezone.utc).isoformat(),
            "match_player_name": user_data.get("match_result", {}).get("name") if user_data.get(
                "match_result") else None,
            "match_score": user_data.get("match_result", {}).get("score") if user_data.get("match_result") else None
        }

        payload_cleaned = {k: v for k, v in payload.items() if v is not None}

        new_user_ref = ref.push(payload_cleaned)
        print(f"Perfil do usuário salvo no Realtime Database com ID: {new_user_ref.key}")
        return True

    except Exception as e:
        print(f"Erro ao salvar perfil no Firebase Realtime Database: {e}")
        st.error(f"Erro ao salvar seu perfil no banco de dados: {e}")
        return False
