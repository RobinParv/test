import streamlit as st
import math
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib

# Leht laiaks
st.set_page_config(layout="wide")



# Sisukorra kasti tegemine ------------------------------------------------------------------------
st.markdown("""
    <style>
        [data-testid="stMain"] {
            position: relative;
        }

        /* VAIKIMISI STIIL (Suurele ekraanile/arvutile) */
        .fikseeritud-sisukord {
            position: fixed !important;
            right: 2rem;
            top: 5rem;
            width: 180px;
            background-color: #f9f9f9; 
            padding: 1rem;
            border-radius: 8px;
            border: 1px solid #e6e6e6;
            z-index: 999999;
            overflow-y: auto; 
            max-height: 75vh; 
            box-shadow: 0px 4px 10px rgba(0, 0, 0, 0.05);
        }
        
        .fikseeritud-sisukord a {
            text-decoration: none;
            color: #0066cc; 
            display: block;
            margin-bottom: 0.5rem;
            font-size: 0.9rem;
        }
        .fikseeritud-sisukord a:hover {
            text-decoration: underline;
            color: #004499;
        }

        /* MOBIILI JA KETSA AKNA STIIL (Ekraanid, mis on kitsamad kui 992px) */
        @media (max-width: 992px) {
            .fikseeritud-sisukord {
                position: static !important;  /* Kaotab ekraanile kleepumise */
                width: 100% !important;       /* Võtab terve ekraani laiuse */
                margin-bottom: 2rem;          /* Jtab teksti vahele ruumi */
                box-shadow: none;             /* Eemaldab varju, et sulanduks lehega */
                right: auto;
                top: auto;
            }
        }
    </style>
""", unsafe_allow_html=True)





# SIDEBAR - LÄHTEANDMED -----------------------------------------------------------------------------
with st.sidebar:

    st.html("""
<style>
/* 1. Vähendame elementide omavahelist vahekaugust (vaikeväärtus on tavaliselt 1rem) */
section[data-testid="stSidebar"] [data-testid="stVerticalBlock"] {
    gap: 0.5rem !important; /* Mida väiksem number, seda tihedamalt elemendid on */
}

/* 2. Vähendame tühja maad külgriba päises (kõige ülemise elemendi kohal) */
[data-testid="stSidebarHeader"] {
    padding-top: 1rem !important;
    padding-bottom: 0px !important;
    height: auto !important;
}

/* 3. Eemaldame peamise sisukonteineri liigse ülemise paddingu */
section[data-testid="stSidebar"] .stMainBlockContainer {
    padding-top: 0.5rem !important;
}
</style>
""")
    
    st.header("Lähteandmed")
    st.subheader("Betooni omadused")
    betooni_klassid = ["C12/15", "C16/20", "C20/25", "C25/30", "C30/37", "C35/45", "C40/50"]
    betooni_klass = st.selectbox("Vali betooni klass:", betooni_klassid, index=3) # Vaikimisi C25/30

    

    #Betooni klassist tulenevad omadused andmebaas
    survetugevused = {"C12/15": 12,"C16/20": 16,"C20/25": 20,"C25/30": 25,"C30/37": 30,"C35/45": 35,"C40/50": 40}
    elastsusmoodulid = {"C12/15": 27, "C16/20": 29, "C20/25": 30, "C25/30": 31, "C30/37": 33, "C35/45": 34, "C40/50": 35}
    tõmbetugevused = {"C12/15": 1.6, "C16/20": 1.9, "C20/25": 2.2, "C25/30": 2.6, "C30/37": 2.9, "C35/45": 3.2, "C40/50": 3.5}
    diameetrid = [6, 8, 10, 12, 14, 16, 20, 22, 25, 28, 32]

    #Betooni klassist tulenevad omadused andmebaas
    f_ck = survetugevused[betooni_klass]
    E_cm = elastsusmoodulid[betooni_klass]
    f_ctm = tõmbetugevused[betooni_klass]
    f_yk = 500 # Terase survetugevus hiljem
    
    

    st.markdown(f"##### $E_{{cm}}$ = {E_cm} GPa")
    st.markdown(f"##### $f_{{ctm}}$ = {f_ctm} MPa")
    
    
    st.subheader("Ristlõike mõõtmed")
    
    b = st.number_input("Sisesta ristlõike laius b (mm):", min_value=10, max_value=2000, value=300, step=10)
    h = st.number_input("Sisesta ristlõike kõrgus h (mm):", min_value=10, max_value=2000, value=500, step=10)

    st.subheader("Armatuuri omadused")

    A_s1 = st.number_input("Sisesta As1 (mm²):", min_value=0, max_value=10000, value=500, step=10)
    A_s2 = st.number_input("Sisesta As2 (mm²):", min_value=0, max_value=10000, value=500, step=10)

    d_s1 = st.number_input("Sisesta Ds1 (mm):", min_value=0, max_value=h, value=h-30, step=10)
    d_s2 = st.number_input("Sisesta Ds2 (mm):", min_value=0, max_value=h, value=30, step=10)

    st.subheader("Betooni omadused")


    t = st.number_input("Vaadeldav hetk päevades:", min_value=0, max_value=10000000, value=365, step=10)
    t_0 = st.number_input("Betooni vanus koormamise hetkel päevades:", min_value=0, max_value=10000000, value=28, step=10)

    ajaparandus = st.toggle("Kasuta ajaparandus tegurit")

    tsemendi_klass = "N"
    RH = 80

    if ajaparandus:
        RH = st.number_input("Õhuniiskus", min_value=0, max_value=100, value=80, step=5)
        tsemendi_klass = st.selectbox("Tsemendi klass:",options=["S", "N", "R"])

   
    
