import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
import numpy as np
import os
import base64
import json
import requests

def save_question_to_github(question):
    try:
        # Configuración de GitHub
        github_token = st.secrets["github"]["token"]
        repo_name = "alejoherrera/chatbot_obra"
        file_path = "data/preguntas.csv"
        
        # Headers para la API de GitHub
        headers = {
            "Authorization": f"token {github_token}",
            "Accept": "application/vnd.github.v3+json"
        }

        # URL de la API
        url = f"https://api.github.com/repos/{repo_name}/contents/{file_path}"

        try:
            # Intentar obtener el archivo existente
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            
            # Decodificar el contenido existente
            content = base64.b64decode(response.json()["content"]).decode("utf-8")
            sha = response.json()["sha"]
            
            # Convertir el contenido a DataFrame
            df = pd.read_csv(pd.StringIO(content))
            st.success("Archivo de preguntas existente cargado correctamente")
        except Exception as e:
            # Si el archivo no existe, crear un DataFrame nuevo
            st.info("Creando nuevo archivo de preguntas")
            df = pd.DataFrame(columns=['fecha', 'pregunta'])
            sha = None

        # Agregar nueva pregunta
        new_row = pd.DataFrame({
            'fecha': [datetime.now().strftime('%Y-%m-%d %H:%M:%S')],
            'pregunta': [question]
        })
        df = pd.concat([df, new_row], ignore_index=True)

        # Convertir DataFrame a CSV
        csv_content = df.to_csv(index=False)
        content_encoded = base64.b64encode(csv_content.encode("utf-8")).decode("utf-8")

        # Preparar el commit
        data = {
            "message": f"Nueva pregunta registrada: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "content": content_encoded,
            "branch": "main"
        }
        
        if sha:
            data["sha"] = sha

        # Hacer el commit
        response = requests.put(url, headers=headers, data=json.dumps(data))
        response.raise_for_status()

        # Mostrar las últimas preguntas en el sidebar
        st.sidebar.markdown("### Últimas preguntas registradas:")
        st.sidebar.dataframe(df.tail(), use_container_width=True)

        st.toast("✅ Pregunta guardada en GitHub", icon='✍️')
        return True

    except Exception as e:
        st.error(f"Error al guardar en GitHub: {str(e)}")
        return False

# Configuración de la página
st.set_page_config(
    page_title="Proyecto Taras-La Lima Chat",
    page_icon="🚧",
    layout="wide",
    initial_sidebar_state="expanded"
)

# El resto del código anterior se mantiene igual hasta llegar a la parte del manejo de preguntas...

# Cuando llegas a la parte del else donde se manejan las preguntas sin respuesta, reemplazas con:

            else:
                # Guardar la pregunta sin respuesta
                save_question_to_github(prompt)
                response = f"""Esa pregunta aun no la puedo responder, estoy en proceso de entrenamiento, voy a guardar tu pregunta en mis registros para que la tomen en cuenta.

Guardando la pregunta: "{prompt}"

Puedo ayudarte con información sobre:
- Promedios por imagen
- Promedios diarios de detecciones
- Máximos de detecciones por tipo
- Distribución de detecciones
- Patrones horarios
- Total de detecciones

¿Te gustaría saber algo sobre estos temas?"""

# El resto del código se mantiene igual
