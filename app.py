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
    print(f"Aviso técnico al inyectar PWA/Analítica: {e}")

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
      if ("503" in str(e) or "UNAVAILABLE" in str(e) or "429" in str(e)) and intento < max_intentos - 1:
        time.sleep(2)
        continue
      raise e

# ==========================================
# ESTRUCTURA DE CATEGORÍAS Y GÉNEROS
# ==========================================
library_categories = {
    "Libros": ["Fantasía", "Ciencia Ficción", "Ficción Histórica", "Distopía"],
    "Poemas": ["Poesía"],
    "Fanfics": ["Fanfic"],
    "Cuentos": ["Realismo Mágico", "Terror / Horror", "Aventura"],
    "Historias Cortas": ["Romance", "Misterio y Thriller", "Drama", "Ensayo / Filosofía"]
}

all_genres = [g for sublist in library_categories.values() for g in sublist]

supabase = get_supabase_client()

# ==========================================
# GESTIÓN DE SESIÓN Y PERSISTENCIA ROBUSTA
# ==========================================
if "user" not in st.session_state:
  st.session_state.user = None
  try:
    session_res = supabase.auth.get_session()
    if session_res and session_res.user:
      st.session_state.user = session_res.user
  except Exception:
    pass

if not st.session_state.user:
  try:
    current_session = supabase.auth.get_session()
    if current_session and current_session.user:
      st.session_state.user = current_session.user
  except Exception:
    pass

query_params = st.query_params

if "app_view_mode" not in st.session_state:
  default_mode = "app" if st.session_state.user else "landing"
  st.session_state.app_view_mode = query_params.get("app_view_mode", default_mode)

if "current_view" not in st.session_state:
  st.session_state.current_view = query_params.get("current_view", "chat")

if "is_editing_work" not in st.session_state:
  st.session_state.is_editing_work = False

def cambiar_estado_vista(app_mode, current_v):
  st.session_state.app_view_mode = app_mode
  st.session_state.current_view = current_v
  st.query_params["app_view_mode"] = app_mode
  st.query_params["current_view"] = current_v
  st.rerun()

