import os
import pathlib
import time
from google import genai
from google.genai import types
import streamlit as st
import streamlit as st_pkg
from supabase import Client, create_client

logo_path = "logo.png" if os.path.exists("logo.png") else "✍️"
st.set_page_config(
    page_title="LyzAI Studio",
    page_icon=logo_path if os.path.exists("logo.png") else "✍️",
    layout="wide",
)

# ==========================================
# CONFIGURACIÓN E INYECCIÓN (ANALYTICS Y PWA)
# ==========================================
@st.cache_resource
def inject_pwa_and_analytics():
  try:
    st_dir = pathlib.Path(st_pkg.__file__).parent
    index_path = st_dir / "static" / "index.html"
    if index_path.exists():
      content = index_path.read_text(encoding="utf-8")

      pwa_ga_snippet = """
            <!-- Google tag (gtag.js) -->
            <script async src="https://www.googletagmanager.com/gtag/js?id=G-SE3F0436R"></script>
            <script>
              window.dataLayer = window.dataLayer || [];
              function gtag(){dataLayer.push(arguments);}
              gtag('js', new Date());
              gtag('config', 'G-SE3F0436R');
              gtag('config', 'GT-KTTZPP4C');
            </script>
            <!-- PWA Manifest & Icons -->
            <link rel="manifest" href="https://raw.githubusercontent.com/Neutrox08/lyz-ai/main/manifest.json">
            <link rel="icon" type="image/png" href="https://raw.githubusercontent.com/Neutrox08/lyz-ai/main/logo-512.png">
            <link rel="apple-touch-icon" href="https://raw.githubusercontent.com/Neutrox08/lyz-ai/main/logo-512.png">
            """

      if "G-SE3F0436R" not in content or "manifest.json" not in content:
        new_content = content.replace("</head>", f"{pwa_ga_snippet}</head>")
        index_path.write_text(new_content, encoding="utf-8")
  except Exception as e:
    print(f"Error al inyectar PWA/Analítica: {e}")


inject_pwa_and_analytics()

# ==========================================
# CONFIGURACIÓN SEGURA (SECRETS DE STREAMLIT)
# ==========================================
SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
GEMINI_API_KEY = st.secrets["GEMINI_API_KEY"]


def get_supabase_client() -> Client:
  if "supabase_client" not in st.session_state:
    st.session_state.supabase_client = create_client(SUPABASE_URL, SUPABASE_KEY)
  return st.session_state.supabase_client


def get_genai_client():
  if "genai_client" not in st.session_state:
    st.session_state.genai_client = genai.Client(api_key=GEMINI_API_KEY)
  return st.session_state.genai_client


def enviar_mensaje_seguro(chat_session, mensaje):
  max_intentos = 3
  for intento in range(max_intentos):
    try:
      return chat_session.send_message(mensaje)
    except Exception as e:
      if ("503" in str(e) or "UNAVAILABLE" in str(e)) and intento < max_intentos - 1:
        time.sleep(2)
        continue
      raise e


# ==========================================
# GESTIÓN DE ESTADOS DE NAVEGACIÓN Y SESIÓN
# ==========================================
if "user" not in st.session_state:
  st.session_state.user = None

if "app_view_mode" not in st.session_state:
  st.session_state.app_view_mode = "landing"

supabase = get_supabase_client()

# ==========================================
# 1. PANTALLA DE BIENVENIDA (PÚBLICA)
# ==========================================
if not st.session_state.user and st.session_state.app_view_mode == "landing":
  col1, col2, col3 = st.columns([1, 2, 1])
  with col2:
    if os.path.exists(logo_path):
      st.image(logo_path, width=100)
    else:
      st.markdown("# ✍️")

    st.title("LyzAI Studio — Asistente de Escritura Creativa")
    st.write("""
        Bienvenido a **LyzAI Studio**, tu plataforma impulsada por Inteligencia Artificial de clase mundial para dar vida a tus historias, novelas, poesía y guiones literarios. 
        Explora géneros como Fantasía, Ciencia Ficción, Romance, Thriller y mucho más con un co-creador inteligente en la nube.
        """)

    st.markdown("---")

    if st.button(
        "🚀 Comenzar / Iniciar Sesión", use_container_width=True, type="primary"
    ):
      st.session_state.app_view_mode = "auth"
      st.rerun()

    st.caption(
        "Plataforma interactiva de escritura creativa con almacenamiento seguro"
        " en la nube."
    )
  st.stop()