#Defineeritud suurused------------------------------------------------------------------------------ 
betooni_osavarutegur = 1.5
armatuuri_osavarutegur = 1.15
η = 1.0 #betooni pingeploki tugevuse tegur
λ = 0.8 #betooni pingeploki ekvivalentse kõrguse tegur
E_s = 200000 #armatuuri elastsusmoodul
ε_cu = 0.0035 #betooni piirdedeformatsioon
ε_yd = (f_yk / armatuuri_osavarutegur) / E_s #armatuuri piirdedeformatsioon
ξ_c_lim = round(ε_cu / (ε_cu + ε_yd), 2)
ξ_c2_lim = round((ε_cu / (ε_cu - ε_yd)) * (d_s2 / d_s1), 2)
σ_sc_u = E_s * ε_cu
f_cm = f_ck + 8
h_0 = round(2*((b * h) / (2 * (b + h))), 0)
tsemendi_klassid = {"S": -1, "N": 0, "R": 1}
α_tsement = tsemendi_klassid[tsemendi_klass] 







#--------------------------------------------------------------------------------------------------

# 2. PÕHISISU JA SISUKORD
# col_sisukord toimib nüüd lihtsalt tühja kohahoidjana, et tekst ei vajuks sisukorrale alla
col_tekst, col_sisukord = st.columns([5, 1.5], gap="large")

with col_tekst:
    # See tekstiosa kasutab nüüd veebilehe peamist kerimisriba (kõige mugavam kerida)
    st.title("Raudbetooni arvutused")



#Kandevõime arvutamine ------------------------------------------------------------------------------
    st.header(f"Kandevõime", anchor=f"Kandevõime")
    st.write("Leiame arvutuslikud tugevused")
    st.latex(fr"\footnotesize f_{{cd}} = \frac{{f_{{ck}}}}{{\gamma_{{c}}}} = \frac{{{f_ck}}}{{{betooni_osavarutegur}}} = {f_ck/betooni_osavarutegur:.2f} \text{{ MPa}}")
    st.latex(fr"\footnotesize f_{{yd}} = \frac{{f_{{yk}}}}{{\gamma_{{s}}}} = \frac{{{f_yk}}}{{{armatuuri_osavarutegur}}} = {f_yk/armatuuri_osavarutegur:.0f} \text{{ MPa}}")
    f_cd = round(f_ck / betooni_osavarutegur, 2)
    f_yd = round(f_yk / armatuuri_osavarutegur, 0)

    st.write("kus")
    st.write(f"<small>$\\gamma_{{c}} = {betooni_osavarutegur}$ — betooni osavarutegur</small>", unsafe_allow_html=True)
    st.write(f"<small>$\\gamma_{{s}} = {armatuuri_osavarutegur}$ — armatuurterase osavarutegur</small>", unsafe_allow_html=True) 

    st.html("<br>")

    st.write("Survekõrguse leidmine")  
    if A_s2 > 0:
        st.latex(fr"\footnotesize x = \frac{{A_{{s1}} \cdot f_{{yd}} - A_{{s2}} \cdot f_{{yd}}}}{{λ \cdot b \cdot η \cdot f_{{cd}}}} = \frac{{{A_s1} \cdot {f_yd} - {A_s2} \cdot {f_yd}}}{{ {λ} \cdot {η} \cdot {b} \cdot {f_cd}}} = {(A_s1 * f_yd - A_s2 * f_yd) / (λ * η * b):.2f} \text{{ mm}}")
        
    else:
        st.latex(fr"\footnotesize x = \frac{{A_{{s1}} \cdot f_{{yd}} - A_{{s2}} \cdot f_{{yd}}}}{{λ \cdot b \cdot η \cdot f_{{cd}}}} = \frac{{{A_s1} \cdot {f_yd}}}{{ {λ} \cdot {η} \cdot {b} \cdot {f_cd}}} = {(A_s1 * f_yd - A_s2 * f_yd) / (λ * η * b):.2f} \text{{ mm}}")
    
    x = round((A_s1 * f_yd - A_s2 * f_yd) / (λ * η * b * f_cd), 2)

    st.write("kus")
    st.write(f"<small>$λ = {λ}$ — betooni pingeploki kuju tegur, tavabetoonil 0,8</small>", unsafe_allow_html=True)
    st.write(f"<small>$\\eta = {η}$ — betooni pingeploki ekvivalentse kõrguse tegur</small>", unsafe_allow_html=True)

    st.write("Kontrollime armatuuri voolamist ")

#Survearmatuuri voolamise kontroll
    st.markdown(fr"Suhteline survetsooni kõrgus")
    st.latex(fr"\footnotesize ξ = \frac{{x}}{{d_{{s1}}}} = \frac{{{x}}}{{{d_s1}}} = {x/d_s1:.2f}")
    ξ = round(x / d_s1, 2)
    st.write(fr"<small> Piirväärtused </small>", unsafe_allow_html=True)
    st.markdown(fr"<small>$ξ_{{c2,lim}}$ = {ξ_c2_lim}</small>", unsafe_allow_html=True)
    st.markdown(fr"<small>$ξ_{{c,lim}}$ = {ξ_c_lim}</small>", unsafe_allow_html=True)


