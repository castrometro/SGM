# components/chatbot.py
import streamlit as st
from utils.llm import preguntar_ollama

def mostrar_chatbot():
    st.subheader("🤖 Chat de Análisis")
    
    # Inicializa el historial si no existe
    if "mensajes" not in st.session_state:
        st.session_state.mensajes = []

    # Mostrar historial
    for msg in st.session_state.mensajes:
        with st.chat_message(msg["rol"]):
            st.markdown(msg["contenido"])

    # Input del usuario
    prompt = st.chat_input("Haz una pregunta sobre el dashboard...")

    if prompt:
        # Mostrar el mensaje del usuario
        st.session_state.mensajes.append({"rol": "user", "contenido": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        # Responder con LLM
        with st.chat_message("assistant"):
            respuesta = preguntar_ollama(prompt)
            st.markdown(respuesta)
            st.session_state.mensajes.append({"rol": "assistant", "contenido": respuesta})
