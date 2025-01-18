import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
import base64
import json
import requests

# Configuración de la página
st.set_page_config(
    page_title="Proyecto Taras-La Lima Chat",
    page_icon="🚧",
    layout="wide",
    initial_sidebar_state="expanded"
)

def update_question_file_in_github(df):
    try:
        # Configuración de GitHub
        github_token = st.secrets["github"]["token"]
        repo_name = "alejoherrera/chatbot_obra"
        file_path = "data/preguntas.csv"

        headers = {
            "Authorization": f"token {github_token}",
            "Accept": "application/vnd.github.v3+json"
        }

        # Obtener contenido actual del archivo desde GitHub
        url = f"https://api.github.com/repos/{repo_name}/contents/{file_path}"
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        file_data = response.json()

        # Decodificar el contenido existente del archivo
        existing_content = base64.b64decode(file_data["content"]).decode("utf-8")
        existing_df = pd.read_csv(pd.compat.StringIO(existing_content))

        # Combinar el DataFrame existente con el nuevo DataFrame
        updated_df = pd.concat([existing_df, df], ignore_index=True)

        # Convertir el DataFrame actualizado a CSV y codificarlo en Base64
        updated_csv = updated_df.to_csv(index=False)
        updated_content_encoded = base64.b64encode(updated_csv.encode("utf-8")).decode("utf-8")

        # Preparar datos para actualizar el archivo en GitHub
        update_data = {
            "message": f"Actualización: Nueva pregunta agregada el {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "content": updated_content_encoded,
            "sha": file_data["sha"]
        }

        # Actualizar el archivo en GitHub
        update_response = requests.put(url, headers=headers, data=json.dumps(update_data))
        update_response.raise_for_status()

        st.success("✅ Pregunta agregada exitosamente en GitHub")
        return True
    except Exception as e:
        st.error(f"Error al guardar la pregunta en GitHub: {str(e)}")
        return False

def extract_datetime(filename):
    try:
        # Formato esperado: YYYYMMDD-HHMMSS.jpg
        date_part = filename.split('-')[0]
        time_part = filename.split('-')[1].split('.')[0]
        
        year = date_part[:4]
        month = date_part[4:6]
        day = date_part[6:8]
        
        hour = time_part[:2]
        minute = time_part[2:4]
        second = time_part[4:6]
        
        return datetime(int(year), int(month), int(day), 
                       int(hour), int(minute), int(second))
    except Exception as e:
        st.error(f"Error al procesar fecha del archivo {filename}: {str(e)}")
        return None

# Función para cargar y procesar datos
@st.cache_data
def load_data():
    try:
        # Intenta diferentes rutas posibles para el archivo
        possible_paths = [
            'matriz_prototipo.csv',
            'data/matriz_prototipo.csv',
            './matriz_prototipo.csv',
            './data/matriz_prototipo.csv'
        ]
        
        df = None
        for path in possible_paths:
            try:
                df = pd.read_csv(path, sep=';')
                st.success(f'Archivo cargado correctamente desde: {path}')
                break
            except FileNotFoundError:
                continue
        
        if df is None:
            raise FileNotFoundError(
                "No se pudo encontrar el archivo matriz_prototipo.csv. "
                "Por favor, contacta al administrador para obtener el archivo."
            )
        
        # Procesar fechas y horas
        df['datetime'] = df['nombre_imagen'].apply(extract_datetime)
        df['date'] = df['datetime'].dt.date
        df['hour'] = df['datetime'].dt.hour
        
        # Mapear etiquetas a nombres descriptivos
        df['tipo_objeto'] = df['etiqueta'].map({
            2: 'Personas',
            3: 'Tractores',
            6: 'Aplanadoras'
        })
        
        return df
    
    except Exception as e:
        st.error(f"Error al cargar o procesar los datos: {str(e)}")
        return None

def main():
    # Título y descripción
    st.title("💬 Chat Proyecto Taras-La Lima")
    st.markdown("""
    Este chat te permite analizar los datos de detección de objetos del proyecto Intersección vial Taras-La Lima.
    Puedes hacer preguntas sobre:
    - Detecciones de personas, tractores y aplanadoras
    - Tendencias diarias y horarias
    - Estadísticas específicas
    """)

    try:
        # Intentar cargar datos
        df = load_data()
        
        if df is None:
            st.warning("No se pudo cargar el archivo CSV. Por favor, contacta al administrador.")
            st.stop()
        
        # Calcular algunas estadísticas útiles
        total_detections = len(df)
        unique_days = df['date'].nunique()
        detection_by_type = df['tipo_objeto'].value_counts()
        
        # Mostrar estadísticas generales en columnas
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Detecciones", f"{total_detections:,}")
        with col2:
            st.metric("Días Monitoreados", unique_days)
        with col3:
            st.metric("Tipos de Objetos", len(detection_by_type))
        
        # Área de chat
        if "messages" not in st.session_state:
            st.session_state.messages = []

        # Mostrar mensajes anteriores
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])
        # Reaccionar a las preguntas del usuario
        if prompt := st.chat_input("Haz una pregunta sobre el proyecto"):
            # Agregar mensaje del usuario
            st.session_state.messages.append({"role": "user", "content": prompt})
            with st.chat_message("user"):
                st.markdown(prompt)

            # Procesar la pregunta y generar respuesta
            response = ""
            fig = None
            
            # Palabras clave para diferentes tipos de análisis
            prompt_lower = prompt.lower()
            
            if "promedio por imagen" in prompt_lower:
                # Agrupar por nombre de imagen primero
                image_stats = df.groupby(['nombre_imagen', 'tipo_objeto']).size().reset_index(name='count')
                avg_by_image = image_stats.groupby('tipo_objeto')['count'].mean().round(2)
                
                response = "Promedio de detecciones por imagen:\n\n"
                for obj_type, avg in avg_by_image.items():
                    response += f"- {obj_type}: {avg:.2f}\n"
                
                # Crear gráfico de barras
                fig = px.bar(avg_by_image, 
                            title='Promedio de Detecciones por Imagen',
                            labels={'index': 'Tipo de Objeto', 'value': 'Promedio por Imagen'},
                            color=avg_by_image.index)
            
            # El resto del código de análisis y generación de respuesta se mantiene igual
            ...

            # Guardar la pregunta en GitHub
            new_row = pd.DataFrame({
                'fecha': [datetime.now().strftime('%Y-%m-%d %H:%M:%S')],
                'pregunta': [prompt]
            })
            if update_question_file_in_github(new_row):
                st.session_state.messages.append({"role": "assistant", "content": response})
            else:
                st.session_state.messages.append({"role": "assistant", "content": "Lo siento, hubo un problema al guardar tu pregunta. Por favor, inténtalo de nuevo más tarde."})

    except Exception as e:
        st.error(f"Error al cargar o procesar los datos: {str(e)}")
        st.write("Por favor, contacta al administrador para obtener el archivo CSV.")
        if st.button('Reintentar'):
            st.experimental_rerun()

if __name__ == "__main__":
    main()
