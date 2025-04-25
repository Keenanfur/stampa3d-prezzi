import re
import streamlit as st
import pandas as pd
import io
import zipfile

st.title("Calcolo Prezzo da File G-code o 3MF")

uploaded_file = st.file_uploader("Carica il tuo file G-code o 3MF", type=["gcode", "3mf"])


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


if uploaded_file:
    materiale = st.selectbox("Materiale", ["PLA", "PETG", "TPU"])
    dettaglio = st.selectbox("Livello di dettaglio", ["Basso", "Medio", "Alto"])

    if uploaded_file.name.endswith(".gcode"):
        content = uploaded_file.read().decode("utf-8")

        # Aggiungi il debug: visualizza il contenuto del G-code
        st.text_area("Contenuto G-code", content, height=300)  # Mostra tutto il G-code per il debug

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

    # Parametri di costo
    costi = {
        "PLA": 0.06,
        "PETG": 0.08,
        "TPU": 0.10,
    }
    costo_ora_stampa = 1.50
    costo_elettricita_ora = 0.10
    avviamento = 2.00
    margine = 30
    dettagli = {"Basso": 0.0, "Medio": 0.15, "Alto": 0.30}

    # Calcoli
    costo_materiale = grammi * costi[materiale]
    costo_stampa = (tempo_totale_minuti / 60) * costo_ora_stampa
    costo_elettricita = (tempo_totale_minuti / 60) * costo_elettricita_ora
    parziale = costo_materiale + costo_stampa + costo_elettricita + avviamento
    supplemento = parziale * dettagli[dettaglio]
    totale = parziale + supplemento
    margine_val = totale * (margine / 100)
    prezzo_finale = totale + margine_val

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
