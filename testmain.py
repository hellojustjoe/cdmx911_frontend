#from dotenv import load_dotenv
#load_dotenv()
import streamlit as st
import pandas as pd
import geopandas as gpd
import pydeck as pdk
import json
import os
import requests

from functions import show_dynamic_plot, show_historic_tvsf, show_predicted_incidents, get_feature_info, show_aggregated_predictions

#print("SERVICE_URL:", os.getenv("SERVICE_URL"))

#API_HOST_LOCAL = os.getenv('SERVICE_URL', 'http://localhost:8000')
FASTAPI_URL = 'https://cdmx911-api-osg4ztthva-uc.a.run.app'


st.set_page_config(layout="wide")

def fetch_geojson(url):
    response = requests.get(url)
    if response.status_code == 200:
        try:
            geojson_dict = json.loads(response.text)
            return gpd.GeoDataFrame.from_features(geojson_dict["features"])
        except json.JSONDecodeError as e:
            st.error(f"Error decoding JSON: {e}")
            st.text(response.text[:500])  # Show first 500 characters of the response for debugging
            return None
    else:
        st.error(f"Failed to fetch data: HTTP {response.status_code}")
        st.text(response.text[:500])  # Show first 500 characters of the response for debugging
        return None

mapa = fetch_geojson(f"{FASTAPI_URL}/main-map")


# Get main map
# response = requests.get(API_HOST_LOCAL + '/main-map')
#response = requests.get(FASTAPI_URL + '/main-map')

#mapa = gpd.read_file(response.text, driver='GeoJSON')
#geojson_dict = json.loads(response.text)
#mapa = gpd.GeoDataFrame.from_features(geojson_dict["features"])


# Página principal
def main():
    github_url = "https://github.com/Hellojustjoe/"
    badge_url = "https://img.shields.io/badge/-hellojustjoe-black?style=flat-square&logo=github"

    st.markdown(f"""
        <div style="display: flex; justify-content: center; align-items: center;">
            <h1 style="margin-right: 10px;">Consola de datos 911 CDMX</h1>
            <a href="{github_url}">
                <img src="{badge_url}" alt="GitHub Badge" style="height: 40px; border-radius: 10px;">
            </a>
        </div>
        """, unsafe_allow_html=True)
    st.markdown("<h3 style='text-align: center;'>Obten informacion detallada acerca de los incidentes reportados al 911</h3>", unsafe_allow_html=True)

    #st.markdown('### Obten informacion detallada acerca de los incidentes reportados al 911')

    # name-alcaldia api call
    response = requests.get(FASTAPI_URL + '/name-alcaldia')
    # Check if the response status code indicates success
    if response.status_code == 200:
        try:
            names_alcaldias = response.json()['alcaldias']
        except json.JSONDecodeError:
            st.error("Failed to decode JSON from response. The service might be down or returning an unexpected format.")
            # Log the first 500 characters of the response for debugging (consider logging more or less depending on your needs)
            st.text(response.text[:500])
            # Set names_alcaldias to None or an empty list to handle this error gracefully in your app
            names_alcaldias = None
    else:
        st.error(f"Error fetching data: HTTP {response.status_code}")
        # Optionally log the response body for debugging
        st.text(response.text[:500])
        # Set names_alcaldias to None or an empty list to handle this error gracefully in your app
        names_alcaldias = None


    names_alcaldias = response.json()['alcaldias']

    # Select box alcaldia
    alcaldia_seleccionada = st.selectbox("Selecciona una alcaldía:", names_alcaldias)
    col1, col2 = st.columns(2)
    # Get alcaldia lat & lon
    params = {'name_alcaldia': alcaldia_seleccionada}
    response = requests.get(FASTAPI_URL + '/latlon', params=params).json()
    latitud, longitud = response['Latitud'], response['Longitud']



    # Visualizar el mapa
    view_state = pdk.ViewState(
        latitude=latitud,
        longitude=longitud,
        zoom=12
    )

    #response = requests.get(API_HOST_LOCAL + '/model-data', params=params).json()


    with col1:
        st.markdown('## Mapa de CMDX')

        layer_alcaldias = pdk.Layer(
            "GeoJsonLayer",
            data=mapa,
            get_fill_color=[255, 0, 0, 100],
            get_line_color=[0, 255, 0, 200],
            get_line_width=60, #thicc so they can be seen
            pickable=True,
            auto_highlight=True,
            opacity=0.8,
            tooltip={
                    "text": "{NOMGEO}"
            }
        )

        r = pdk.Deck(layers=[layer_alcaldias], initial_view_state=view_state, map_style=None)

        # Mostrar el mapa en Streamlit
        st.pydeck_chart(r,use_container_width=True)

        if st.button("Desplegar informacion Alcaldía mensual"):
            # Navegar a la página de información detallada
            st.session_state.ubicacion_seleccionada = alcaldia_seleccionada
            st.experimental_rerun()

    line_chart, pie_chart = show_predicted_incidents(alcaldia_seleccionada)
    #pie_chart = show_aggregated_predictions()
    with col2:
        st.markdown('## Predicciones de Incidentes')
        st.plotly_chart(line_chart,use_container_width=True)

    col3, col4 = st.columns(2)
    total_prediction, per_pop = show_aggregated_predictions()
    with col3:
        st.markdown('## Total incidentes por alcaldía')
        st.plotly_chart(total_prediction,use_container_width=True)

    with col4:
        # Historic True vs False case calls
        st.markdown('## Total incidentes por poblacion')
        st.plotly_chart(per_pop,use_container_width=True)


    # Página de información detallada
def mostrar_informacion_detallada():
    st.title(f"Información de la Alcaldía {st.session_state.ubicacion_seleccionada}")

    st.markdown('##### *Datos actualizados hasta Julio de 2023')

    # Show plot
    show_dynamic_plot(st.session_state.ubicacion_seleccionada)


# Manejo de la navegación entre páginas
if 'ubicacion_seleccionada' not in st.session_state:
    st.session_state.ubicacion_seleccionada = None

if st.session_state.ubicacion_seleccionada is not None:
    mostrar_informacion_detallada()
    if st.button("Regresar al mapa"):
        # Regresar a la página principal
        st.session_state.ubicacion_seleccionada = None
        st.experimental_rerun()
else:
    main()