#Kas survearmatuur voolab
    if ξ < ξ_c2_lim:
        #survearmatuur ei voola
        if A_s2 > 0:
            st.markdown(fr"Survearmatuur hakkab voolama, kui $ξ ≥ ξ_{{c2,lim}}$")
            st.latex(fr"\footnotesize ξ < ξ_{{c2,lim}} < ξ_{{c,lim}}")
            st.latex(fr"\footnotesize {{{ξ}}}< {{{ξ_c2_lim}}} < {{{ξ_c_lim}}}")
            st.write("Survearmatuur ei voola.")
            st.write("Survearmatuuri pinge leiame võrrandisüsteemist")
            st.latex(r'''\footnotesize\begin{cases} \eta \cdot f_{cd} \cdot b \cdot \lambda \cdot x + f_{ycd} \cdot A_{s2} - \sigma_{s1} \cdot A_{s1} = 0 \\\sigma_{s2} = \sigma_{sc,u} \left(1 - \frac{d_2}{x}\right)\end{cases}''')
            st.write("Lahendame võrrandisüsteemi ξ suhtes")


            ρ_s1 = float(f"{A_s1 / (b * d_s1):.3g}")
            ρ_s2 = float(f"{A_s2 / (b * d_s1):.3g}")
            λ_1 = float(f"{(f_yd * ρ_s1 - σ_sc_u * ρ_s2) / (2 * λ * η * f_cd):.3g}")
            λ_2 = float(f"{(σ_sc_u * ρ_s2 * d_s2) / (λ * η * f_cd * d_s1):.3g}")
            ξ_uus = float(f"{λ_1 + math.sqrt(λ_1**2 + λ_2):.3g}")

            st.latex(fr"\footnotesize ξ = λ_{{1}} + \sqrt{{λ_{{1}}^2 + λ_{{2}}}} = {λ_1} + \sqrt{{({λ_1})^2 + {λ_2}}} = {λ_1 + math.sqrt(λ_1**2 + λ_2):.3g}")
            st.write("kus")
            st.latex(fr"\footnotesize λ_{{1}} = \frac{{f_{{ycd}} \cdot ρ_{{s1}} - σ_{{sc,u}} \cdot ρ_{{s2}}}}{{2 \cdot λ \cdot η \cdot f_{{cd}}}} = \frac{{{f_yd} \cdot {ρ_s1} - {σ_sc_u} \cdot {ρ_s2}}}{{2 \cdot {λ} \cdot {η} \cdot {f_cd}}} = {(f_yd * ρ_s1 - σ_sc_u * ρ_s2) / (2 * λ * η * f_cd):.3g}")
            st.latex(fr"\footnotesize λ_{{2}} = \frac{{σ_{{sc,u}} \cdot ρ_{{s2}} \cdot d_{{s2}}}}{{λ \cdot η \cdot f_{{cd}} \cdot d_{{s1}}}} = \frac{{{σ_sc_u} \cdot {ρ_s2} \cdot {d_s2}}}{{{λ} \cdot {η} \cdot {f_cd} \cdot {d_s1}}} = {(σ_sc_u * ρ_s2 * d_s2) / (λ * η * f_cd * d_s1):.3g}") 
            st.latex(fr"\footnotesize ρ_{{s1}} = \frac{{A_{{s1}}}}{{b \cdot d_{{s1}}}} = \frac{{{A_s1}}}{{{b} \cdot {d_s1}}} = {A_s1/b/d_s1:.3g}")
            st.latex(fr"\footnotesize ρ_{{s2}} = \frac{{A_{{s2}}}}{{b \cdot d_{{s1}}}} = \frac{{{A_s2}}}{{{b} \cdot {d_s1}}} = {A_s2/b/d_s1:.3g}")
            st.write("Uus survetsooni kõrgus on")
            st.latex(fr"\footnotesize x = ξ \cdot d_{{s1}} = {ξ_uus} \cdot {d_s1} = {ξ_uus * d_s1:.2f} \text{{ mm}}")
            x = round(ξ_uus * d_s1, 2)
            st.write("Leiame effektiivse survetsooni kõrguse")
            st.latex(fr"\footnotesize y = λ \cdot x = {λ} \cdot {x} = {λ * x:.2f} \text{{ mm}}")
            y= round(λ * x, 2)
            st.write("Pinge survearmatuuris")
            st.latex(fr"\footnotesize σ_{{s2}} = σ_{{sc,u}} \left(1 - \frac{{d_{{s2}}}}{{x}}\right) = {σ_sc_u} \left(1 - \frac{{{d_s2}}}{{{x}}}\right) = {σ_sc_u * (1 - d_s2/x):.2f} \text{{ MPa}}")
            σ_s2 = round(σ_sc_u * (1 - d_s2/x),2)
            st.write("Arvutuslik kandevõime")
            st.latex(fr"\footnotesize M_{{Rd}} = η \cdot f_{{cd}} \cdot b \cdot y \cdot (d_{{s1}} - 0.5 \cdot y) + A_{{s2}} \cdot σ_{{s2}} \cdot (d_{{s1}} - d_{{s2}})")
            st.latex(fr"\footnotesize M_{{Rd}} = {η} \cdot {f_cd} \cdot {b} \cdot {y} \cdot ({d_s1} - 0.5 \cdot {y}) + {A_s2} \cdot {σ_s2} \cdot ({d_s1} - {d_s2}) = {(η * f_cd * b * y * (d_s1 - 0.5 * y) + A_s2 * σ_s2 * (d_s1 - d_s2))/10**6:.2f} * 10^6  \text{{ Nmm}}")
            st.latex(fr"\footnotesize M_{{Rd}} = {(η * f_cd * b * y * (d_s1 - 0.5 * y) + A_s2 * σ_s2 * (d_s1 - d_s2))/10**6:.2f} \text{{ kNm}}")
            M_Rd = round((η * f_cd * b * y * (d_s1 - 0.5 * y) + A_s2 * σ_s2 * (d_s1 - d_s2))/10**6, 2)


        else:
            #survearmatuuri pole
            st.write("Survearmatuur puudub.")
    else:
        #survearmatuur voolab
        #Kas tõmbearmatuur voolab
        if ξ > ξ_c_lim:
            #Tõmbearmatuur ei voola
            st.markdown(fr"Tõmbearmatuur hakkab voolama, kui $ξ ≤ ξ_{{c,lim}}$")
            st.latex(fr"\footnotesize  ξ_{{c2,lim}} < ξ_{{c,lim}} < ξ")
            st.latex(fr"\footnotesize {{{ξ_c2_lim}}} < {{{ξ_c_lim}}} < {{{ξ}}}")
            st.write("Ristlõige on ülearmeeritud ja tõmbearmatuur ei voola.")
            st.write("Tõmbearmatuuri pinge leiame võrrandisüsteemist")
            st.latex(r'''\footnotesize\begin{cases} \eta \cdot f_{cd} \cdot b \cdot \lambda \cdot x + f_{ycd} \cdot A_{s2} - \sigma_{s1} \cdot A_{s1} = 0 \\\sigma_{s1} = \sigma_{sc,u} \left(\frac{d_1}{x} - 1\right)\end{cases}''')
            st.write("Lahendame võrrandisüsteemi ξ suhtes")


            ρ_s1 = float(f"{A_s1 / (b * d_s1):.3g}")
            ρ_s2 = float(f"{A_s2 / (b * d_s1):.3g}")
            λ_1 = float(f"{- (f_yd * ρ_s2 + σ_sc_u * ρ_s1) / (2 * λ * η * f_cd):.3g}")
            λ_2 = float(f"{(σ_sc_u * ρ_s1) / (λ * η * f_cd):.3g}")
            ξ_uus = float(f"{λ_1 + math.sqrt(λ_1**2 + λ_2):.3g}")

            st.latex(fr"\footnotesize ξ = λ_{{1}} + \sqrt{{λ_{{1}}^2 + λ_{{2}}}} = {λ_1} + \sqrt{{({λ_1})^2 + {λ_2}}} = {λ_1 + math.sqrt(λ_1**2 + λ_2):.3g}")
            st.write("kus")
            st.latex(fr"\footnotesize λ_{{1}} = - \frac{{f_{{ycd}} \cdot ρ_{{s2}} + σ_{{sc,u}} \cdot ρ_{{s1}}}}{{2 \cdot λ \cdot η \cdot f_{{cd}}}} = - \frac{{{f_yd} \cdot {ρ_s2} + {σ_sc_u} \cdot {ρ_s1}}}{{2 \cdot {λ} \cdot {η} \cdot {f_cd}}} = {- (f_yd * ρ_s2 + σ_sc_u * ρ_s1) / (2 * λ * η * f_cd):.3g}")
            st.latex(fr"\footnotesize λ_{{2}} = \frac{{σ_{{sc,u}} \cdot ρ_{{s1}}}}{{λ \cdot η \cdot f_{{cd}}}} = \frac{{{σ_sc_u} \cdot {ρ_s1}}}{{{λ} \cdot {η} \cdot {f_cd}}} = {(σ_sc_u * ρ_s1) / (λ * η * f_cd):.3g}") 
            st.latex(fr"\footnotesize ρ_{{s1}} = \frac{{A_{{s1}}}}{{b \cdot d_{{s1}}}} = \frac{{{A_s1}}}{{{b} \cdot {d_s1}}} = {A_s1/b/d_s1:.3g}")
            st.latex(fr"\footnotesize ρ_{{s2}} = \frac{{A_{{s2}}}}{{b \cdot d_{{s1}}}} = \frac{{{A_s2}}}{{{b} \cdot {d_s1}}} = {A_s2/b/d_s1:.3g}")
            st.write("Uus survetsooni kõrgus on")
            st.latex(fr"\footnotesize x = ξ \cdot d_{{s1}} = {ξ_uus} \cdot {d_s1} = {ξ_uus * d_s1:.2f} \text{{ mm}}")
            x = round(ξ_uus * d_s1, 2)
            st.write("Leiame effektiivse survetsooni kõrguse")
            st.latex(fr"\footnotesize y = λ \cdot x = {λ} \cdot {x} = {λ * x:.2f} \text{{ mm}}")
            y= round(λ * x, 2)
            st.write("Arvutuslik kandevõime")
            st.latex(fr"\footnotesize M_{{Rd}} = η \cdot f_{{cd}} \cdot b \cdot y \cdot (d_{{s1}} - 0.5 \cdot y) + A_{{s2}} \cdot f_{{yd}} \cdot (d_{{s1}} - d_{{s2}})")
            st.latex(fr"\footnotesize M_{{Rd}} = {η} \cdot {f_cd} \cdot {b} \cdot {y} \cdot ({d_s1} - 0.5 \cdot {y}) + {A_s2} \cdot {f_yd} \cdot ({d_s1} - {d_s2}) = {(η * f_cd * b * y * (d_s1 - 0.5 * y) + A_s2 * f_yd * (d_s1 - d_s2))/10**6:.2f} * 10^6  \text{{ Nmm}} = {(η * f_cd * b * y * (d_s1 - 0.5 * y) + A_s2 * f_yd * (d_s1 - d_s2))/10**6:.2f} \text{{ kNm}}")
            M_Rd = round((η * f_cd * b * y * (d_s1 - 0.5 * y) + A_s2 * f_yd * (d_s1 - d_s2))/10**6, 2)


        else:
            #Tõmbearmatuur voolab
            st.markdown(fr"Tõmbearmatuur hakkab voolama, kui $ξ ≤ ξ_{{c,lim}}$")
            st.latex(fr"\footnotesize ξ_{{c2,lim}} < ξ < ξ_{{c,lim}}")
            st.latex(fr"\footnotesize  {{{ξ_c2_lim}}} < {{{ξ}}}< {{{ξ_c_lim}}}")
            st.write("Tõmbe- ja survearmatuur voolab.")

            st.write("Leiame effektiivse survetsooni kõrguse")
            st.latex(fr"\footnotesize y = λ \cdot x = {λ} \cdot {x} = {λ * x:.2f} \text{{ mm}}")
            y= round(λ * x, 2)
            st.write("Arvutuslik kandevõime")
            st.latex(fr"\footnotesize M_{{Rd}} = η \cdot f_{{cd}} \cdot b \cdot y \cdot (d_{{s1}} - 0.5 \cdot y) + A_{{s2}} \cdot f_{{yd}} \cdot (d_{{s1}} - d_{{s2}})")
            st.latex(fr"\footnotesize M_{{Rd}} = {η} \cdot {f_cd} \cdot {b} \cdot {y} \cdot ({d_s1} - 0.5 \cdot {y}) + {A_s2} \cdot {f_yd} \cdot ({d_s1} - {d_s2}) = {(η * f_cd * b * y * (d_s1 - 0.5 * y) + A_s2 * f_yd * (d_s1 - d_s2))/10**6:.2f} * 10^6  \text{{ Nmm}} ")
            st.latex(fr"\footnotesize M_{{Rd}} = {(η * f_cd * b * y * (d_s1 - 0.5 * y) + A_s2 * f_yd * (d_s1 - d_s2))/10**6:.2f} \text{{ kNm}}")
            M_Rd = round((η * f_cd * b * y * (d_s1 - 0.5 * y) + A_s2 * f_yd * (d_s1 - d_s2))/10**6, 2)
   



    st.html("<br>")