# ==========================================
# 2. PANTALLA DE AUTENTICACIÓN (LOGIN / REGISTRO)
# ==========================================
if not st.session_state.user and st.session_state.app_view_mode == "auth":
  col1, col2, col3 = st.columns([1, 2, 1])
  with col2:
    if os.path.exists(logo_path):
      st.image(logo_path, width=90)
    else:
      st.markdown("# ✍️")

    st.title("Acceso a LyzAI Studio")

    tab_login, tab_signup = st.tabs(["Iniciar Sesión", "Registrarse"])

    with tab_login:
      with st.form("login_form"):
        email_l = st.text_input("Correo electrónico", key="email_l")
        password_l = st.text_input("Contraseña", type="password", key="pass_l")
        submit_l = st.form_submit_button("Entrar", use_container_width=True)

        if submit_l:
          try:
            res = supabase.auth.sign_in_with_password(
                {"email": email_l, "password": password_l}
            )
            st.session_state.user = res.user
            st.success("¡Bienvenido de nuevo!")
            st.rerun()
          except Exception as e:
            st.error(f"Error al iniciar sesión: {e}")

    with tab_signup:
      with st.form("signup_form"):
        email_s = st.text_input("Correo electrónico", key="email_s")
        password_s = st.text_input(
            "Contraseña (mínimo 6 caracteres)", type="password", key="pass_s"
        )
        submit_s = st.form_submit_button(
            "Crear cuenta", use_container_width=True
        )

        if submit_s:
          try:
            res = supabase.auth.sign_up(
                {"email": email_s, "password": password_s}
            )
            st.success("¡Cuenta creada! Ya puedes iniciar sesión.")
          except Exception as e:
            st.error(f"Error al registrarse: {e}")

    st.write("")
    if st.button("⬅️ Volver al inicio"):
      st.session_state.app_view_mode = "landing"
      st.rerun()

  st.stop()

# ==========================================
# APLICACIÓN PRINCIPAL (USUARIO LOGUEADO)
# ==========================================
all_genres = [
    "Fantasía",
    "Ciencia Ficción",
    "Romance",
    "Misterio y Thriller",
    "Terror / Horror",
    "Ficción Histórica",
    "Aventura",
    "Drama",
    "Fanfic",
    "Poesía",
    "Ensayo / Filosofía",
    "Realismo Mágico",
    "Distopía",
]

if "chat" not in st.session_state:
  client = get_genai_client()
  system_instruction = """
    Eres "LyzAI", un asistente de escritura creativa de clase mundial, experto en narrativa, desarrollo de personajes, poesía y una enorme variedad de géneros literarios globales.
    REGLA DE ORO: Cuando un capítulo o título esté listo, incluye al final la etiqueta exacta: [GUARDAR_OBRA: Título | Género]
    """
  st.session_state.chat = client.chats.create(
      model="gemini-2.5-flash",
      config=types.GenerateContentConfig(
          system_instruction=system_instruction, temperature=0.7
      ),
  )

if "messages" not in st.session_state:
  st.session_state.messages = [{
      "role": "assistant",
      "content": (
          "¡Hola! Soy LyzAI, tu co-creador literario en la nube. ¿Qué obra"
          " fantástica vamos a crear hoy?"
      ),
  }]

if "current_work_genre" not in st.session_state:
  st.session_state.current_work_genre = None
if "favorite_shortcuts" not in st.session_state:
  st.session_state.favorite_shortcuts = [
      "Fantasía",
      "Ciencia Ficción",
      "Romance",
      "Misterio y Thriller",
  ]
if "current_view" not in st.session_state:
  st.session_state.current_view = "chat"


def cargar_biblioteca_nube():
  library = {genre: {} for genre in all_genres}
  try:
    response = (
        supabase.table("obras")
        .select("*")
        .eq("user_id", st.session_state.user.id)
        .execute()
    )
    for row in response.data:
      g = row["genero"]
      t = row["titulo"]
      c = row["contenido"]
      if g in library:
        library[g][t] = c
  except Exception as e:
    st.error(f"Error cargando la biblioteca: {e}")
  return library


with st.sidebar:
  if os.path.exists(logo_path):
    st.image(logo_path, width=70)

  st.title("LyzAI Menu")
  st.write(f"👤 `{st.session_state.user.email}`")

  if st.button("Cerrar Sesión", use_container_width=True, key="btn_cerrar_sesion_sidebar"):
    supabase.auth.sign_out()
    st.session_state.user = None
    st.session_state.app_view_mode = "landing"
    st.rerun()

  if st.button("💬 Nueva Conversación", use_container_width=True, key="btn_nueva_conv_sidebar"):
    client = get_genai_client()
    system_instruction = (
        "Eres LyzAI, un asistente de escritura creativa de clase mundial."
    )
    st.session_state.chat = client.chats.create(
        model="gemini-2.5-flash",
        config=types.GenerateContentConfig(
            system_instruction=system_instruction, temperature=0.7
        ),
    )
    st.session_state.messages = [{
        "role": "assistant",
        "content": "¡Nueva conversación iniciada!",
    }]
    st.session_state.current_work_genre = None
    st.session_state.current_view = "chat"
    st.rerun()

  st.markdown("---")
  st.markdown("### 📚 Biblioteca en la Nube")

  library_data = cargar_biblioteca_nube()
  for genre in all_genres:
    works_dict = library_data.get(genre, {})
    count = len(works_dict)
    if st.button(
        f"📖 {genre} ({count})",
        use_container_width=True,
        key=f"lib_btn_{genre}",
    ):
      st.session_state.current_view = genre
      st.rerun()

