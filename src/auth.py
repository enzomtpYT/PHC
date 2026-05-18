import streamlit as st
from database import verify_user, create_user
from passlib.hash import argon2

ALLOW_REGISTRATION = True


# -----------------------
# SESSION INIT
# -----------------------
def init_session():
    st.session_state.setdefault("authenticated", False)
    st.session_state.setdefault("username", None)
    st.session_state.setdefault("auth_mode", "login")


# -----------------------
# HELPERS
# -----------------------
def sanitize_username(username: str) -> str:
    return (username or "").strip()


def hash_password(password: str) -> str:
    return argon2.hash(password)


def verify_password(password: str, hashed: str) -> bool:
    return argon2.verify(password, hashed)


def validate_password(password: str) -> tuple[bool, str]:
    if not password:
        return False, "Mot de passe vide"

    if len(password) < 4:
        return False, "Mot de passe trop court"

    return True, ""


# -----------------------
# LOGIN
# -----------------------
def login():
    st.title("🔐 Connexion")

    username = sanitize_username(st.text_input("Utilisateur", key="login_user"))
    password = st.text_input("Mot de passe", type="password", key="login_pass")

    if st.button("Se connecter"):
        if not username or not password:
            st.error("Champs obligatoires")
            return

        try:
            # ✅ appel correct
            if verify_user(username, password):
                st.session_state.authenticated = True
                st.session_state.username = username
                st.rerun()
            else:
                st.error("Identifiants incorrects")

        except Exception as e:
            st.error(f"Erreur login: {e}")

    if ALLOW_REGISTRATION:
        if st.button("Créer un compte"):
            st.session_state.auth_mode = "register"
            st.rerun()


# -----------------------
# REGISTER
# -----------------------
def register():
    st.title("📝 Création de compte")

    username = sanitize_username(st.text_input("Utilisateur", key="reg_user"))
    password = st.text_input("Mot de passe", type="password", key="reg_pass")
    confirm = st.text_input("Confirmer", type="password", key="reg_confirm")

    if st.button("Créer le compte"):

        if not username:
            st.error("Username requis")
            return

        ok, msg = validate_password(password)
        if not ok:
            st.error(msg)
            return

        if password != confirm:
            st.error("Les mots de passe ne correspondent pas")
            return

        try:
            hashed = hash_password(password)

            success = create_user(username, hashed)

            if success:
                st.success("Compte créé avec succès")
                st.session_state.auth_mode = "login"
                st.rerun()
            else:
                st.error("Utilisateur déjà existant")

        except Exception as e:
            st.error(f"Erreur création compte: {e}")


    if st.button("Retour connexion"):
        st.session_state.auth_mode = "login"
        st.rerun()


# -----------------------
# LOGOUT
# -----------------------
def logout():
    st.session_state.authenticated = False
    st.session_state.username = None
    st.rerun()


# -----------------------
# MAIN AUTH
# -----------------------
def require_auth():
    init_session()

    if not st.session_state.authenticated:
        if st.session_state.auth_mode == "login":
            login()
        else:
            register()
        return False

    st.sidebar.write(f"👤 {st.session_state.username}")

    if st.sidebar.button("Logout"):
        logout()

    return True