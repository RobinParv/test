import streamlit as st

# Seab lehe laiaks, et sisu jaotuks reaalsetesse ekraani äärtesse
st.set_page_config(layout="wide")

# CSS: See lukustab AINULT sisukorra kasti ekraani külge, jättes Streamliti struktuuri terveks
st.markdown("""
    <style>
        /* Loome unikaalse klassi, mis kleebib elemendi 100% paigale */
        .fikseeritud-sisukord {
            position: fixed;
            right: 0rem;          /* Paremast servast */
            top: 4rem;            /* Ülevalt servast */
            width: 150px;         /* Laius */
            background-color: #f9f9f9; /* Taustavärv */
            padding: 1rem;
            border-radius: 8px;
            border: 1px solid #e6e6e6;
            z-index: 999;
            overflow-y: auto; /* Kerimine */
            max-height: 80vh; /* 80% ekraani kõrgusest */
        }
        
        /* Muudab lingid sisukorras kenamaks */
        .fikseeritud-sisukord a {
            text-decoration: none;
            color: #0066cc; /* sinine */
        }
        .fikseeritud-sisukord a:hover {
            text-decoration: underline;
        }
    </style>
""", unsafe_allow_html=True)

# 1. Lähteandmed
with st.sidebar:
    st.header("Lähteandmed")
    arv = st.number_input("Sisesta arv:")
    vanus = st.number_input("Vanus:", min_value=0, max_value=120, value=25)
    st.button("Arvuta")

# 2. PÕHISISU JA SISUKORD
# col_sisukord toimib nüüd lihtsalt tühja kohahoidjana, et tekst ei vajuks sisukorrale alla
col_tekst, col_sisukord = st.columns([5, 1.5], gap="large")

with col_tekst:
    # See tekstiosa kasutab nüüd veebilehe peamist kerimisriba (kõige mugavam kerida)
    st.title("Peamine sisu")
    
    
    st.header(f"Kandevõime", anchor=f"Kandevoime")
    st.latex(rf"\frac{{\frac{{\frac{{{arv}}}{{{vanus}}}}}{{1}}}}{{1}}")

    for i in range(1, 11):
        st.header(f"Peatükk {i}", anchor=f"peatukk-{i}")
        st.write("Siia tuleb sinu rakenduse peamine tekst, graafikud või tabelid. " * 60)

with col_sisukord:
    # Süstime puhast HTML-i, mis kasutab meie loodud fikseeritud CSS klassi
    st.markdown("""
        <div class="fikseeritud-sisukord">
            <hr style="margin: 0.1rem 0 0.2rem 0;">
            <ul style="list-style-type: none; padding-left: 0; margin: 0; line-height: 1,6;">
                <li><a href="#pKandevõime">Kandevõime</a></li>
                <li><a href="#peatukk-2">Peatükk 2</a></li>
                <li><a href="#peatukk-3">Peatükk 3</a></li>
                <li><a href="#peatukk-4">Peatükk 4</a></li>
                <li><a href="#peatukk-5">Peatükk 5</a></li>
                <li><a href="#peatukk-6">Peatükk 6</a></li>
                <li><a href="#peatukk-7">Peatükk 7</a></li>
                <li><a href="#peatukk-8">Peatükk 8</a></li>
                <li><a href="#peatukk-9">Peatükk 9</a></li>
                <li><a href="#peatukk-10">Peatükk 10</a></li>
            </ul>
        </div>
    """, unsafe_allow_html=True)