if st.session_state.user:
  st.session_state.app_view_mode = "app"
  st.query_params["app_view_mode"] = "app"

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
        Bienvenido a **LyzAI Studio**, tu plataforma impulsada por Inteligencia Artificial para dar vida a tus historias, novelas, poesía y guiones literarios de forma organizada.
        """)
    st.markdown("---")
    if st.button("🚀 Comenzar / Iniciar Sesión", use_container_width=True, type="primary"):
      cambiar_estado_vista("auth", "chat")
  st.stop()

# ==========================================
# 2. PANTALLA DE AUTENTICACIÓN
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
        mantener_sesion = st.checkbox("Mantener sesión iniciada", value=True, key="mantener_sesion_chk")
        
        submit_l = st.form_submit_button("Entrar", use_container_width=True)
        if submit_l:
          try:
            res = supabase.auth.sign_in_with_password({"email": email_l, "password": password_l})
            st.session_state.user = res.user
            if res.session:
              supabase.auth.set_session(res.session.access_token, res.session.refresh_token)
            
            if mantener_sesion:
              st.toast("🔒 Sesión guardada de forma persistente.")

            st.success("¡Bienvenido de nuevo!")
            cambiar_estado_vista("app", "chat")
          except Exception as e:
            st.warning(f"No se pudo iniciar sesión. Verifica tus credenciales (Detalle: {e})")

    with tab_signup:
      with st.form("signup_form"):
        email_s = st.text_input("Correo electrónico", key="email_s")
        password_s = st.text_input("Contraseña (mínimo 6 caracteres)", type="password", key="pass_s")
        submit_s = st.form_submit_button("Crear cuenta", use_container_width=True)
        if submit_s:
          try:
            supabase.auth.sign_up({"email": email_s, "password": password_s})
            st.success("¡Cuenta creada con éxito! Ya puedes iniciar sesión.")
          except Exception as e:
            st.warning(f"Hubo un problema al registrar la cuenta: {e}")

    st.write("")
    if st.button("⬅️ Volver al inicio"):
      cambiar_estado_vista("landing", "chat")
  st.stop()

if not st.session_state.user:
  cambiar_estado_vista("landing", "chat")

# ==========================================
# CARGAR PREFERENCIAS DE USUARIO DESDE SUPABASE
# ==========================================
def cargar_preferencias_usuario():
  default_favs = ["Fantasía", "Ciencia Ficción", "Romance", "Misterio y Thriller"]
  try:
    res = supabase.table("preferencias_usuario").select("favoritos").eq("user_id", st.session_state.user.id).execute()
    if res.data and len(res.data) > 0 and "favoritos" in res.data[0]:
      favs = res.data[0]["favoritos"]
      if isinstance(favs, list) and len(favs) == 4:
        return favs
  except Exception:
    pass
  return default_favs

def guardar_preferencias_usuario(favs):
  try:
    supabase.table("preferencias_usuario").upsert({
        "user_id": st.session_state.user.id,
        "favoritos": favs
    }, on_conflict="user_id").execute()
  except Exception as e:
    st.info(f"Aviso de sincronización de preferencias: {e}")

if "favorite_shortcuts" not in st.session_state:
  st.session_state.favorite_shortcuts = cargar_preferencias_usuario()

if "chat" not in st.session_state:
  client = get_genai_client()
  system_instruction = """
    Eres "LyzAI", un asistente de escritura creativa de clase mundial.
    Ayuda al usuario a desarrollar sus historias, capítulos y novelas de manera creativa y fluida.
    """
  st.session_state.chat = client.chats.create(
      model="gemini-3.6-flash",
      config=types.GenerateContentConfig(system_instruction=system_instruction, temperature=0.7),
  )

if "messages" not in st.session_state:
  st.session_state.messages = [{
      "role": "assistant",
      "content": "¡Hola! Soy LyzAI, tu co-creador literario en la nube. ¿Qué obra fantástica vamos a crear hoy?",
  }]

if "current_conversation_title" not in st.session_state:
  st.session_state.current_conversation_title = "Nueva Conversación"

if "current_genre" not in st.session_state:
  st.session_state.current_genre = "Fantasía"

def cargar_biblioteca_nube():
  library = {genre: {} for genre in all_genres}
  try:
    response = supabase.table("obras").select("*").eq("user_id", st.session_state.user.id).execute()
    for row in response.data:
      g = row["genero"]
      t = row["titulo"]
      c = row["contenido"]
      if g in library:
        library[g][t] = c
  except Exception as e:
    st.info(f"Nota informativa al cargar la biblioteca: {e}")
  return library

def cargar_historial_conversaciones():
  historial = []
  try:
    res = supabase.table("historial_chats").select("*").eq("user_id", st.session_state.user.id).order("ultima_fecha", desc=True).execute()
    if res.data:
      historial = res.data
  except Exception as e:
    st.info(f"Nota informativa al cargar historial: {e}")
  return historial

def guardar_conversacion_actual(tema_str):
  try:
    import datetime
    hoy = datetime.datetime.now().strftime("%Y-%m-%d")
    contenido_total = "\n".join([f"{m['role'].upper()}: {m['content']}" for m in st.session_state.messages])
    supabase.table("historial_chats").upsert({
        "user_id": st.session_state.user.id,
        "tema": tema_str,
        "ultima_fecha": hoy,
        "contenido": contenido_total
    }, on_conflict="user_id,tema").execute()
  except Exception as e:
    print(f"Error menor guardando historial: {e}")

# ==========================================
# BARRA LATERAL (MENU Y BIBLIOTECA)
# ==========================================
with st.sidebar:
  if os.path.exists(logo_path):
    st.image(logo_path, width=70)
  else:
    st.markdown("# ✍️")

  st.title("LyzAI Menu")
  
  if st.session_state.user and hasattr(st.session_state.user, "email"):
    st.write(f"👤 `{st.session_state.user.email}`")
  else:
    st.write("👤 `Sesión activa`")

  if st.button("Cerrar Sesión", use_container_width=True, key="btn_cerrar_sesion_sidebar"):
    try:
      supabase.auth.sign_out()
    except Exception:
      pass
    st.session_state.user = None
    st.session_state.is_editing_work = False
    cambiar_estado_vista("landing", "chat")

  if st.button("💬 Nueva Conversación", use_container_width=True, key="btn_nueva_conv_sidebar"):
    client = get_genai_client()
    system_instruction = "Eres LyzAI, un asistente de escritura creativa de clase mundial."
    st.session_state.chat = client.chats.create(
        model="gemini-3.6-flash",
        config=types.GenerateContentConfig(system_instruction=system_instruction, temperature=0.7),
    )
    st.session_state.messages = [{
        "role": "assistant",
        "content": "¡Nueva conversación iniciada!",
    }]
    st.session_state.current_conversation_title = "Nueva Conversación"
    st.session_state.current_genre = "Fantasía"
    st.session_state.is_editing_work = False
    cambiar_estado_vista("app", "chat")

  st.markdown("---")
  st.markdown("### 📚 Biblioteca en la Nube")
  library_data = cargar_biblioteca_nube()

  for cat_name, genres_in_cat in library_categories.items():
    with st.expander(f"📁 {cat_name}"):
      for genre in genres_in_cat:
        works_dict = library_data.get(genre, {})
        count = len(works_dict)
        if st.button(f"📖 {genre} ({count})", use_container_width=True, key=f"lib_btn_{genre}"):
          cambiar_estado_vista("app", genre)

  st.markdown("---")
  st.markdown("### 🕒 Historial por Días y Temas")
  historial_chats = cargar_historial_conversaciones()
  if not historial_chats:
    st.caption("Aún no hay chats guardados.")
  else:
    for h in historial_chats[:5]:
      fecha = h.get("ultima_fecha", "Sin fecha")
      tema = h.get("tema", "Sin tema")
      contenido_guardado = h.get("contenido", "")

      if st.button(f"📅 {fecha} — {tema}", use_container_width=True, key=f"hist_{h.get('id', tema)}"):
        mensajes_reconstruidos = []
        if contenido_guardado:
          lineas = contenido_guardado.split("\n")
          for linea in lineas:
            if linea.startswith("USER:"):
              mensajes_reconstruidos.append({
                  "role": "user",
                  "content": linea.replace("USER:", "").strip(),
              })
            elif linea.startswith("ASSISTANT:"):
              mensajes_reconstruidos.append({
                  "role": "assistant",
                  "content": linea.replace("ASSISTANT:", "").strip(),
              })

        if mensajes_reconstruidos:
          st.session_state.messages = mensajes_reconstruidos
        else:
          st.session_state.messages = [{
              "role": "assistant",
              "content": f"Conversación recuperada del tema: *{tema}* ({fecha})",
          }]

        st.session_state.current_conversation_title = tema
        st.session_state.is_editing_work = False
        cambiar_estado_vista("app", "chat")

# ==========================================
# VISTAS PRINCIPALES
# ==========================================
if st.session_state.current_view == "modifier":
  st.title("⚙️ Personalizar Accesos Directos Favoritos")
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
        guardar_preferencias_usuario(selected_choices)
        st.success("¡Tus accesos directos favoritos se han guardado permanentemente!")
        cambiar_estado_vista("app", "chat")
      else:
        st.warning("Debes seleccionar exactamente 4 géneros para continuar.")
  if st.button("⬅️ Volver al Chat", key="btn_volver_chat_mod"):
    cambiar_estado_vista("app", "chat")

elif st.session_state.current_view in all_genres:
  genre = st.session_state.current_view
  st.title(f"📚 Estante de {genre}")
  works_dict = library_data.get(genre, {})
  if not works_dict:
    st.info(f"Aún no hay obras registradas en el género {genre}.")
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
        col1, col2, col3 = st.columns(3)
        with col1:
          st.download_button(
              "📥 Descargar TXT",
              data=content,
              file_name=f"{title}.txt",
              mime="text/plain",
              key=f"dl_{genre}_{title}",
          )
        with col2:
          if st.button("✏️ Editar en Chat", key=f"edit_{genre}_{title}"):
            mensajes_reconstruidos = []
            lineas = content.split("\n")
            for linea in lineas:
              if linea.startswith("USER:"):
                mensajes_reconstruidos.append({
                    "role": "user",
                    "content": linea.replace("USER:", "").strip(),
                })
              elif linea.startswith("ASSISTANT:"):
                mensajes_reconstruidos.append({
                    "role": "assistant",
                    "content": linea.replace("ASSISTANT:", "").strip(),
                })
            
            if mensajes_reconstruidos:
              st.session_state.messages = mensajes_reconstruidos
            else:
              st.session_state.messages = [{
                  "role": "assistant",
                  "content": content,
              }]
            
            st.session_state.current_conversation_title = title
            st.session_state.current_genre = genre
            st.session_state.is_editing_work = True
            cambiar_estado_vista("app", "chat")

        with col3:
          if st.button("🗑️ Eliminar", key=f"del_{genre}_{title}"):
            try:
              supabase.table("obras").delete().eq("user_id", st.session_state.user.id).eq("titulo", title).execute()
              st.success("Obra eliminada correctamente.")
              st.rerun()
            except Exception as e:
              st.warning(f"No se pudo eliminar la obra: {e}")
  st.write("")
  if st.button("⬅️ Volver al Chat", key=f"btn_volver_chat_estante_{genre}"):
    cambiar_estado_vista("app", "chat")

else:
  if os.path.exists(logo_path):
    st.image(logo_path, width=80)
  else:
    st.markdown("# ✍️")

  st.title("LyzAI")
  st.caption("Tu asistente de escritura creativa en la nube")

  st.write("### 🚀 Accesos Directos Favoritos")
  cols = st.columns(5)
  selected_prompt = None
  favs = st.session_state.favorite_shortcuts

  for i in range(4):
    with cols[i]:
      genre_name = favs[i] if i < len(favs) else all_genres[i]
      if st.button(f"📖 {genre_name}", use_container_width=True, key=f"fav_btn_{i}_{genre_name}"):
        selected_prompt = f"Quiero escribir una obra del género {genre_name}. Guíame paso a paso."
        st.session_state.current_conversation_title = f"Obra de {genre_name}"
        st.session_state.current_genre = genre_name
        st.session_state.is_editing_work = False

  with cols[4]:
    if st.button("⚙️ Modificar", use_container_width=True, key="btn_modificar_favs"):
      cambiar_estado_vista("app", "modifier")

  st.write("---")

  # ==========================================
  # PANEL AUTOMÁTICO DE GUARDADO DE OBRA
  # ==========================================
  with st.container(border=True):
    col_g1, col_g2, col_g3 = st.columns([2, 2, 1])
    with col_g1:
      input_titulo_obra = st.text_input("Título de la obra:", value=st.session_state.current_conversation_title, key="input_titulo_obra_auto")
    with col_g2:
      input_genero_obra = st.selectbox("Género de la obra:", options=all_genres, index=all_genres.index(st.session_state.current_genre) if st.session_state.current_genre in all_genres else 0, key="select_genero_obra_auto")
    with col_g3:
      st.write("")
      st.write("")
      if st.button("💾 Guardar Obra", type="primary", use_container_width=True, key="btn_guardar_obra_automatico"):
        try:
          contenido_total = "\n".join([f"{m['role'].upper()}: {m['content']}" for m in st.session_state.messages])
          
          existing = supabase.table("obras").select("id").eq("user_id", st.session_state.user.id).eq("titulo", input_titulo_obra).execute()
          
          if existing.data and len(existing.data) > 0:
            if st.session_state.is_editing_work:
              supabase.table("obras").update({
                  "genero": input_genero_obra,
                  "contenido": contenido_total,
              }).eq("user_id", st.session_state.user.id).eq("titulo", input_titulo_obra).execute()
              st.success(f"✨ ¡Obra '{input_titulo_obra}' actualizada correctamente!")
            else:
              st.error(f"⚠️ Ya existe una obra registrada con el título '{input_titulo_obra}'. Elige otro título o edita la obra existente desde su estante.")
          else:
            supabase.table("obras").insert({
                "user_id": st.session_state.user.id,
                "titulo": input_titulo_obra,
                "genero": input_genero_obra,
                "contenido": contenido_total,
            }).execute()
            st.session_state.is_editing_work = True
            st.success(f"✨ ¡Obra '{input_titulo_obra}' guardada en el estante de {input_genero_obra}!")
        except Exception as ex:
          st.warning(f"No se pudo guardar la obra: {ex}")

  st.write("---")

  for message in st.session_state.messages:
    with st.chat_message(message["role"]):
      st.markdown(message["content"])

  if selected_prompt:
    st.session_state.messages.append({"role": "user", "content": selected_prompt})
    with st.chat_message("user"):
      st.markdown(selected_prompt)
    with st.chat_message("assistant"):
      with st.spinner("Conectando con la IA..."):
        try:
          response = enviar_mensaje_seguro(st.session_state.chat, selected_prompt)
          text_resp = response.text
          st.markdown(text_resp)
          st.session_state.messages.append({"role": "assistant", "content": text_resp})
          guardar_conversacion_actual(st.session_state.current_conversation_title)
        except Exception as e:
          st.warning(f"Tuvimos un inconveniente al procesar tu solicitud: {e}. Intenta nuevamente en unos segundos.")
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

          st.markdown(text)
          st.session_state.messages.append({"role": "assistant", "content": text})
          guardar_conversacion_actual(st.session_state.current_conversation_title)
        except Exception as e:
          error_msg = f"⚠️ Nota del sistema: Ocurrió un detalle técnico temporal ({e}). Por favor, reintenta enviar tu mensaje."
          st.warning(error_msg)
          st.session_state.messages.append({"role": "assistant", "content": error_msg})
