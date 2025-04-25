import re
import streamlit as st
import pandas as pd
import io
import zipfile
from stl import mesh
import tempfile

st.title("Calcolo Prezzo da File G-code, 3MF o STL")

uploaded_file = st.file_uploader("Carica il tuo file G-code, 3MF o STL", type=["gcode", "3mf", "stl"])


def estrai_dati_da_3mf(file):
    with zipfile.ZipFile(file, 'r') as archive:
        for name in archive.namelist():
            if "metadata" in name.lower() and name.endswith(".xml"):
                content = archive.read(name).decode("utf-8")
                time_match = re.search(r'<slicestats:printingTime>([\d\.]+)</slicestats:printingTime>', content)
                weight_match = re.search(r'<slicestats:filamentWeight>([\d\.]+)</slicestats:filamentWeight>', content)

                minuti = float(time_match.group(1)) if time_match else 0
                grammi = float(weight_match.group(1)) if weight_match else 0
                return grammi, minuti
    return 0, 0


def calcola_volume_stl(file):
    # Creiamo un file temporaneo per salvare il file STL
    with tempfile.NamedTemporaryFile(delete=False, suffix='.stl') as temp_file:
        temp_file.write(file.read())  # Salviamo il contenuto del file STL
        temp_file_path = temp_file.name

    # Carichiamo il file STL dal percorso temporaneo
    model = mesh.Mesh.from_file(temp_file_path)
    volume = model.get_mass_properties()[0]  # Ottiene il volume del modello
    return volume


if uploaded_file:
    materiale = st.selectbox("Materiale", ["PLA", "PETG", "TPU"])
    dettaglio = st.selectbox("Livello di dettaglio", ["Basso", "Medio", "Alto"])

    if uploaded_file.name.endswith(".gcode"):
        content = uploaded_file.read().decode("utf-8")

        # Estrazione del peso del filamento
        match_filament = re.search(r";\s*filament used \[g\]\s*=\s*([\d\.]+)", content)
        if match_filament:
            grammi = float(match_filament.group(1))
        else:
            grammi = 0
            st.warning("Peso del filamento non trovato nel G-code!")

        # Estrazione del tempo di stampa
        match_time = re.search(r";\s*estimated printing time \(normal mode\)\s*=\s*(\d+)h\s*(\d+)m\s*(\d+)s", content)
        if match_time:
            ore = int(match_time.group(1))
            minuti = int(match_time.group(2))
            secondi = int(match_time.group(3))
            tempo_totale_minuti = ore * 60 + minuti + (secondi / 60)
        else:
            tempo_totale_minuti = 0
            st.warning("Tempo di stampa non trovato nel G-code!")

    elif uploaded_file.name.endswith(".3mf"):
        grammi, tempo_totale_minuti = estrai_dati_da_3mf(uploaded_file)

    elif uploaded_file.name.endswith(".stl"):
        volume = calcola_volume_stl(uploaded_file)
        # Utilizziamo una densità approssimativa per il materiale PLA (1.25 g/cm³)
        densita_materiale = 1.25  # g/cm³ per PLA
        grammi = volume * dens *
