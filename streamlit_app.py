import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
import numpy as np
import os
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

# Función para guardar en GitHub




import requests
import base64
import pandas as pd
import io
from datetime import datetime
import json
import streamlit as st

def save_question_to_github(question):
    try:
        # Configuración
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
        existing_df = pd.read_csv(io.StringIO(existing_content))

        # Agregar la nueva pregunta
        new_row = {
            "fecha": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            "pregunta": question
        }
        updated_df = pd.concat([existing_df, pd.DataFrame([new_row])], ignore_index=True)

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

        st.toast("✅ Pregunta agregada exitosamente en GitHub", icon='✍️')
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
def load_data(uploaded_file=None):
    try:
        if uploaded_file is not None:
            df = pd.read_csv(uploaded_file, sep=';')
            st.success('Archivo cargado correctamente desde la carga manual')
        else:
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
                    "Por favor, sube el archivo manualmente usando el panel lateral."
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
        st.error(f"Error al procesar los datos: {str(e)}")
        return None
def main():
    # Agregar opción de carga de archivo en el sidebar
    st.sidebar.markdown("### Cargar Datos")
    uploaded_file = st.sidebar.file_uploader("Cargar archivo CSV", type=['csv'])
    try:
        # Intentar cargar datos
        if uploaded_file is not None:
            df = load_data(uploaded_file)
        else:
            df = load_data()
            
        if df is None:
            st.warning("Por favor, sube el archivo CSV usando el panel lateral para comenzar el análisis.")
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
            
            elif "promedio" in prompt_lower or "media" in prompt_lower:
                if "día" in prompt_lower or "diario" in prompt_lower:
                    daily_avg = df.groupby(['date', 'tipo_objeto']).size().reset_index(name='count')
                    daily_avg = daily_avg.groupby(['tipo_objeto'])['count'].mean().round(2)
                    response = f"Promedios diarios de detecciones:\n\n"
                    for obj_type, avg in daily_avg.items():
                        response += f"- {obj_type}: {avg:.2f}\n"
                    
                    # Crear gráfico
                    fig = px.bar(daily_avg, 
                               title='Promedio Diario de Detecciones por Tipo',
                               labels={'index': 'Tipo de Objeto', 'value': 'Promedio de Detecciones'})

            elif "máximo" in prompt_lower or "mayor" in prompt_lower:
                daily_counts = df.groupby(['date', 'tipo_objeto']).size().reset_index(name='count')
                max_days = daily_counts.loc[daily_counts.groupby('tipo_objeto')['count'].idxmax()]
                response = "Días con mayor número de detecciones:\n\n"
                for _, row in max_days.iterrows():
                    response += f"- {row['tipo_objeto']}: {row['count']} detecciones el {row['date']}\n"
                    
                fig = px.bar(max_days, x='tipo_objeto', y='count',
                            title='Máximo de Detecciones por Tipo',
                            labels={'tipo_objeto': 'Tipo de Objeto', 'count': 'Número de Detecciones'})

            elif "distribución" in prompt_lower or "porcentaje" in prompt_lower:
                total_by_type = df['tipo_objeto'].value_counts()
                percentages = (total_by_type / len(df) * 100).round(2)
                response = "Distribución de detecciones:\n\n"
                for obj_type, pct in percentages.items():
                    response += f"- {obj_type}: {pct:.2f}%\n"
                    
                fig = px.pie(values=percentages.values, 
                            names=percentages.index,
                            title='Distribución de Detecciones por Tipo')

            elif "hora" in prompt_lower or "horario" in prompt_lower:
                hourly_avg = df.groupby(['hour', 'tipo_objeto']).size().reset_index(name='count')
                pivot_hourly = hourly_avg.pivot(index='hour', columns='tipo_objeto', values='count').fillna(0)
                
                response = "Distribución horaria de detecciones:\n\n"
                for hour in range(24):
                    if hour in pivot_hourly.index:
                        response += f"\nHora {hour:02d}:00:\n"
                        for col in pivot_hourly.columns:
                            response += f"- {col}: {pivot_hourly.loc[hour, col]:.0f}\n"
                            
                fig = px.line(hourly_avg, x='hour', y='count', color='tipo_objeto',
                             title='Detecciones por Hora del Día',
                             labels={'hour': 'Hora', 'count': 'Número de Detecciones', 'tipo_objeto': 'Tipo'})

            elif "total" in prompt_lower or "detecciones" in prompt_lower:
                total_by_type = df['tipo_objeto'].value_counts()
                response = "Total de detecciones por tipo:\n\n"
                for obj_type, count in total_by_type.items():
                    response += f"- {obj_type}: {count:,}\n"
                
                fig = px.bar(x=total_by_type.index, y=total_by_type.values,
                            title='Total de Detecciones por Tipo',
                            labels={'x': 'Tipo de Objeto', 'y': 'Número de Detecciones'})

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

            # Mostrar respuesta
            with st.chat_message("assistant"):
                st.markdown(response)
                if fig is not None:
                    st.plotly_chart(fig, use_container_width=True)
            
            # Guardar respuesta
            st.session_state.messages.append({"role": "assistant", "content": response})

    except Exception as e:
        st.error(f"Error al cargar o procesar los datos: {str(e)}")
        st.write("Por favor, asegúrate de que el archivo CSV esté en el formato correcto y contenga los datos necesarios.")
        if st.button('Reintentar'):
            st.experimental_rerun()

if __name__ == "__main__":
    main()
