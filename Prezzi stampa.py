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

    # Otteniamo il volume del modello
    volume = model.get_mass_properties()[0]  # Ottiene il volume del modello
    st.write(f"Volume del modello STL (in cm³): {volume:.2f}")

    return volume


if uploaded_file:
    materiale = st.selectbox("Materiale", ["PLA", "PETG", "TPU"])
    dettaglio = st.selectbox("Livello di dettaglio", ["Basso", "Medio", "Alto"])

    # Variabili per il calcolo
    grammi = 0
    tempo_totale_minuti = 0
    totale = 0  # Impostiamo una variabile per totale, inizializzata a 0
    volume_stl = 0

    # Densità materiale - facoltativo da cambiare
    densita_materiale = 1.25  # g/cm³ per PLA, ma può essere modificato

    if uploaded_file.name.endswith(".gcode"):
        content = uploaded_file.read().decode("utf-8")

        # Estrazione del peso del filamento
        match_filament = re.search(r";\s*filament used \[g\]\s*=\s*([\d\.]+)", content)
        if match_filament:
            grammi = float(match_filament.group(1))
        else:
            st.warning("Peso del filamento non trovato nel G-code!")

        # Estrazione del tempo di stampa
        match_time = re.search(r";\s*estimated printing time \(normal mode\)\s*=\s*(\d+)h\s*(\d+)m\s*(\d+)s", content)
        if match_time:
            ore = int(match_time.group(1))
            minuti = int(match_time.group(2))
            secondi = int(match_time.group(3))
            tempo_totale_minuti = ore * 60 + minuti + (secondi / 60)
        else:
            st.warning("Tempo di stampa non trovato nel G-code!")

    elif uploaded_file.name.endswith(".3mf"):
        grammi, tempo_totale_minuti = estrai_dati_da_3mf(uploaded_file)

    elif uploaded_file.name.endswith(".stl"):
        volume_stl = calcola_volume_stl(uploaded_file)
        # Verifica del volume del modello STL
        st.write(f"Volume del modello STL: {volume_stl:.2f} cm³")

        # Calcolo del peso in base al volume e densità
        grammi = volume_stl * densita_materiale  # Peso in grammi basato sul volume e densità

        # Se il peso calcolato è troppo grande, diminuiamo il volume (fattore di correzione)
        if grammi > 1000:  # Limite di sicurezza (per esempio 1000g)
            st.warning(
                f"Attenzione: il peso calcolato ({grammi:.2f}g) sembra essere troppo elevato. Potrebbe esserci un problema con la scala del modello.")
            grammi /= 1000  # Fattore di correzione per ridurre il peso (esempio: per millimetri al posto di centimetri)

        tempo_totale_minuti = 0  # Tempo di stampa non disponibile per STL, ma può essere stimato tramite slicing

    # Parametri di costo
    costi = {
        "PLA": 0.06,
        "PETG": 0.08,
        "TPU": 0.10,
    }
    costo_ora_stampa = 1.50
    costo_elettricita_ora = 0.10
    avviamento = 2.00
    margine = 50  # Margine di guadagno aggiornato al 50%
    dettagli = {"Basso": 0.0, "Medio": 0.15, "Alto": 0.30}

    # Calcoli
    costo_materiale = grammi * costi[materiale]
    costo_stampa = (tempo_totale_minuti / 60) * costo_ora_stampa
    costo_elettricita = (tempo_totale_minuti / 60) * costo_elettricita_ora
    parziale = costo_materiale + costo_stampa + costo_elettricita + avviamento
    supplemento = parziale * dettagli[dettaglio]
    totale = parziale + supplemento  # Assicuriamoci che totale venga calcolato sempre
    margine_val = totale * (margine / 100)
    prezzo_finale = totale + margine_val

    # Risultati
    st.markdown("### Risultati del calcolo:")
    st.write(f"Peso del filamento: {grammi:.2f} g")
    st.write(f"Tempo di stampa: {tempo_totale_minuti:.2f} minuti")
    st.write(f"Costo materiale: €{costo_materiale:.2f}")
    st.write(f"Costo stampa: €{costo_stampa:.2f}")
    st.write(f"Costo elettricità: €{costo_elettricita:.2f}")
    st.write(f"Costo avviamento: €{avviamento:.2f}")
    st.write(f"Supplemento dettaglio ({dettaglio}): €{supplemento:.2f}")
    st.write(f"Margine di guadagno ({margine}%): €{margine_val:.2f}")
    st.subheader(f"Prezzo Finale: €{prezzo_finale:.2f}")