if st.session_state.current_view == "modifier":
  st.title("⚙️ Personalizar Accesos Directos")
  with st.form("shortcut_form"):
    selected_choices = st.multiselect(
        "Elige exactamente 4 géneros favoritos:",
        options=all_genres,
        default=st.session_state.favorite_shortcuts,
        max_selections=4,
    )
    submitted = st.form_submit_button("Guardar Cambios")
    if submitted:
      if len(selected_choices) == 4:
        st.session_state.favorite_shortcuts = selected_choices
        st.success("¡Actualizado con éxito!")
        st.session_state.current_view = "chat"
        st.rerun()
      else:
        st.error("Selecciona exactamente 4 géneros.")
  if st.button("⬅️ Volver al Chat", key="btn_volver_chat_mod"):
    st.session_state.current_view = "chat"
    st.rerun()

elif st.session_state.current_view in all_genres:
  genre = st.session_state.current_view
  st.title(f"📚 Estante de {genre}")
  works_dict = library_data.get(genre, {})
  if not works_dict:
    st.info(f"Aún no hay obras en {genre}.")
  else:
    for title, content in list(works_dict.items()):
      with st.container(border=True):
        st.subheader(f"📖 {title}")
        st.text_area(
            "Contenido:",
            value=content[:300] + "...",
            height=100,
            disabled=True,
            key=f"prev_{genre}_{title}",
        )
        col1, col2 = st.columns(2)
        with col1:
          st.download_button(
              "📥 Descargar TXT",
              data=content,
              file_name=f"{title}.txt",
              mime="text/plain",
              key=f"dl_{genre}_{title}",
          )
        with col2:
          if st.button("🗑️ Eliminar", key=f"del_{genre}_{title}"):
            (
                supabase.table("obras")
                .delete()
                .eq("user_id", st.session_state.user.id)
                .eq("titulo", title)
                .execute()
            )
            st.success("Obra eliminada.")
            st.rerun()
  st.write("")
  if st.button("⬅️ Volver al Chat", key=f"btn_volver_chat_estante_{genre}"):
    st.session_state.current_view = "chat"
    st.rerun()

else:
  if os.path.exists(logo_path):
    st.image(logo_path, width=80)

  st.title("LyzAI")
  st.caption("Tu asistente de escritura creativa en la nube")

  st.write("### 🚀 Accesos Directos Favoritos")
  cols = st.columns(5)
  selected_prompt = None
  favs = st.session_state.favorite_shortcuts

  for i in range(4):
    with cols[i]:
      genre_name = favs[i]
      if st.button(f"📖 {genre_name}", use_container_width=True, key=f"fav_btn_{i}_{genre_name}"):
        selected_prompt = (
            f"Quiero escribir una obra del género {genre_name}. Guíame paso a"
            " paso."
        )
        st.session_state.current_work_genre = genre_name

  with cols[4]:
    if st.button("⚙️ Modificar", use_container_width=True, key="btn_modificar_favs"):
      st.session_state.current_view = "modifier"
      st.rerun()

  st.write("---")

  for message in st.session_state.messages:
    with st.chat_message(message["role"]):
      st.markdown(message["content"])

  if selected_prompt:
    st.session_state.messages.append(
        {"role": "user", "content": selected_prompt}
    )
    with st.chat_message("user"):
      st.markdown(selected_prompt)
    with st.chat_message("assistant"):
      with st.spinner("Conectando..."):
        response = enviar_mensaje_seguro(
            st.session_state.chat, selected_prompt
        )
        st.markdown(response.text)
        st.session_state.messages.append(
            {"role": "assistant", "content": response.text}
        )
    st.rerun()

  if prompt := st.chat_input("Escribe tu mensaje..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
      st.markdown(prompt)

    with st.chat_message("assistant"):
      with st.spinner("LyzAI está escribiendo..."):
        try:
          response = enviar_mensaje_seguro(st.session_state.chat, prompt)
          text = response.text

          if "[GUARDAR_OBRA:" in text:
            try:
              tag = text.split("[GUARDAR_OBRA:")[1].split("]")[0].strip()
              if "|" in tag:
                t_det, g_det = [p.strip() for p in tag.split("|", 1)]
                if g_det in all_genres:
                  contenido_total = "\n".join([
                      f"{m['role'].upper()}: {m['content']}"
                      for m in st.session_state.messages
                  ])
                  (
                      supabase.table("obras")
                      .upsert(
                          {
                              "user_id": st.session_state.user.id,
                              "titulo": t_det,
                              "genero": g_det,
                              "contenido": contenido_total,
                          },
                          on_conflict="user_id,titulo",
                      )
                      .execute()
                  )
                  text = text.replace(
                      f"[GUARDAR_OBRA: {tag}]",
                      "\n\n✨ *[Guardado automáticamente en Supabase]*",
                  )
            except Exception as ex:
              print(ex)

          st.markdown(text)
          st.session_state.messages.append(
              {"role": "assistant", "content": text}
          )
        except Exception as e:
          error_msg = f"⚠️ Error: {e}"
          st.error(error_msg)
          st.session_state.messages.append(
              {"role": "assistant", "content": error_msg}
          )