#Roome ------------------------------------------------------------------------------

#Keskmine päevade temperatuur tabel ------------------------------------------
    # Funktsioon kolmanda lahtri väärtuse arvutamiseks
    def arvuta_lahter(delta_t, T):
        try:
            delta_t = float(delta_t)
            T = float(T)
            aste = -((4000 / (273 + T)) - 13.65)
            return round(math.exp(aste) * delta_t, 4)
        except (ValueError, ZeroDivisionError):
            return 0.0

    # Algseisu loomine mälus (kui leht käivitub esimest korda)
    if "tabeli_andmed" not in st.session_state:
        st.session_state.tabeli_andmed = [
            {"Δt_i": "1", "T(Δt_i)": "20.0", "Arvutatud väärtus": f"{arvuta_lahter(1, 20.0):.4f}"}
        ]

    # ARVUTAME SUMMA KOHE KÄIVITUMISEL KOKKU
    t_T_summa = 0.0
    for rida in st.session_state.tabeli_andmed:
        try:
            d_t = int(float(str(rida.get("Δt_i", "1")).strip()))
            temp = float(str(rida.get("T(Δt_i)", "20.0")).strip())
            t_T_summa += round(arvuta_lahter(d_t, temp),2)
        except ValueError:
            pass

    if ajaparandus:
        t_0 = round(t_T_summa * (9/(2 + t_T_summa**1.2) + 1)**α_tsement,2)

