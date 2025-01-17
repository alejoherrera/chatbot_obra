import base64
import json
import requests
from datetime import datetime
import pandas as pd

def save_question_to_github(question):
    try:
        # Configuración de GitHub
        github_token = st.secrets["github"]["token"]
        repo_name = "tu_usuario/tu_repositorio"
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
        except:
            # Si el archivo no existe, crear un DataFrame nuevo
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
            "message": f"Add new question: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "content": content_encoded,
            "branch": "main"
        }
        
        if sha:
            data["sha"] = sha

        # Hacer el commit
        response = requests.put(url, headers=headers, data=json.dumps(data))
        response.raise_for_status()

        st.toast("Pregunta guardada en GitHub", icon='✍️')
        return True

    except Exception as e:
        st.error(f"Error al guardar en GitHub: {str(e)}")
        return False
