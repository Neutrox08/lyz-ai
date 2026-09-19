import os
import streamlit as st
from supabase import create_client, Client

# ==========================================
# CONFIGURACIÓN DE PÁGINA
# ==========================================
st.set_page_config(
    page_title="Asistente de Productividad y Chat",
    page_icon="🤖",
    layout="wide"
)

# ==========================================
# CONFIGURACIÓN DE SUPABASE
# ==========================================
SUPABASE_URL = os.getenv("SUPABASE_URL", "TU_SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "TU_SUPABASE_ANON_KEY")

@st.cache_resource
def get_supabase_client() -> Client:
    return create_client(SUPABASE_URL, SUPABASE_KEY)

supabase = get_supabase_client()

# ==========================================
# GESTIÓN DE SESIÓN Y PERSISTENCIA ROBUSTA (F5 FIX)
# ==========================================
if "user" not in st.session_state:
    st.session_state.user = None

# Intento múltiple de recuperación de sesión activa al recargar (F5)
if not st.session_state.user:
    try:
        # 1. Intentar obtener la sesión activa actual del cliente de Supabase
        current_session = supabase.auth.get_session()
        if current_session and current_session.user:
            st.session_state.user = current_session.user
        else:
            # 2. Intentar recuperar mediante el usuario activo almacenado
            user_res = supabase.auth.get_user()
            if user_res and user_res.user:
                st.session_state.user = user_res.user
    except Exception:
        pass

query_params = st.query_params

if "app_view_mode" not in st.session_state:
    default_mode = "app" if st.session_state.user else "landing"
    st.session_state.app_view_mode = query_params.get("app_view_mode", default_mode)

if "current_view" not in st.session_state:
    st.session_state.current_view = query_params.get("current_view", "chat")

def cambiar_estado_vista(app_mode, current_v):
    st.session_state.app_view_mode = app_mode
    st.session_state.current_view = current_v
    st.query_params["app_view_mode"] = app_mode
    st.query_params["current_view"] = current_v
    st.rerun()

# FORZAR MODO APP si el usuario ya está autenticado (Garantiza que F5 no devuelva al login)
if st.session_state.user:
    st.session_state.app_view_mode = "app"
    st.query_params["app_view_mode"] = "app"

# ==========================================
# COMPONENTES DE INTERFAZ: LOGIN / LANDING
# ==========================================
def render_landing_or_login():
    st.title("Bienvenido a tu Asistente Inteligente")
    st.write("Inicia sesión o regístrate para continuar.")
    
    tab_login, tab_signup = st.tabs(["Iniciar Sesión", "Registrarse"])
    
    with tab_login:
        st.subheader("Acceso")
        login_email = st.text_input("Correo Electrónico", key="login_email")
        login_password = st.text_input("Contraseña", type="password", key="login_password")
        
        if st.button("Entrar", type="primary"):
            try:
                response = supabase.auth.sign_in_with_password({
                    "email": login_email,
                    "password": login_password
                })
                if response.user:
                    st.session_state.user = response.user
                    st.session_state.app_view_mode = "app"
                    st.query_params["app_view_mode"] = "app"
                    st.success("¡Inicio de sesión exitoso!")
                    st.rerun()
            except Exception as e:
                st.error(f"Error al iniciar sesión: {e}")

    with tab_signup:
        st.subheader("Crear una cuenta nueva")
        signup_email = st.text_input("Correo Electrónico", key="signup_email")
        signup_password = st.text_input("Contraseña", type="password", key="signup_password")
        
        if st.button("Registrarse", type="secondary"):
            try:
                response = supabase.auth.sign_up({
                    "email": signup_email,
                    "password": signup_password
                })
                if response.user:
                    st.success("¡Registro exitoso! Por favor verifica tu correo o inicia sesión.")
            except Exception as e:
                st.error(f"Error en el registro: {e}")

# ==========================================
# APLICACIÓN PRINCIPAL (AUTENTICADO)
# ==========================================
def render_main_app():
    # Barra lateral de navegación
    with st.sidebar:
        st.write(f"👤 **Usuario:** {st.session_state.user.email}")
        st.divider()
        
        if st.button("💬 Chat con IA", use_container_width=True):
            cambiar_estado_vista("app", "chat")
            
        if st.button("📚 Biblioteca / Documentos", use_container_width=True):
            cambiar_estado_vista("app", "library")
            
        st.divider()
        if st.button("Cerrar Sesión", type="secondary", use_container_width=True):
            try:
                supabase.auth.sign_out()
            except Exception:
                pass
            st.session_state.user = None
            st.session_state.app_view_mode = "landing"
            st.query_params["app_view_mode"] = "landing"
            st.rerun()

    # Enrutamiento interno de vistas principales
    if st.session_state.current_view == "chat":
        st.title("💬 Chat Asistente")
        st.write("Escribe tus consultas aquí abajo:")
        
        # Simulación de historial de chat básico
        if "messages" not in st.session_state:
            st.session_state.messages = []
            
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])
                
        if prompt := st.chat_input("¿En qué puedo ayudarte hoy?"):
            st.session_state.messages.append({"role": "user", "content": prompt})
            with st.chat_message("user"):
                st.markdown(prompt)
                
            assistant_response = f"Respuesta simulada a: '{prompt}'"
            st.session_state.messages.append({"role": "assistant", "content": assistant_response})
            with st.chat_message("assistant"):
                st.markdown(assistant_response)

    elif st.session_state.current_view == "library":
        st.title("📚 Biblioteca de Documentos")
        st.write("Aquí puedes gestionar tus archivos guardados y notas.")
        st.info("No hay documentos subidos todavía.")

# ==========================================
# CONTROLADOR GENERAL DE VISTAS
# ==========================================
if st.session_state.app_view_mode == "landing" or not st.session_state.user:
    render_landing_or_login()
else:
    render_main_app()