#-----------------------------------------------------------------

    #parameetrid
    α_1 = round((35/f_cm)**0.7,3) #betooni tugevuse mõju arvestav parameeter
    α_2 = round((35/f_cm)**0.2,3) #betooni tugevuse mõju arvestav parameeter
    α_3 = round((35/f_cm)**0.5,3) #betooni tugevuse mõju arvestav parameeter

    if f_cm>35:
        β_H = round(1.5 * (1 + (0.0012*RH)**(18)) * h_0 +250*α_3,2) #suhtelisest niiskusest tulenev tegur
        φ_RH = round((1 + (((1 - RH / 100) / (0.1 * (h_0 ** (1/3))))*α_1)*α_2),3)
        if β_H > 1500 * α_3:
            β_H = 1500 * α_3
    else:
        β_H = round(1.5 * (1 + (0.0012*RH)**(18)) * h_0 +250,2)#suhtelisest niiskusest tulenev tegur
        φ_RH = round(1 + (1 - RH / 100) / (0.1 * (h_0 ** (1/3))),3)
        if β_H > 1500:
            β_H = 1500
    β_c_t_t0 = round(((t - t_0)/(β_H + t - t_0))**0.3,3)
    β_t_0 = round(1/(0.1+t_0**(0.2)),3)
    β_f_cm = round(16.8/(f_cm)**(0.5),3)
    φ_0 = round(φ_RH * β_f_cm * β_t_0,3)
    φ_t_t_0 = round(φ_0 * β_c_t_t0,3)



    st.header(f"Roometegur", anchor=f"Roometegur")
    st.write("Roometeguri võib määrata kahel viisil: kas arvutuslikult või määrata see nonogrammist vastavalt standardile. Arvutuslik roometegur on määratud valemiga:")
    st.latex(fr"\footnotesize φ_{{0}}(∞,t_{{0}}) = φ_{{0}} \cdot β_{{c}}(t,t_{{0}}) = {{{φ_0}}} \cdot {{{β_c_t_t0}}} = {φ_t_t_0}" ) 

