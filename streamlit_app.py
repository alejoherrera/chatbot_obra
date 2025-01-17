import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
import plotly.graph_objects as go
import numpy as np
import os

# Configuración de la página
st.set_page_config(
    page_title="Proyecto Taras-La Lima Chat",
    page_icon="🚧",
    layout="wide"
)

# Función para guardar preguntas sin respuesta
def save_unanswered_question(question):
    try:
        filename = 'preguntas_sin_contestar.csv'
        current_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        # Crear el CSV si no existe
        if not os.path.exists(filename):
            with open(filename, 'w', encoding='utf-8') as f:
                f.write('fecha,pregunta\n')
        
        # Agregar la nueva pregunta
        with open(filename, 'a', encoding='utf-8') as f:
            f.write(f'"{current_date}","{question}"\n')
            
        return True
    except Exception as e:
        st.error(f"Error al guardar la pregunta: {str(e)}")
        return False

# [El resto del código anterior se mantiene igual hasta la parte del manejo de preguntas]

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
        
        # Detectar si la pregunta coincide con alguno de los patrones conocidos
        if "promedio por imagen" in prompt_lower:
            # [código existente para promedio por imagen]
            pass
        elif "promedio" in prompt_lower or "media" in prompt_lower:
            # [código existente para promedios]
            pass
        elif "máximo" in prompt_lower or "mayor" in prompt_lower:
            # [código existente para máximos]
            pass
        elif "distribución" in prompt_lower or "porcentaje" in prompt_lower:
            # [código existente para distribución]
            pass
        elif "hora" in prompt_lower or "horario" in prompt_lower:
            # [código existente para horarios]
            pass
        elif "total" in prompt_lower or "detecciones" in prompt_lower:
            # [código existente para totales]
            pass
        else:
            # Guardar la pregunta sin respuesta
            save_unanswered_question(prompt)
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

# [El resto del código se mantiene igual]