#-------------------------------------------------------------------

    # x telje suurus
    t_max = 100 * 365

    # Loome 10 000 punkti, mis on alguses ülitihedalt koos, et tagada täiuslik sujuvus
    t_graafik = np.geomspace(t_0 + 0.0001, t_max, 10000)

    # 2. Arvutame roometeguri väärtused täpselt sinu funktsiooniga
    φ_t_graafik = (((t_graafik - t_0)/(β_H + t_graafik - t_0))**0.3) * φ_0

    # 3. Joonise ettevalmistus Matplotlibi objekti (fig) abil
    fig, ax = plt.subplots(figsize=(8, 4))
    ax.plot(t_graafik, φ_t_graafik, label=f'Roometegur $\\phi(t)$', color='blue', lw=2)

    # MUUDATUS: Seame x-telje logaritmiliseks
    ax.set_xscale('log')

    # Lukustame telgede alguspunktid rangesse nulli/t_0-sse, et graafik ei läheks miinuspoolele
    ax.set_xlim(t_0, t_max)
    ax.set_ylim(0, np.max(φ_t_graafik) * 1.1)

    # Kohandame ajamärgid logaritmilisele skaalale sobivaks (kuudest kuni 100 aastani)
    ajapunktid = [t_0, 90, 365, 10 * 365, 100 * 365]
    ajasildid = [f'{t_0} päeva', '3 kuud', '1 aasta', '10 aastat', '100 aastat']
    ax.set_xticks(ajapunktid)
    ax.set_xticklabels(ajasildid)

    # Kujunduselemendid, sildid ja ruudustik (kasutame "both", et log-ruudustik oleks tihe)
    ax.set_title('Roometeguri $\\phi$ kulg ajas kuni 100 aastat', fontsize=14, fontweight='bold')
    ax.set_xlabel('Betooni vanus alates koormamisest', fontsize=12)
    ax.set_ylabel('Roometeguri väärtus $\\phi(t)$', fontsize=12)
    ax.grid(True, which="both", ls="--", alpha=0.5)
    ax.legend(loc='lower right', fontsize=11)

    # 4. KUVAME GRAAFIKU STREAMLITIS
    st.pyplot(fig)


#--------------------------------------------------------------------

    st.markdown(fr"$\footnotesize \text{{kus }} φ_{{0}} \text{{ - on mõttleine roome algtegur, mis leitakse:}}$")
    st.latex(fr"\footnotesize φ_{{0}} = φ_{{RH}} \cdot β(f_{{cm}} \cdot β(t_{{0}})) = {{{φ_RH}}} \cdot {{{β_f_cm}}} \cdot {{{β_t_0}}})) = {{{φ_0}}}")

    st.markdown(fr"$\footnotesize \text{{kus }} φ_{{RH}} \text{{ on tegur, mis arvestab suhtelise niiskuse mõju}}$")
    st.markdown(fr"$\footnotesize \text{{Keskmine 28-päevase survetugevuse võib leida }}$")
    st.latex(fr"\footnotesize f_{{cm}} = f_{{ck}} + 8 = {{{f_ck}}} + 8 = {{{f_cm}}} \text{{ MPa}}")
    if f_cm>35:
        st.markdown(fr"$\footnotesize \text{{kui }} f_{{cm}} \text{{ ≤ 35 MPa}}$")
        st.latex(fr"\footnotesize φ_{{RH}} = 1 + \frac{{1 - \frac{{RH}}{{100}}}}{{0.1 \cdot \sqrt[3]{{h_{{0}}}}}}")
        st.markdown(fr"$\footnotesize \text{{kui }} f_{{cm}} > 35 \text{{ MPa}}$")
        st.latex(fr"\footnotesize φ_{{RH}} = \left[1 + \frac{{1 - \frac{{RH}}{{100}}}}{{0.1 \cdot \sqrt[3]{{h_{{0}}}}}} \cdot α_{{1}}\right]\cdot α_{{2}}") #siia valem
        st.markdown(fr"$\footnotesize h_{{0}} \text{{ on elemendi mõtteline mõõde}}$")
        st.latex(fr"\footnotesize h_{{0}} = \frac{{2 \cdot A_{{c}}}}{{u}} = \frac{{2 \cdot {b} \cdot {h}}}{{2 \cdot ({b} + {h})}} = {h_0:.0f}")
        st.markdown(fr"$\footnotesize A_{{c}} \text{{ - ristlõike pindala, mm²}}$")
        st.markdown(fr"$\footnotesize u \text{{ - ristlõike õhuga kokkupuutev ümbermõõt, mm}}$")
        st.markdown(fr"$\footnotesize RH \text{{ - keskkonna suhteline niiskus, \%}}$")

    else:
        st.markdown(fr"$\footnotesize \text{{kui }} f_{{cm}} \text{{ ≤ 35 MPa}}$")
        st.latex(fr"\footnotesize φ_{{RH}} = 1 + \frac{{1 - \frac{{RH}}{{100}}}}{{0.1 \cdot \sqrt[3]{{h_{{0}}}}}} = 1 + \frac{{1 - \frac{{{RH}}}{{100}}}}{{0.1 \cdot \sqrt[3]{{{h_0}}}}} = {1 + (1 - RH / 100) / (0.1 * (h_0 ** (1/3))):.3g}") #siia valem
        st.markdown(fr"$\footnotesize \text{{kui }} f_{{cm}} > 35 \text{{ MPa}}$")
        st.latex(fr"\footnotesize φ_{{RH}} = \left[1 + \frac{{1 - \frac{{RH}}{{100}}}}{{0.1 \cdot \sqrt[3]{{h_{{0}}}}}} \cdot α_{{1}}\right]\cdot α_{{2}}")
        st.markdown(fr"$\footnotesize h_{{0}} \text{{ on elemendi mõtteline mõõde}}$")
        st.latex(fr"\footnotesize h_{{0}} = \frac{{2 \cdot A_{{c}}}}{{u}} = \frac{{2 \cdot {b} \cdot {h}}}{{2 \cdot ({b} + {h})}} = {h_0:.0f}")
        st.markdown(fr"$\footnotesize A_{{c}} \text{{ - ristlõike pindala, mm²}}$")
        st.markdown(fr"$\footnotesize u \text{{ - ristlõike õhuga kokkupuutev ümbermõõt, mm}}$")
        st.markdown(fr"$\footnotesize RH \text{{ - keskkonna suhteline niiskus, \%}}$")
    st.html("<br>")
    st.markdown(fr"$\footnotesize β(f_{{cm}}) \text{{ on tegur, mis arvestab betooni survetugevuse mõju mõttelisele roome algtegurile}}$")
    st.latex(fr"\footnotesize β(f_{{cm}}) = \frac{{16.8}}{{\sqrt{{f_{{cm}}}}}} = \frac{{16.8}}{{\sqrt{{{f_cm}}}}} = {β_f_cm}")
    
    st.markdown(fr"$\footnotesize β(t_{{0}}) \text{{ on tegur, mis arvestab betooni koormamisaegse vanuse mõju mõttelisele roome algtegurile}}$")
    st.latex(fr"\footnotesize β(t_{{0}}) = \frac{{1}}{{0.1 + t_{{0}}^{{0.2}}}} = \frac{{1}}{{0.1 + {{{t_0}}}^{{0.2}}}} = {β_t_0}")
    st.markdown(fr"$\footnotesize \text{{kus }} t_0 \text{{ vanus päevades koormuse rakendades}}$")

    st.markdown(fr"$\footnotesize β_{{c}}(t,t_{{0}}) \text{{ on pärast koormamise algust roome ajalist kulgu kirjeldav tegur}}$")
    st.latex(fr"\footnotesize β_{{c}}(t,t_{{0}}) = \left[ \frac{{t - t_{{0}}}}{{β_{{H}}+t - t_{{0}}}} \right]^{{0.3}} = \left[ \frac{{{t} - {t_0}}}{{{β_H} + {t} - {t_0}}} \right]^{{0.3}} = {β_c_t_t0}")
    st.markdown(fr"$\footnotesize t \text{{ on betooni vanus päevades vaadeldaval ajal}}$")

    st.markdown(fr"$\footnotesize β_{{H}} \text{{ on suhtelist niiskust ja mõttelisest mõõtmest sõltuv tegur}}$")
    if f_cm>35:
        st.markdown(fr"$\footnotesize \text{{kui }} f_{{cm}} \text{{ ≤ 35 MPa}}$")
        st.latex(fr"\footnotesize β_{{H}} = 1.5 \cdot [1 + (0.0012 \cdot RH)^{{18}}] \cdot h_{{0}} +250 ≤ 1500")
        st.markdown(fr"$\footnotesize \text{{kui }} f_{{cm}} > 35 \text{{ MPa}}$")
        st.latex(fr"\footnotesize β_{{H}} = 1.5 \cdot [1 + (0.0012 \cdot RH)^{{18}}] \cdot h_{{0}} +250 \cdot a_{{3}} ≤ 1500 \cdot a_{{3}}")
        if 1.5 * (1 + (0.0012*RH)**(18)) * h_0 +250 * α_3 > 1500 * α_3:
            st.latex(fr"\footnotesize β_{{H}} = 1.5 \cdot [1 + (0.0012 \cdot {{{RH}}})^{{18}}] \cdot {{{h_0}}} +250 \cdot {{{α_3}}} ≤ 1500 \cdot {{{α_3}}}")
            st.latex(fr"\footnotesize β_{{H}} = {1.5 * (1 + (0.0012*RH)**(18)) * h_0 +250 * α_3} > {1500 * α_3}")
        else:
            st.latex(fr"\footnotesize β_{{H}} = 1.5 \cdot [1 + (0.0012 \cdot {{{RH}}})^{{18}}] \cdot {{{h_0}}} +250 \cdot {{{α_3}}} > 1500 \cdot {{{α_3}}}")
            st.latex(fr"\footnotesize β_{{H}} = {1.5 * (1 + (0.0012*RH)**(18)) * h_0 +250 * α_3} ≤ {1500 * α_3}")
            st.latex(fr"\footnotesize β_{{H}} = {{{β_H}}}")
        
    else:
        st.markdown(fr"$\footnotesize \text{{kui }} f_{{cm}} \text{{ ≤ 35 MPa}}$")
        st.latex(fr"\footnotesize β_{{H}} = 1.5 \cdot [1 + (0.0012 \cdot RH)^{{18}}] \cdot h_{{0}} +250 ≤ 1500")
        if 1.5 * (1 + (0.0012*RH)**(18)) * h_0 +250 > 1500:
            st.latex(fr"\footnotesize β_{{H}} = 1.5 \cdot [1 + (0.0012 \cdot {{{RH}}})^{{18}}] \cdot {{{h_0}}} +250 ≤ 1500")
            st.latex(fr"\footnotesize β_{{H}} = {1.5 * (1 + (0.0012*RH)**(18)) * h_0 +250} > 1500")
        else:
            st.latex(fr"\footnotesize β_{{H}} = 1.5 \cdot [1 + (0.0012 \cdot {{{RH}}})^{{18}}] \cdot {{{h_0}}} +250 > 1500 ")
            st.latex(fr"\footnotesize β_{{H}} = {1.5 * (1 + (0.0012*RH)**(18)) * h_0 +250} ≤ {1500}") 
        st.latex(fr"\footnotesize β_{{H}} = {{{β_H}}}")       
        st.markdown(fr"$\footnotesize \text{{kui }} f_{{cm}} > 35 \text{{ MPa}}$")
        st.latex(fr"\footnotesize β_{{H}} = 1.5 \cdot [1 + (0.0012 \cdot RH)^{{18}}] \cdot h_{{0}} +250 \cdot α_{{3}} ≤ {1500}")

    st.markdown(fr"$\footnotesize α_{{1/2/3}} \text{{ on tegurid mis arvestavad betooni tugevust}}$")
    
    if f_cm>35:
        st.latex(fr"\footnotesize α_{{1}} = \left[ \frac{{35}}{{f_{{cm}}}} \right]^{{0.7}} = \left[ \frac{{35}}{{{{f_cm}}}} \right]^{{0.7}} = {{{α_1}}}") 
        st.latex(fr"\footnotesize α_{{2}} = \left[ \frac{{35}}{{f_{{cm}}}} \right]^{{0.2}} = \left[ \frac{{35}}{{{{f_cm}}}} \right]^{{0.2}} = {{{α_2}}}")
        st.latex(fr"\footnotesize α_{{3}} = \left[ \frac{{35}}{{f_{{cm}}}} \right]^{{0.5}} = \left[ \frac{{35}}{{{{f_cm}}}} \right]^{{0.5}} = {{{α_3}}}")

    else:
        st.latex(fr"""\footnotesize α_{{1}} = \left[ \frac{{35}}{{f_{{cm}}}} \right]^{{0.7}} , 
        α_{{2}} = \left[ \frac{{35}}{{f_{{cm}}}} \right]^{{0.2}} , 
        α_{{3}} = \left[ \frac{{35}}{{f_{{cm}}}} \right]^{{0.5}}""")

    st.write("Tsemendi liigi mõju võib arvesse võtta")
    if ajaparandus:
        st.latex(fr"\footnotesize t_{{0}} = t_{{0,T}} \cdot \left( \frac{{9}}{{2 + t_{{0,T}}^{{1.2}}}} + 1\right)^{{α}} = t_{{0}} = {{{t_T_summa}}} \cdot \left( \frac{{9}}{{2 + t_{{{t_T_summa}}}^{{1.2}}}} + 1\right)^{{{α_tsement}}} = {{{t_0}}}")
         
    else:
        st.latex(fr"\footnotesize t_{{0}} = t_{{0,T}} \cdot \left( \frac{{9}}{{2 + t_{{0,T}}^{{1.2}}}} + 1\right)^{{α}}")

    st.markdown(fr"$\footnotesize \text{{kus α on tsemendi klassist tulenev astendaja}}$")
    st.markdown(fr"$\footnotesize \text{{α = -1 tsemendiklass S}}$")
    st.markdown(fr"$\footnotesize \text{{α = 0 tsemendiklass N}}$")
    st.markdown(fr"$\footnotesize \text{{α = 1 tsemendiklass R}}$")

    if ajaparandus:
        st.latex(fr"\footnotesize t_T = \sum_{{i=1}}^{{n}} e^{{-\left\{{ \frac{{4000}}{{273 + T(Δt_i)}} - 13.65 \right\}}}} \cdot Δt_i = {{{t_T_summa}}}")
    
    else:
         st.latex(fr"\footnotesize t_T = \sum_{{i=1}}^{{n}} e^{{-\left\{{ \frac{{4000}}{{273 + T(Δt_i)}} - 13.65 \right\}}}} \cdot Δt_i ")
    
    st.markdown(fr"$\footnotesize T(Δt_{{i}}) \text{{ on temperatuur ajavahemikus }} Δt_{{i}}$")
    st.markdown(fr"$\footnotesize Δt_{{i}} \text{{ on temperatuuri T kestus päevades}})$")
    



#Keskmine päevade temperatuur tabel visuaalne ---------------------------------------------------------
    st.subheader("Päevade keskmine temperatuur")
    # Nuppude loogika
    def lisa_rida():
        uue_rea_tulemus = arvuta_lahter(1, 20.0)
        st.session_state.tabeli_andmed.append(
            {"Δt_i": "1", "T(Δt_i)": "20.0", "Arvutatud väärtus": f"{uue_rea_tulemus:.4f}"}
        )

    def eemalda_rida():
        if len(st.session_state.tabeli_andmed) > 0:
            st.session_state.tabeli_andmed.pop()

    # Tabeli kuvamine
    muudetud_tabel = st.data_editor(
        st.session_state.tabeli_andmed,
        column_config={
            "Δt_i": st.column_config.TextColumn("Δt_i (päevades)", alignment="center"),
            "T(Δt_i)": st.column_config.TextColumn("T(Δt_i) (temperatuur)", alignment="center"),
            "Arvutatud väärtus": st.column_config.TextColumn("Arvutatud tulemus", disabled=True, alignment="center")
        },
        hide_index=True,
        use_container_width=True,
        key="tabeli_editor"  
    )

    # Andmete turvaline salvestamine taustal mällu
    uuendatud_andmed = []
    for rida in muudetud_tabel:
        try:
            d_t = int(float(str(rida.get("Δt_i", "1")).strip()))
        except ValueError:
            d_t = 1
            
        try:
            temp = float(str(rida.get("T(Δt_i)", "20.0")).strip())
        except ValueError:
            temp = 20.0
        
        tulemus = arvuta_lahter(d_t, temp)
        
        uuendatud_rida = {
            "Δt_i": str(d_t),
            "T(Δt_i)": f"{temp:.1f}",       
            "Arvutatud väärtus": f"{tulemus:.4f}" 
        }
        uuendatud_andmed.append(uuendatud_rida)

    st.session_state.tabeli_andmed = uuendatud_andmed

    # Lisa ja Eemalda nupud tabeli all
    col1, col2, _ = st.columns([1, 1, 4])
    with col1:
        st.button("➕ Lisa", on_click=lisa_rida, use_container_width=True)
    with col2:
        st.button("➖ Eemalda", on_click=eemalda_rida, use_container_width=True)



#--------------------

    for i in range(1, 11):
        st.header(f"Peatükk {i}", anchor=f"peatukk-{i}")
        st.write("Siia tuleb sinu rakenduse peamine tekst, graafikud või tabelid. " * 60)


#Sisukord
with col_sisukord:
    st.markdown("""
        <div class="fikseeritud-sisukord">
            <hr style="margin: 0.1rem 0 0.2rem 0;">
            <ul style="list-style-type: none; padding-left: 0; margin: 0; line-height: 1,6;">
                <li><a href="#Kandevõime">Kandevõime</a></li>
                <li><a href="#Roometegur">Roometegur</a></li>
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
