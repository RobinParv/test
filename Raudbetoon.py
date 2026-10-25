# =====================================================================
# Moodulite import
# =====================================================================

import streamlit as st
import math
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib

# =====================================================================
# Lehekülje seadistus laiaks
# =====================================================================

st.set_page_config(layout="wide")

# =====================================================================
# Külgriba lähteandmed
# =====================================================================

with st.sidebar:
    st.header("Lähteandmed")

    st.subheader("Betooni omadused")
    betooni_klassid = ["C12/15", "C16/20", "C20/25", "C25/30", "C30/37", "C35/45", "C40/50"]
    betooni_klass = st.selectbox("Vali betooni klass:", betooni_klassid, index=3) # Vaikimisi C25/30

    #Betooni klassist tulenevad omadused andmebaas
    survetugevused = {"C12/15": 12,"C16/20": 16,"C20/25": 20,"C25/30": 25,"C30/37": 30,"C35/45": 35,"C40/50": 40}
    elastsusmoodulid = {"C12/15": 27000, "C16/20": 29000, "C20/25": 30000, "C25/30": 31000, "C30/37": 33000, "C35/45": 34000, "C40/50": 35000}
    tõmbetugevused = {"C12/15": 1.6, "C16/20": 1.9, "C20/25": 2.2, "C25/30": 2.6, "C30/37": 2.9, "C35/45": 3.2, "C40/50": 3.5}
    diameetrid = [6, 8, 10, 12, 14, 16, 20, 22, 25, 28, 32]

    #Betooni klassist tulenevad omaduste määramine
    f_ck = survetugevused[betooni_klass]
    E_cm = elastsusmoodulid[betooni_klass]
    f_ctm = tõmbetugevused[betooni_klass]
    f_yk = 500 # Terase survetugevus hiljem
    
    st.markdown(f"##### $E_{{cm}}$ = {E_cm} MPa")
    st.markdown(f"##### $f_{{ctm}}$ = {f_ctm} MPa")
    
    #Ristlõike mõõtmed
    st.subheader("Ristlõike mõõtmed")
    b = st.number_input("Sisesta ristlõike laius b (mm):", min_value=10, max_value=2000, value=250, step=10)
    h = st.number_input("Sisesta ristlõike kõrgus h (mm):", min_value=10, max_value=2000, value=400, step=10)

    #Armatuuri määramine
    st.subheader("Armatuuri omadused")
    A_s1 = st.number_input("Sisesta As1 (mm²):", min_value=0, max_value=10000, value=628, step=10)
    A_s2 = st.number_input("Sisesta As2 (mm²):", min_value=0, max_value=10000, value=0, step=10)
    d_s1 = st.number_input("Sisesta Ds1 (mm):", min_value=0, max_value=h, value=h-30, step=10)
    d_s2 = st.number_input("Sisesta Ds2 (mm):", min_value=0, max_value=h, value=30, step=10)

    #Roomet määravad parameetrid
    st.subheader("Roome määramine")
    t = st.number_input("Vaadeldav hetk päevades:", min_value=0, max_value=10000000, value=365, step=10)
    t_0 = st.number_input("Betooni vanus koormamise hetkel päevades:", min_value=0, max_value=10000000, value=28, step=10)

    #ajaparandus roomele
    ajaparandus = st.toggle("Kasuta ajaparandus tegurit")

    #Vaikimisi
    tsemendi_klass = "N"
    RH = 80

    if ajaparandus:
        RH = st.number_input("Õhuniiskus", min_value=0, max_value=100, value=80, step=5)
        tsemendi_klass = st.selectbox("Tsemendi klass:",options=["S", "N", "R"])

    #Sisejõud
    st.subheader("Sisejõud")
    M = st.number_input("Sisesta M (kNm):", min_value=0, max_value=10000, value=54, step=10)
    N = st.number_input("Sisesta N (kN):", min_value=-1000, max_value=1000, value=0, step=10)
 
# =====================================================================
# Defineeritud omadused
# =====================================================================

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
f_cm = f_ck + 8 #betooni keskmine survetugevus
h_0 = round(2*((b * h) / (2 * (b + h))), 0)
tsemendi_klassid = {"S": -1, "N": 0, "R": 1}
α_tsement = tsemendi_klassid[tsemendi_klass] 

# =====================================================================
# Keskmine päevade temperatuur tabel
# =====================================================================
    
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

# =====================================================================
# Arvutused 
# =====================================================================

# KANDEVÕIME ==========================================================

f_cd = round(f_ck / betooni_osavarutegur, 2)
f_yd = round(f_yk / armatuuri_osavarutegur, 0)
x = round((A_s1 * f_yd - A_s2 * f_yd) / (λ * η * b * f_cd), 2)
ξ = round(x / d_s1, 2)

#ROOME=================================================================

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

# Betooni ja armatuuri pinged =========================================

# Enne pragu enne roomet ==============================================

α_s = round(E_s/E_cm,2)
A_Red = round(b * h + α_s * A_s1 + α_s * A_s2,0)
S_0_Red = round(b * h * h/2 + α_s * A_s1 * (h-d_s1) + α_s * A_s2 * (h-d_s2),0)
y_0_Red = round(S_0_Red / A_Red,1)
x_Red = round(h - y_0_Red,1)
I_Red = round((b * h**3)/12 + b * h * (h/2 - y_0_Red)**2  + α_s * A_s1 * (x_Red - d_s1)**2 + α_s * A_s2 * (x_Red - d_s2)**2,0)
W_c_Red = round(I_Red / x_Red,0) 
W_t_Red = round(I_Red / y_0_Red,0) 
σ_c   = round((N * 1000) / A_Red - (M * 10**6) / W_c_Red, 2)
σ_ct  = round((N * 1000) / A_Red + (M * 10**6) / W_t_Red, 2)
σ_s1 = round(α_s * ((N * 1000) / A_Red + (M * 10**6 * (d_s1 - x_Red)) / I_Red), 2)
σ_s2 = round(α_s * ((N * 1000) / A_Red - (M * 10**6 * (x_Red - d_s2)) / I_Red), 2)
M_cr     = round((f_ctm * W_t_Red) / 10**6, 2)

# Enne pragu peale roomet =============================================

if "loplik_ajal_t_roome" not in st.session_state:
    st.session_state.loplik_ajal_t_roome = True

if st.session_state.loplik_ajal_t_roome:
    E_c_eff = round(1.05 * E_cm / (1 + φ_0 ),0)
else:
    E_c_eff = round(1.05 * E_cm / (1 + φ_t_t_0 ),0)

α_s_eff = round(E_s/E_c_eff,2)
A_Red_eff = round(b * h + α_s_eff * A_s1 + α_s_eff * A_s2,0)
S_0_Red_eff = round(b * h * h/2 + α_s_eff * A_s1 * (h-d_s1) + α_s_eff * A_s2 * (h-d_s2),0)
y_0_Red_eff = round(S_0_Red_eff / A_Red_eff,1)
x_Red_eff = round(h - y_0_Red_eff,1)
I_Red_eff = round((b * h**3)/12 + b * h * (h/2 - y_0_Red_eff)**2  + α_s_eff * A_s1 * (x_Red_eff - d_s1)**2 + α_s_eff * A_s2 * (x_Red_eff - d_s2)**2,0) 
W_c_Red_eff = round(I_Red_eff / x_Red_eff,0) 
W_t_Red_eff = round(I_Red_eff / y_0_Red_eff,0)
σ_c_eff   = round((N * 1000) / A_Red_eff - (M * 10**6) / W_c_Red_eff, 2)
σ_ct_eff  = round((N * 1000) / A_Red_eff + (M * 10**6) / W_t_Red_eff, 2)
σ_s1_eff = round(α_s_eff * ((N * 1000) / A_Red_eff + (M * 10**6 * (d_s1 - x_Red_eff)) / I_Red_eff), 2)
σ_s2_eff = round(α_s_eff * ((N * 1000) / A_Red_eff - (M * 10**6 * (x_Red_eff - d_s2)) / I_Red_eff), 2)
M_cr_eff = round((f_ctm * W_t_Red_eff) / 10**6, 2)

# Peale pragu enne roomet =============================================

if N != 0:
    # 1. Arvutame e_0 alati absoluutväärtusega, sest joonisel 10.2 on see geomeetriline kaugus
    e_0 = (M / abs(N)) * 1000
    e_s1 = e_0 + d_s1 - h / 2
    e_s2 = e_s1 - d_s1 + d_s2
    
    if N != 0:
        # SURVE (Sinu süsteemis miinusmärgiga): surve suurendab survetsooni x
        tegurid = [
            -b / 6.0,                                                            # x³ kordaja
            (b * d_s1) / 2.0 - (b * e_s1) / 2.0,                                 # x² kordaja
            α_s * A_s2 * (d_s1 - d_s2) - α_s * A_s1 * e_s1 - α_s * A_s2 * e_s1,  # x kordaja
            α_s * A_s1 * d_s1 * e_s1 + α_s * A_s2 * d_s2 * e_s1                  # vabaliige
        ]
else:
    # PUHAS PAINE (N = 0)
    tegurid = [
        b / 2.0,                                                             # x² kordaja
        α_s * A_s1 + α_s * A_s2,                                             # x kordaja
        - (α_s * A_s1 * d_s1 + α_s * A_s2 * d_s2)                            # vabaliige
    ]

# Lahendite leidmine NumPy abil
pragunenud_ristloike_vorrand = np.roots(tegurid)

x_cr = round([np.real(z) for z in pragunenud_ristloike_vorrand if np.isreal(z) and np.real(z) > 0][0],2)
σ_c0 = abs(N) * 1000 / (((b * x_cr) / 2) - (α_s * A_s1 * ((d_s1 / x_cr) - 1)) + (α_s * A_s2 * (1 - (d_s2 / x_cr))))
A_cr_Red = round(b * x_cr + α_s * A_s1 + α_s * A_s2,0)
y_cr_Red = round((b * x_cr * (d_s1 - x_cr / 2) + α_s * A_s2 * (d_s1 - d_s2)) / A_cr_Red,2)
I_cr_Red = round((b * x_cr**3 / 12) + b * x_cr * (d_s1 - x_cr / 2 - y_cr_Red)**2 + α_s * A_s1 * y_cr_Red**2 + α_s * A_s2 * (d_s1 - d_s2 - y_cr_Red)**2,0)
if N == 0:
    σ_cr_c = round(-(M * 10**6 * x_cr) / I_cr_Red,2)
    σ_cr_s1 = round(α_s * ((M * 10**6 *(d_s1 - x_cr)) / I_cr_Red),2)
    σ_cr_s2 = round(α_s * ((M * 10**6 * (d_s2 - x_cr)) / I_cr_Red),2)
else: 
    σ_cr_c = round(-(abs(N) * 1000 / A_cr_Red) - (abs(N) * 1000 * e_0 * x_cr) / I_cr_Red,2)
    σ_cr_s1 = round(α_s * (-(abs(N) * 1000 / A_cr_Red) + (abs(N) * e_0 * 1000 * (d_s1 - x_cr)) / I_cr_Red),2)
    σ_cr_s2 = round(α_s * (-(abs(N) * 1000 / A_cr_Red) - (abs(N) * e_0 * 1000 * (x_cr - d_s2)) / I_cr_Red),2)

# Peale pragu peale roomet =============================================

if N != 0:
    # 1. Arvutame e_0 alati absoluutväärtusega, sest joonisel 10.2 on see geomeetriline kaugus
    e_0 = (M / abs(N)) * 1000
    e_s1 = e_0 + d_s1 - h / 2
    e_s2 = e_s1 - d_s1 + d_s2
    
    if N != 0:
        # SURVE (Sinu süsteemis miinusmärgiga): surve suurendab survetsooni x
        tegurid_roome = [
            -b / 6.0,                                                            # x³ kordaja
            (b * d_s1) / 2.0 - (b * e_s1) / 2.0,                                 # x² kordaja
            α_s_eff * A_s2 * (d_s1 - d_s2) - α_s_eff * A_s1 * e_s1 - α_s_eff * A_s2 * e_s1,  # x kordaja
            α_s_eff * A_s1 * d_s1 * e_s1 + α_s_eff * A_s2 * d_s2 * e_s1                  # vabaliige
        ]
else:
    # PUHAS PAINE (N = 0)
    tegurid_roome = [
        b / 2.0,                                                             # x² kordaja
        α_s_eff * A_s1 + α_s_eff * A_s2,                                             # x kordaja
        - (α_s_eff * A_s1 * d_s1 + α_s_eff * A_s2 * d_s2)                            # vabaliige
    ]

# Lahendite leidmine NumPy abil
pragunenud_ristloike_vorrand_roome = np.roots(tegurid_roome)

x_cr_eff = round([np.real(z) for z in pragunenud_ristloike_vorrand_roome if np.isreal(z) and np.real(z) > 0][0],2)
σ_c0_eff = abs(N) * 1000 / (((b * x_cr_eff) / 2) - (α_s_eff * A_s1 * ((d_s1 / x_cr_eff) - 1)) + (α_s_eff * A_s2 * (1 - (d_s2 / x_cr_eff))))
A_cr_Red_eff = round(b * x_cr_eff + α_s_eff * A_s1 + α_s_eff * A_s2,0)
y_cr_Red_eff = round((b * x_cr_eff * (d_s1 - x_cr_eff / 2) + α_s_eff * A_s2 * (d_s1 - d_s2)) / A_cr_Red_eff,2)
I_cr_Red_eff = round((b * x_cr_eff**3 / 12) + b * x_cr_eff * (d_s1 - x_cr_eff / 2 - y_cr_Red_eff)**2 + α_s_eff * A_s1 * y_cr_Red_eff**2 + α_s_eff * A_s2 * (d_s1 - d_s2 - y_cr_Red_eff)**2,0)
if N == 0:
    σ_cr_c_eff = round(-(M * 10**6 * x_cr_eff) / I_cr_Red_eff,2)
    σ_cr_s1_eff = round(α_s_eff * ((M * 10**6 *(d_s1 - x_cr_eff)) / I_cr_Red_eff),2)
    σ_cr_s2_eff = round(α_s_eff * ((M * 10**6 * (d_s2 - x_cr_eff)) / I_cr_Red_eff),2)
else: 
    σ_cr_c_eff = round(-(abs(N) * 1000 / A_cr_Red_eff) - (abs(N) * 1000 * e_0 * x_cr_eff) / I_cr_Red_eff,2)
    σ_cr_s1_eff = round(α_s_eff * (-(abs(N) * 1000 / A_cr_Red_eff) + (abs(N) * e_0 * 1000 * (d_s1 - x_cr_eff)) / I_cr_Red_eff), 2)
    σ_cr_s2_eff = round(α_s_eff * (-(abs(N) * 1000 / A_cr_Red_eff) - (abs(N) * e_0 * 1000 * (x_cr_eff - d_s2)) / I_cr_Red_eff),2)


# =====================================================================
# Peatükid
# =====================================================================

# Kandevõime ==========================================================

def kandevoime_funktsioon():

    global x, d_s1, ξ, f_ck, betooni_osavarutegur, f_yk, armatuuri_osavarutegur, A_s1, A_s2, f_yd, λ, η, b, f_cd    

    st.header(f"Kandevõime", anchor=f"Kandevõime")
    st.write("Leiame arvutuslikud tugevused")
    st.latex(fr"\footnotesize f_{{cd}} = \frac{{f_{{ck}}}}{{\gamma_{{c}}}} = \frac{{{f_ck}}}{{{betooni_osavarutegur}}} = {f_ck/betooni_osavarutegur:.2f} \text{{ MPa}}")
    st.latex(fr"\footnotesize f_{{yd}} = \frac{{f_{{yk}}}}{{\gamma_{{s}}}} = \frac{{{f_yk}}}{{{armatuuri_osavarutegur}}} = {f_yk/armatuuri_osavarutegur:.0f} \text{{ MPa}}")


    st.write("kus")
    st.write(f"<small>$\\gamma_{{c}} = {betooni_osavarutegur}$ — betooni osavarutegur</small>", unsafe_allow_html=True)
    st.write(f"<small>$\\gamma_{{s}} = {armatuuri_osavarutegur}$ — armatuurterase osavarutegur</small>", unsafe_allow_html=True) 

    st.html("<br>")

    st.write("Survekõrguse leidmine")  
    if A_s2 > 0:
        st.latex(fr"\footnotesize x = \frac{{A_{{s1}} \cdot f_{{yd}} - A_{{s2}} \cdot f_{{yd}}}}{{λ \cdot b \cdot η \cdot f_{{cd}}}} = \frac{{{A_s1} \cdot {f_yd} - {A_s2} \cdot {f_yd}}}{{ {λ} \cdot {η} \cdot {b} \cdot {f_cd}}} = {(A_s1 * f_yd - A_s2 * f_yd) / (λ * η * b):.2f} \text{{ mm}}")
        
    else:
        st.latex(fr"\footnotesize x = \frac{{A_{{s1}} \cdot f_{{yd}} - A_{{s2}} \cdot f_{{yd}}}}{{λ \cdot b \cdot η \cdot f_{{cd}}}} = \frac{{{A_s1} \cdot {f_yd}}}{{ {λ} \cdot {η} \cdot {b} \cdot {f_cd}}} = {(A_s1 * f_yd - A_s2 * f_yd) / (λ * η * b):.2f} \text{{ mm}}")
    
    st.write("kus")
    st.write(f"<small>$λ = {λ}$ — betooni pingeploki kuju tegur, tavabetoonil 0,8</small>", unsafe_allow_html=True)
    st.write(f"<small>$\\eta = {η}$ — betooni pingeploki ekvivalentse kõrguse tegur</small>", unsafe_allow_html=True)

    st.write("Kontrollime armatuuri voolamist ")

#Survearmatuuri voolamise kontroll
    st.markdown(fr"Suhteline survetsooni kõrgus")
    st.latex(fr"\footnotesize ξ = \frac{{x}}{{d_{{s1}}}} = \frac{{{x}}}{{{d_s1}}} = {ξ:.2f}")
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
   



def roometegur_funktsioon():

    st.header(f"Roometegur", anchor=f"Roometegur")
    st.write("Roometeguri võib määrata kahel viisil: kas arvutuslikult või määrata see nonogrammist vastavalt standardile. Arvutuslik roometegur on määratud valemiga:")
    st.latex(fr"\footnotesize φ_{{0}}(∞,t_{{0}}) = φ_{{0}} \cdot β_{{c}}(t,t_{{0}}) = {{{φ_0}}} \cdot {{{β_c_t_t0}}} = {φ_t_t_0}" ) 

#ROOMETEGURI GRAAFIK----------------------------------------------------------

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


# =====================================================================
# Keskmine päevade temperatuur tabel visuaalne 
# =====================================================================

    # =====================================================================
    # Keskmine päevade temperatuur tabel visuaalne
    # =====================================================================
    st.subheader("Päevade keskmine temperatuur")

    # Päästik, mis sunnib lehe kohe uuesti käivituma, kui kasutaja muudab lahtrit ja vajutab Enter
    def tabeli_muudatuse_paastik():
        st.rerun()

    # Nuppude loogika (Lisame puhtad ujuvpomaarvud, mitte teksti "1" ja "20.0")
    def lisa_rida():
        st.session_state.tabeli_andmed.append({"Δt_i": 1.0, "T(Δt_i)": 20.0})

    def eemalda_rida():
        if len(st.session_state.tabeli_andmed) > 0:
            st.session_state.tabeli_andmed.pop()

    # Kontrollime reaalajas kasutaja sisestatud muudatusi otse editori sisemälust enne kuvamist
    kuvatavad_andmed = []
    if "tabeli_editor" in st.session_state and "edited_rows" in st.session_state.tabeli_editor:
        muudatused = st.session_state.tabeli_editor["edited_rows"]
        for i, algne_rida in enumerate(st.session_state.tabeli_andmed):
            kopeeritud_rida = algne_rida.copy()
            if i in muudatused:
                kopeeritud_rida.update(muudatused[i])
            kuvatavad_andmed.append(kopeeritud_rida)
    else:
        kuvatavad_andmed = st.session_state.tabeli_andmed

    # Arvutame igale reale dünaamiliselt värske "Arvutatud tulemus" veeru väärtuse kuvamiseks
    for rida in kuvatavad_andmed:
        try:
            d_t = float(rida.get("Δt_i", 1.0))
            temp = float(rida.get("T(Δt_i)", 20.0))
            rida["Arvutatud väärtus"] = f"{arvuta_lahter(d_t, temp):.4f}"
        except (ValueError, TypeError):
            rida["Arvutatud väärtus"] = "0.0000"

    # Tabeli kuvamine (Kasutame TextColumn asemel NumberColumn, et sisendid oleksid puhtad arvud)
    muudetud_tabel = st.data_editor(
        kuvatavad_andmed,
        column_config={
            "Δt_i": st.column_config.NumberColumn("Δt_i (päevades)", alignment="center", min_value=0.0, format="%.1f"),
            "T(Δt_i)": st.column_config.NumberColumn("T(Δt_i) (temperatuur °C)", alignment="center", format="%.1f"),
            "Arvutatud väärtus": st.column_config.TextColumn("Arvutatud tulemus", disabled=True, alignment="center")
        },
        hide_index=True,
        use_container_width=True,
        key="tabeli_editor",
        on_change=tabeli_muudatuse_paastik  
    )

    # Salvestame reaalajas uuendatud andmed mällu tagasi
    st.session_state.tabeli_andmed = muudetud_tabel

    # Lisa ja Eemalda nupud tabeli all
    col1, col2, _ = st.columns([1, 1, 4])
    with col1:
        st.button("➕ Lisa", on_click=lisa_rida, use_container_width=True)
    with col2:
        st.button("➖ Eemalda", on_click=eemalda_rida, use_container_width=True)

    # Kasutame eelmise lehe tulemust
    tulemus_1 = st.session_state.get("tulemus_1", 0.0)

def pingete_funktsioon():
#Betooni ja armatuuri pinged ------------------------------------------------------------------------------
    st.header(f"Betooni ja armatuuri pinged", anchor=f"Betooni ja armatuuri pinged")
    st.subheader("Enne pragu enne roomet")
    st.write("""Enne pragude tekkimist betoonis eeldatakse tavaliselt raudbetoonelemendi kasutusseisundis betooni ja armatuuri elastset töötamist. Elemendi lõike mingis punktis on betooni ja armatuuri suhtelised deformatsioonid võrdsed: """)
    st.latex(fr"\footnotesize ε_{{c}} = \frac{{σ_{{c}}}}{{E_{{cm}}}} = ε_{{s}} = \frac{{σ_{{s}}}}{{E_{{s}}}}")
    st.write("kust saame armatuuri pinge")
    st.latex(fr"\footnotesize σ_{{s}} = \frac{{E_{{s}}}}{{E_{{cm}}}} \cdot σ_{{c}} = α_{{s}} \cdot σ_{{c}}")
    st.write("kus")
    st.latex(fr"\footnotesize α_{{s}} = \frac{{E_{{s}}}}{{E_{{cm}}}} = \frac{{{E_s}}}{{{E_cm}}} = {α_s}")
    st.write("Arvutustes on otstarbekohane asendada kahest materjalist koosneva elemendi tegelik ristlõige samaväärse betoonristlõikega - redutseeritud ristlõikega")
    st.write("Redutseeritud ristlõike pindala")
    if A_s2 > 0:
        st.latex(fr"\footnotesize A_{{red}} = A_{{c}} + α_{{s}} \cdot A_{{s1}} + α_{{s}} \cdot A_{{s2}} = {{{b}}} \cdot {{{h}}} + {{{α_s}}} \cdot {{{A_s1}}} + {{{α_s}}} \cdot {{{A_s2}}} = {{{A_Red}}} \text{{ mm}}^{{2}}")
        st.write("Redutseeritud ristlõike staatiline moment alumise serva suhtes")
        st.latex(fr"\footnotesize S_{{0,Red}} = S_{{0,c}} + α_{{s}} \cdot A_{{s1}} \cdot (h - d{{s1}})+ α_{{s}} \cdot A_{{s2}} \cdot (h - d{{s2}})")
        st.latex(fr"\footnotesize S_{{0,Red}} = {{{b}}} \cdot {{{h}}} \cdot \frac{{{h}}}{{2}} + {{{α_s}}} \cdot {{{A_s1}}} \cdot ({{{h}}} - {{{d_s1}}}) + {{{α_s}}} \cdot {{{A_s2}}} \cdot ({{{h}}} - {{{d_s2}}}) = {{{S_0_Red}}} \text{{ mm}}^{{3}}")
    else:
        st.latex(fr"\footnotesize A_{{red}} = A_{{c}} + α_{{s}} \cdot A_{{s1}} + α_{{s}} \cdot A_{{s2}} = {{{b}}} \cdot {{{h}}} + {{{α_s}}} \cdot {{{A_s1}}} = {{{A_Red}}} \text{{ mm}}^{{2}}")
        st.write("Redutseeritud ristlõike staatiline moment alumise serva suhtes")
        st.latex(fr"\footnotesize S_{{0,Red}} = S_{{0,c}} + α_{{s}} \cdot A_{{s1}} \cdot (h - d{{s1}})+ α_{{s}} \cdot A_{{s2}} \cdot (h - d{{s2}})")  
        st.latex(fr"\footnotesize S_{{0,Red}} = {{{b}}} \cdot {{{h}}} \cdot \frac{{{h}}}{{2}} + {{{α_s}}} \cdot {{{A_s1}}} \cdot ({{{h}}} - {{{d_s1}}}) + {{{α_s}}} = {{{S_0_Red}}} \text{{ mm}}^{{3}}")            
    
    st.write("Redutseeritud ristlõike raskuskeskme kaugus ristlõike alumisest servast ")
    st.latex(fr"\footnotesize y_{{0,Red}}=\frac{{S_{{0,Red}}}}{{A_{{Red}}}} = \frac{{{S_0_Red}}}{{{A_Red}}} = {{{y_0_Red}}} \text{{ mm}}")
    st.write("Survetsooni kõrgus on")
    st.latex(fr"\footnotesize x_{{Red}} = h - y_{{0,Red}} = {{{h}}} - {{{y_0_Red}}} = {{{x_Red}}} \text{{ mm}}")
    st.write("Redutseeritud ristlõike inertsimoment")

    if A_s2 > 0:
        st.latex(fr"\footnotesize I_{{Red}} = I_{{c}} + α_{{s}} \cdot A_{{s1}} \cdot y_{{s1}}^{{2}}+ α_{{s}} \cdot A_{{s2}} \cdot y_{{s2}}^{{2}}")
        st.latex(fr"\footnotesize I_{{Red}} = \frac{{{{{b}}} \cdot {{{h}}}^{{3}}}}{{12}} + {{{b}}} \cdot {{{h}}} \cdot (\frac{{{h}}}{{2}} - {{{y_0_Red}}})^{{2}}  + {{{α_s}}} \cdot {{{A_s1}}} \cdot ({{{x_Red}}} - {{{d_s1}}})^{{2}} + {{{α_s}}} \cdot {{{A_s2}}} \cdot ({{{x_Red}}} - {{{d_s2}}})^{{2}}")
        st.latex(fr"\footnotesize I_{{Red}} = {{{I_Red}}} \text{{ mm}}^{{4}}")
    else:
        st.latex(fr"\footnotesize I_{{Red}} = I_{{c}} + α_{{s}} \cdot A_{{s1}} \cdot y_{{s1}}^{{2}}+ α_{{s}} \cdot A_{{s2}} \cdot y_{{s2}}^{{2}} ")
        st.latex(fr"\footnotesize I_{{Red}} = \frac{{{{{b}}} \cdot {{{h}}}^{{3}}}}{{12}} + {{{b}}} \cdot {{{h}}} \cdot (\frac{{{h}}}{{2}} - {{{y_0_Red}}})^{{2}}  + {{{α_s}}} \cdot {{{A_s1}}} \cdot ({{{x_Red}}} - {{{d_s1}}})^{{2}}")
        st.latex(fr"\footnotesize I_{{Red}} = {{{I_Red}}} \text{{ mm}}^{{4}}")
    st.markdown(fr"$\footnotesize \text{{ kus }}$")
    st.markdown(fr"$\footnotesize I_{{c}} \text{{ on betooni inertsimoment redutseeritud ristlõike raskuskeskme suhtes}}$")
    st.markdown(fr"$\footnotesize y_{{s1}} \text{{ ja }} y_{{s2}} \text{{ on armatuuri kaugus redutseeritud ristlõike raskuskeskmest}}$")
    st.write("Vastupanumoment surutud serva suhtes")
    st.latex(fr"\footnotesize W_{{c,Red}} = \frac{{I_{{Red}}}}{{x}} = \frac{{{I_Red}}}{{{x_Red}}} = {W_c_Red}")
    st.write("Vastupanumoment tõmmatud serva suhtes")
    st.latex(fr"\footnotesize W_{{t,Red}} = \frac{{I_{{Red}}}}{{y_{{0,Red}}}} = \frac{{{I_Red}}}{{{y_0_Red}}} = {W_t_Red}")


    st.write("Betooni pinge ristlõike surutud ja tõmmatud servas")
    if N == 0:
        st.latex(fr"\footnotesize σ_{{c,max}} = \frac{{N}}{{A_{{Red}}}} - \frac{{M}}{{W_{{c,Red}}}} = - \frac{{{M} \cdot 10^6}}{{{W_c_Red}}} = {σ_c} \text{{ N/mm}}^2")
        st.latex(fr"\footnotesize σ_{{ct,max}} = \frac{{N}}{{A_{{Red}}}} + \frac{{M}}{{W_{{t,Red}}}} = \frac{{{M} \cdot 10^6}}{{{W_t_Red}}} = {σ_ct} \text{{ N/mm}}^2")
    else:
        st.latex(fr"\footnotesize σ_{{c,max}} = \frac{{N}}{{A_{{Red}}}} - \frac{{M}}{{W_{{c,Red}}}} = \frac{{{N} \cdot 10^3}}{{{A_Red}}} - \frac{{{M} \cdot 10^6}}{{{W_c_Red}}} = {σ_c} \text{{ N/mm}}^2")
        st.latex(fr"\footnotesize σ_{{ct,max}} = \frac{{N}}{{A_{{Red}}}} + \frac{{M}}{{W_{{t,Red}}}} = \frac{{{N} \cdot 10^3}}{{{A_Red}}} + \frac{{{M} \cdot 10^6}}{{{W_t_Red}}} = {σ_ct} \text{{ N/mm}}^2")

    st.write("Armatuuri pinged")
    if N == 0:
        st.latex(fr"\footnotesize σ_{{s1}} = \alpha_{{s}} \cdot \left( \frac{{N}}{{A_{{Red}}}} + \frac{{M \cdot (d_{{s1}} - x_{{Red}})}}{{{I_Red}}} \right) = {α_s} \cdot \left( \frac{{{M} \cdot 10^6 \cdot ({d_s1} - {x_Red})}}{{{I_Red}}} \right) = {σ_s1} \text{{ N/mm}}^2")
        st.latex(fr"\footnotesize σ_{{s2}} = \alpha_{{s}} \cdot \left( \frac{{N}}{{A_{{Red}}}} - \frac{{M \cdot (x_{{Red}} - d_{{s2}})}}{{{I_Red}}} \right) = {α_s} \cdot \left( - \frac{{{M} \cdot 10^6 \cdot ({x_Red} - {d_s2})}}{{{I_Red}}} \right) = {σ_s2} \text{{ N/mm}}^2")
    else:
        st.latex(fr"\footnotesize σ_{{s1}} = \alpha_{{s}} \cdot \left( \frac{{N}}{{A_{{Red}}}} + \frac{{M \cdot (d_{{s1}} - x_{{Red}})}}{{{I_Red}}} \right) = {α_s} \cdot \left( \frac{{{N} \cdot 10^3}}{{{A_Red}}} + \frac{{{M} \cdot 10^6 \cdot ({d_s1} - {x_Red})}}{{{I_Red}}} \right) = {σ_s1} \text{{ N/mm}}^2")
        st.latex(fr"\footnotesize σ_{{s2}} = \alpha_{{s}} \cdot \left( \frac{{N}}{{A_{{Red}}}} - \frac{{M \cdot (x_{{Red}} - d_{{s2}})}}{{{I_Red}}} \right) = {α_s} \cdot \left( \frac{{{N} \cdot 10^3}}{{{A_Red}}} + \frac{{{M} \cdot 10^6 \cdot ({x_Red} - {d_s2})}}{{{I_Red}}} \right) = {σ_s2} \text{{ N/mm}}^2")



    st.subheader("Enne pragu peale roomet")

    st.write("Roome arenedes tuleb leida uus betooni elastsusmoodul")
    if st.session_state.loplik_ajal_t_roome:
        st.latex(fr"\footnotesize E_{{c,eff}} = \frac{{1.05 \cdot E_{{cm}}}}{{1 + φ(t,t_{{0}})}} = \frac{{1.05 \cdot {E_cm}}}{{1 + {φ_0}}} = {E_c_eff}")    
    else:
       st.latex(fr"\footnotesize E_{{c,eff}} = \frac{{1.05 \cdot E_{{cm}}}}{{1 + φ(t,t_{{0}})}} = \frac{{1.05 \cdot {E_cm}}}{{1 + {φ_t_t_0}}} = {E_c_eff}")     
    st.latex(fr"\footnotesize α_{{s}} = \frac{{E_{{s}}}}{{E_{{c,eff}}}} = \frac{{{E_s}}}{{{E_c_eff}}} = {α_s_eff}")

    st.toggle("Arvuta pinged ajahetkel t / peale lõplikku roomet", value=st.session_state.loplik_ajal_t_roome, key="roome_nupp_yleval", on_change=lambda: st.session_state.update({"loplik_ajal_t_roome": st.session_state.roome_nupp_yleval, "roome_nupp_all": st.session_state.roome_nupp_yleval}))


    st.write("Redutseeritud ristlõike pindala")
    if A_s2 > 0:
        st.latex(fr"\footnotesize A_{{red}} = A_{{c}} + α_{{s}} \cdot A_{{s1}} + α_{{s}} \cdot A_{{s2}} = {{{b}}} \cdot {{{h}}} + {{{α_s_eff}}} \cdot {{{A_s1}}} + {{{α_s_eff}}} \cdot {{{A_s2}}} = {{{A_Red_eff}}} \text{{ mm}}^{{2}}")
        st.write("Redutseeritud ristlõike staatiline moment alumise serva suhtes")
        st.latex(fr"\footnotesize S_{{0,Red}} = S_{{0,c}} + α_{{s}} \cdot A_{{s1}} \cdot (h - d{{s1}})+ α_{{s}} \cdot A_{{s2}} \cdot (h - d{{s2}})")
        st.latex(fr"\footnotesize S_{{0,Red}} = {{{b}}} \cdot {{{h}}} \cdot \frac{{{h}}}{{2}} + {{{α_s_eff}}} \cdot {{{A_s1}}} \cdot ({{{h}}} - {{{d_s1}}}) + {{{α_s_eff}}} \cdot {{{A_s2}}} \cdot ({{{h}}} - {{{d_s2}}}) = {{{S_0_Red_eff}}} \text{{ mm}}^{{3}}")
    else:
        st.latex(fr"\footnotesize A_{{red}} = A_{{c}} + α_{{s}} \cdot A_{{s1}} + α_{{s}} \cdot A_{{s2}} = {{{b}}} \cdot {{{h}}} + {{{α_s_eff}}} \cdot {{{A_s1}}} = {{{A_Red_eff}}} \text{{ mm}}^{{2}}")
        st.write("Redutseeritud ristlõike staatiline moment alumise serva suhtes")
        st.latex(fr"\footnotesize S_{{0,Red}} = S_{{0,c}} + α_{{s}} \cdot A_{{s1}} \cdot (h - d{{s1}})+ α_{{s}} \cdot A_{{s2}} \cdot (h - d{{s2}})")  
        st.latex(fr"\footnotesize S_{{0,Red}} = {{{b}}} \cdot {{{h}}} \cdot \frac{{{h}}}{{2}} + {{{α_s_eff}}} \cdot {{{A_s1}}} \cdot ({{{h}}} - {{{d_s1}}}) + {{{α_s_eff}}} = {{{S_0_Red_eff}}} \text{{ mm}}^{{3}}")            
    
    st.write("Redutseeritud ristlõike raskuskeskme kaugus ristlõike alumisest servast ")
    st.latex(fr"\footnotesize y_{{0,Red}}=\frac{{S_{{0,Red}}}}{{A_{{Red}}}} = \frac{{{S_0_Red_eff}}}{{{A_Red_eff}}} = {{{y_0_Red_eff}}} \text{{ mm}}")
    st.write("Survetsooni kõrgus on")
    st.latex(fr"\footnotesize x_{{Red}} = h - y_{{0,Red}} = {{{h}}} - {{{y_0_Red_eff}}} = {{{x_Red_eff}}} \text{{ mm}}")
    st.write("Redutseeritud ristlõike inertsimoment")

    if A_s2 > 0:
        st.latex(fr"\footnotesize I_{{Red}} = I_{{c}} + α_{{s}} \cdot A_{{s1}} \cdot y_{{s1}}^{{2}}+ α_{{s}} \cdot A_{{s2}} \cdot y_{{s2}}^{{2}}")
        st.latex(fr"\footnotesize I_{{Red}} = \frac{{{{{b}}} \cdot {{{h}}}^{{3}}}}{{12}} + {{{b}}} \cdot {{{h}}} \cdot (\frac{{{h}}}{{2}} - {{{y_0_Red_eff}}})^{{2}}  + {{{α_s_eff}}} \cdot {{{A_s1}}} \cdot ({{{x_Red_eff}}} - {{{d_s1}}})^{{2}} + {{{α_s_eff}}} \cdot {{{A_s2}}} \cdot ({{{x_Red_eff}}} - {{{d_s2}}})^{{2}}")
        st.latex(fr"\footnotesize I_{{Red}} = {{{I_Red_eff}}} \text{{ mm}}^{{4}}")
    else:
        st.latex(fr"\footnotesize I_{{Red}} = I_{{c}} + α_{{s}} \cdot A_{{s1}} \cdot y_{{s1}}^{{2}}+ α_{{s}} \cdot A_{{s2}} \cdot y_{{s2}}^{{2}} ")
        st.latex(fr"\footnotesize I_{{Red}} = \frac{{{{{b}}} \cdot {{{h}}}^{{3}}}}{{12}} + {{{b}}} \cdot {{{h}}} \cdot (\frac{{{h}}}{{2}} - {{{y_0_Red_eff}}})^{{2}}  + {{{α_s_eff}}} \cdot {{{A_s1}}} \cdot ({{{x_Red_eff}}} - {{{d_s1}}})^{{2}}")
        st.latex(fr"\footnotesize I_{{Red}} = {{{I_Red_eff}}} \text{{ mm}}^{{4}}")
    st.markdown(fr"$\footnotesize \text{{ kus }}$")
    st.markdown(fr"$\footnotesize I_{{c}} \text{{ on betooni inertsimoment redutseeritud ristlõike raskuskeskme suhtes}}$")
    st.markdown(fr"$\footnotesize y_{{s1}} \text{{ ja }} y_{{s2}} \text{{ on armatuuri kaugus redutseeritud ristlõike raskuskeskmest}}$")
    st.write("Vastupanumoment surutud serva suhtes")
    st.latex(fr"\footnotesize W_{{c,Red}} = \frac{{I_{{Red}}}}{{x}} = \frac{{{I_Red_eff}}}{{{x_Red_eff}}} = {W_c_Red_eff}")
    st.write("Vastupanumoment tõmmatud serva suhtes")
    st.latex(fr"\footnotesize W_{{t,Red}} = \frac{{I_{{Red}}}}{{y_{{0,Red}}}} = \frac{{{I_Red_eff}}}{{{y_0_Red_eff}}} = {W_t_Red_eff}")
 
    st.write("Betooni pinge ristlõike surutud ja tõmmatud servas (peale roomet)")
    if N == 0:
        st.latex(fr"\footnotesize σ_{{c,max}} = \frac{{N}}{{A_{{Red}}}} - \frac{{M}}{{W_{{c,Red}}}} = - \frac{{{M} \cdot 10^6}}{{{W_c_Red_eff}}} = {σ_c_eff} \text{{ N/mm}}^2")
        st.latex(fr"\footnotesize σ_{{ct,max}} = \frac{{N}}{{A_{{Red}}}} + \frac{{M}}{{W_{{t,Red}}}} = \frac{{{M} \cdot 10^6}}{{{W_t_Red_eff}}} = {σ_ct_eff} \text{{ N/mm}}^2")
    else:
        st.latex(fr"\footnotesize σ_{{c,max}} = \frac{{N}}{{A_{{Red}}}} - \frac{{M}}{{W_{{c,Red}}}} = \frac{{{N} \cdot 10^3}}{{{A_Red_eff}}} - \frac{{{M} \cdot 10^6}}{{{W_c_Red_eff}}} = {σ_c_eff} \text{{ N/mm}}^2")
        st.latex(fr"\footnotesize σ_{{ct,max}} = \frac{{N}}{{A_{{Red}}}} + \frac{{M}}{{W_{{t,Red}}}} = \frac{{{N} \cdot 10^3}}{{{A_Red_eff}}} + \frac{{{M} \cdot 10^6}}{{{W_t_Red_eff}}} = {σ_ct_eff} \text{{ N/mm}}^2")

    st.write("Armatuuri pinged (peale roomet)")
    if N == 0:
        st.latex(fr"\footnotesize σ_{{s1}} = \alpha_{{s}} \cdot \left( \frac{{N}}{{A_{{Red}}}} + \frac{{M \cdot (d_{{s1}} - x_{{Red}})}}{{{I_Red}}} \right) = {α_s_eff} \cdot \left( \frac{{{M} \cdot 10^6 \cdot ({d_s1} - {x_Red_eff})}}{{{I_Red_eff}}} \right) = {σ_s1_eff} \text{{ N/mm}}^2")
        st.latex(fr"\footnotesize σ_{{s2}} = \alpha_{{s}} \cdot \left( \frac{{N}}{{A_{{Red}}}} - \frac{{M \cdot (x_{{Red}} - d_{{s2}})}}{{{I_Red}}} \right) = {α_s_eff} \cdot \left( - \frac{{{M} \cdot 10^6 \cdot ({x_Red_eff} - {d_s2})}}{{{I_Red_eff}}} \right) = {σ_s2_eff} \text{{ N/mm}}^2")
    else:
        st.latex(fr"\footnotesize σ_{{s1}} = \alpha_{{s}} \cdot \left( \frac{{N}}{{A_{{Red}}}} + \frac{{M \cdot (d_{{s1}} - x_{{Red}})}}{{{I_Red}}} \right) = {α_s_eff} \cdot \left( \frac{{{N} \cdot 10^3}}{{{A_Red_eff}}} + \frac{{{M} \cdot 10^6 \cdot ({d_s1} - {x_Red_eff})}}{{{I_Red_eff}}} \right) = {σ_s1_eff} \text{{ N/mm}}^2")
        st.latex(fr"\footnotesize σ_{{s2}} = \alpha_{{s}} \cdot \left( \frac{{N}}{{A_{{Red}}}} - \frac{{M \cdot (x_{{Red}} - d_{{s2}})}}{{{I_Red}}} \right) = {α_s_eff} \cdot \left( \frac{{{N} \cdot 10^3}}{{{A_Red_eff}}} - \frac{{{M} \cdot 10^6 \cdot ({x_Red_eff} - {d_s2})}}{{{I_Red_eff}}} \right) = {σ_s2_eff} \text{{ N/mm}}^2")


    st.subheader("Peale pragu enne roomet")
    st.write("Pikijõudude tasakaalu tingimus")
    st.latex(fr"\footnotesize \frac{{σ_{{c0}} \cdot b \cdot x}}{{2}} + \frac{{α_{{s}} \cdot A_{{s2}} \cdot σ_{{c0}} \cdot (x - d_{{s2}})}}{{x}} - \frac{{α_{{s}} \cdot A_{{s1}} \cdot σ_{{c0}} \cdot (d_{{s1}} - x)}}{{x}} = N")
    st.latex(fr"\footnotesize \frac{{b \cdot x^2}}{{2}} + α_{{s}} \cdot A_{{s2}} \cdot (x - d_{{s2}}) - α_{{s}} \cdot A_{{s1}} \cdot (d_{{s1}} - x) = N \cdot \frac{{x}}{{σ_{{c0}}}}")
    st.write("Momentide tasakaalu tingimus")
    st.latex(fr"\footnotesize \frac{{b \cdot x \cdot σ_{{c0}}}}{{2}} \cdot \left( \frac{{2}}{{3}}x + d_{{s1}} - x \right) + α_{{s}} \cdot σ_{{c0}} \cdot A_{{s2}} \cdot \frac{{x - d_{{s2}}}}{{x}} \cdot (d_{{s1}} - d_{{s2}}) = N \cdot e_{{s1}}")
    st.write("milles saab avaldada")
    st.latex(fr"\footnotesize \frac{{b \cdot x^3}}{{3}} + \frac{{b \cdot x^2}}{{2}} \cdot (d_{{s1}} - x) + α_{{s}} \cdot A_{{s2}} \cdot (x - d_{{s2}}) \cdot (d_{{s1}} - d_{{s2}}) = N \cdot e_{{s1}} \cdot \frac{{x}}{{σ_{{c0}}}}")
    st.write("Pikijõudude ja momentide tasakaalu võrrandite kokkupanemisel saame kuupvõrrandi, millest saame leida survetsooni kõrguse")
    st.latex(fr"\footnotesize \frac{{b}}{{6}} \cdot x^3 + \frac{{b}}{{2}} \cdot (e_{{s1}} - d_{{s1}}) \cdot x^2 + α_{{s}} \cdot (A_{{s1}} \cdot e_{{s1}} + A_{{s2}} \cdot e_{{s2}}) \cdot x - α_{{s}} \cdot (A_{{s1}} \cdot d_{{s1}} \cdot e_{{s1}} + A_{{s2}} \cdot d_{{s2}} \cdot e_{{s2}}) = 0")
    if N != 0:    
        st.latex(fr"\footnotesize σ_{{c0}} = \frac{{N}}{{ \frac{{b \cdot x}}{{2}} - α_{{s}} \cdot A_{{s1}} \cdot \left( \frac{{d_{{s1}}}}{{x}} - 1 \right) + α_{{s}} \cdot A_{{s2}} \cdot \left( 1 - \frac{{d_{{s2}}}}{{x}} \right) }}")
        st.markdown(fr"$\footnotesize \text{{Mille lahend on }} x = {x_cr} \text{{ mm}}$")
        st.markdown(fr"$\footnotesize \text{{kus }} e_{{s1}} \text{{ on pikijõu eksentrilisus }} A_{{s1}} \text{{ suhtes}}$", unsafe_allow_html=True)
        st.markdown(fr"$\footnotesize e_{{s1}} = e_{{0}} + d_{{s1}} - \frac{{h}}{{2}} = \frac{{{M} \cdot 10^3}}{{{abs(N)}}} + {d_s1} - \frac{{{h}}}{{2}} = {e_s1} \text{{ mm}}$", unsafe_allow_html=True)
        st.markdown(fr"$\footnotesize \text{{kus }} e_{{s2}} = e_{{s1}} - d_{{s1}} + d_{{s2}} = {e_s1} - {d_s1} + {d_s2} = {e_s2} \text{{ mm}}$", unsafe_allow_html=True)


        st.write("Redutseeritud ristlõike pindala")
        st.latex(fr"\footnotesize A_{{cr,Red}} = b \cdot x + α_{{s}} \cdot A_{{s1}} + α_{{s}} \cdot A_{{s2}} = {b} \cdot {x_cr} + {α_s} \cdot {A_s1} + {α_s} \cdot {A_s2} = {A_cr_Red} \text{{ mm}}^2")
        st.latex(fr"\footnotesize y_{{cr,Red}} = \frac{{b \cdot x \cdot (d_{{s1}} - \frac{{x}}{{2}}) + α_{{s}} \cdot A_{{s2}} \cdot (d_{{s1}} - d_{{s2}})}}{{A_{{cr,Red}}}}")
        st.latex(fr"\footnotesize y_{{cr,Red}} = \frac{{{b} \cdot {x_cr} \cdot ({d_s1} - \frac{{{x_cr}}}{{2}}) + {α_s} \cdot {A_s2} \cdot ({d_s1} - {d_s2})}}{{{A_cr_Red}}} = {y_cr_Red} \text{{ mm}}")
        st.latex(fr"\footnotesize I_{{cr,Red}} = \frac{{b \cdot x^3}}{{12}} + b \cdot x \cdot (d_{{s1}} - \frac{{x}}{{2}} - y_{{cr,Red}})^2 + α_{{s}} \cdot A_{{s1}} \cdot y_{{cr,Red}}^2 + α_{{s}} \cdot A_{{s2}} \cdot (d_{{s1}} - d_{{s2}} - y_{{cr,Red}})^2")
        st.latex(fr"\footnotesize I_{{cr,Red}} = \frac{{{b} \cdot {x_cr}^3}}{{12}} + {b} \cdot {x_cr} \cdot ({d_s1} - \frac{{{x_cr}}}{{2}} - {y_cr_Red})^2 + {α_s} \cdot {A_s1} \cdot {y_cr_Red}^2 + {α_s} \cdot {A_s2} \cdot ({d_s1} - d_{{s2}} - {y_cr_Red})^2")
        st.latex(fr"\footnotesize I_{{cr,Red}} = {I_cr_Red} \text{{ mm}} ^4")

        st.write("Betooni pinged leitakse")
        st.latex(fr"\footnotesize σ_{{c}} = - \frac{{N}}{{A_{{cr,Red}}}} \pm \frac{{N \cdot e_{{0}} \cdot y_{{0}}}}{{I_{{cr,Red}}}} = - \frac{{{abs(N) * 1000}}}{{{A_cr_Red}}} \pm \frac{{{abs(N) * 1000} \cdot {e_0} \cdot {x_cr}}}{{{I_cr_Red}}} = {σ_cr_c} \text{{ MPa}}")
        st.write("Armatuuri pinged leitakse")
        st.latex(fr"\footnotesize σ_{{s1}} = α_{{s}} \cdot \left( - \frac{{N}}{{A_{{cr,Red}}}} + \frac{{N \cdot e_{{0}} \cdot y_{{s1}}}}{{I_{{cr,Red}}}} \right) = {α_s} \cdot \left( - \frac{{{abs(N)} \cdot 10^3}}{{{A_cr_Red}}} + \frac{{{abs(N)} \cdot 10^3 \cdot {e_0} \cdot ({d_s1} - {x_cr})}}{{{I_cr_Red}}} \right) = {σ_cr_s1} \text{{ MPa}}")
        st.latex(fr"\footnotesize σ_{{s2}} = α_{{s}} \cdot \left( - \frac{{N}}{{A_{{cr,Red}}}} - \frac{{N \cdot e_{{0}} \cdot y_{{s2}}}}{{I_{{cr,Red}}}} \right) = {α_s} \cdot \left( - \frac{{{abs(N)} \cdot 10^3}}{{{A_cr_Red}}} - \frac{{{abs(N)} \cdot 10^3 \cdot {e_0} \cdot ({x_cr} - {d_s2})}}{{{I_cr_Red}}} \right) = {σ_cr_s2} \text{{ MPa}}")

      

    else:
        st.latex(fr"\footnotesize σ_{{c0}} = \frac{{N}}{{ \frac{{b \cdot x}}{{2}} - α_{{s}} \cdot A_{{s1}} \cdot \left( \frac{{d_{{s1}}}}{{x}} - 1 \right) + α_{{s}} \cdot A_{{s2}} \cdot \left( 1 - \frac{{d_{{s2}}}}{{x}} \right) }}")
        st.latex(fr"\footnotesize A_{{cr,Red}} = b \cdot x + α_{{s}} \cdot A_{{s1}} + α_{{s}} \cdot A_{{s2}} = {b} \cdot {x_cr} + {α_s} \cdot {A_s1} + {α_s} \cdot {A_s2} = {A_cr_Red} \text{{ mm}}^2")
        st.latex(fr"\footnotesize y_{{cr,Red}} = \frac{{b \cdot x \cdot (d_{{s1}} - \frac{{x}}{{2}}) + α_{{s}} \cdot A_{{s2}} \cdot (d_{{s1}} - d_{{s2}})}}{{A_{{cr,Red}}}}")
        st.latex(fr"\footnotesize I_{{cr,Red}} = \frac{{b \cdot x^3}}{{12}} + b \cdot x \cdot (d_{{s1}} - \frac{{x}}{{2}} - y_{{cr,Red}})^2 + α_{{s}} \cdot A_{{s1}} \cdot y_{{cr,Red}}^2 + α_{{s}} \cdot A_{{s2}} \cdot (d_{{s1}} - d_{{s2}} - y_{{cr,Red}})^2")

        st.latex(fr"\footnotesize σ_{{c}} = - \frac{{N}}{{A_{{cr,Red}}}} \pm \frac{{N \cdot e_{{0}} \cdot y_{{0}}}}{{I_{{cr,Red}}}}")
        st.latex(fr"\footnotesize σ_{{s1}} = α_{{s}} \cdot \left( - \frac{{N}}{{A_{{cr,Red}}}} + \frac{{N \cdot e_{{0}} \cdot y_{{s1}}}}{{I_{{cr,Red}}}} \right)")
        st.latex(fr"\footnotesize σ_{{s2}} = α_{{s}} \cdot \left( - \frac{{N}}{{A_{{cr,Red}}}} - \frac{{N \cdot e_{{0}} \cdot y_{{s2}}}}{{I_{{cr,Red}}}} \right)")    
        st.write("Kuna N = 0, siis kuupvõrrand taandub ruutvõrrandiks ja ristlõike peatelg ühtib nulljoonega")
        st.latex(fr"\footnotesize x = - \frac{{α_{{s}}(A_{{s1}} + A_{{s2}})}}{{b}} + \sqrt{{ \left( \frac{{α_{{s}}(A_{{s1}} + A_{{s2}})}}{{b}} \right)^2 + \frac{{2α_{{s}}(A_{{s1}} \cdot d_{{s1}} + A_{{s2}} \cdot d_{{s2}})}}{{b}} }}")
        st.latex(fr"\footnotesize x = - \frac{{{α_s}({A_s1} + {A_s2})}}{{{b}}} + \sqrt{{ \left( \frac{{{α_s}({A_s1} + {A_s2})}}{{{b}}} \right)^2 + \frac{{2 \cdot {α_s}({A_s1} \cdot {d_s1} + {A_s2} \cdot {d_s2})}}{{{b}}} }} = {x_cr} \text{{ mm}}")

        st.write("Inertsimomendi saab leida")
        st.latex(fr"\footnotesize I_{{cr,red}} = \frac{{b \cdot x^3}}{{3}} + α_{{s}} \cdot A_{{s1}} \cdot (x - d_{{s1}})^2 + α_{{s}} \cdot A_{{s2}} \cdot (x - d_{{s2}})^2")
        st.latex(fr"\footnotesize I_{{cr,red}} = \frac{{{b} \cdot {x_cr}^3}}{{3}} + {α_s} \cdot {A_s1} \cdot ({x_cr} - {d_s1})^2 + {α_s} \cdot {A_s2} \cdot ({x_cr} - {d_s2})^2 = {I_cr_Red} \text{{ mm}}^4")

        st.write("Betooni suurim pinge leitakse")
        st.latex(fr"\footnotesize σ_{{c,max}} = - \frac{{M \cdot x}}{{I_{{cr,red}}}} = - \frac{{{M} \cdot 10^6 \cdot {x_cr}}}{{{I_cr_Red}}} = {σ_cr_c} \text{{ MPa}}")

        st.write("Armatuuri pinged leitakse")
        st.latex(fr"\footnotesize σ_{{s1}} = α_{{s}} \cdot \frac{{M \cdot (d_{{s1}} - x)}}{{I_{{cr,red}}}} = {α_s} \cdot \frac{{{M} \cdot 10^6 \cdot ({d_s1} - {x_cr})}}{{{I_cr_Red}}} = {σ_cr_s1} \text{{ MPa}}")
        st.latex(fr"\footnotesize σ_{{s2}} = α_{{s}} \cdot \frac{{M \cdot (d_{{s2}} - x)}}{{I_{{cr,red}}}} = {α_s} \cdot \frac{{{M} \cdot 10^6 \cdot ({d_s2} - {x_cr})}}{{{I_cr_Red}}} = {σ_cr_s2} \text{{ MPa}}")


    st.subheader("Peale pragu peale roomet")


    st.write("Roome arenedes tuleb leida uus betooni elastsusmoodul")
    if st.session_state.loplik_ajal_t_roome:
        st.latex(fr"\footnotesize E_{{c,eff}} = \frac{{1.05 \cdot E_{{cm}}}}{{1 + φ(t,t_{{0}})}} = \frac{{1.05 \cdot {E_cm}}}{{1 + {φ_0}}} = {E_c_eff}")    
    else:
       st.latex(fr"\footnotesize E_{{c,eff}} = \frac{{1.05 \cdot E_{{cm}}}}{{1 + φ(t,t_{{0}})}} = \frac{{1.05 \cdot {E_cm}}}{{1 + {φ_t_t_0}}} = {E_c_eff}")     
    st.latex(fr"\footnotesize α_{{s}} = \frac{{E_{{s}}}}{{E_{{c,eff}}}} = \frac{{{E_s}}}{{{E_c_eff}}} = {α_s_eff}")
    
    st.toggle("Arvuta pinged ajahetkel t / peale lõplikku roomet", value=st.session_state.loplik_ajal_t_roome, key="roome_nupp_all", on_change=lambda: st.session_state.update({"loplik_ajal_t_roome": st.session_state.roome_nupp_all, "roome_nupp_yleval": st.session_state.roome_nupp_all}))

    st.write("Pikijõudude tasakaalu termin")
    st.latex(fr"\footnotesize \frac{{σ_{{c0}} \cdot b \cdot x}}{{2}} + \frac{{α_{{s}} \cdot A_{{s2}} \cdot σ_{{c0}} \cdot (x - d_{{s2}})}}{{x}} - \frac{{α_{{s}} \cdot A_{{s1}} \cdot σ_{{c0}} \cdot (d_{{s1}} - x)}}{{x}} = N")
    st.latex(fr"\footnotesize \frac{{b \cdot x^2}}{{2}} + α_{{s}} \cdot A_{{s2}} \cdot (x - d_{{s2}}) - α_{{s}} \cdot A_{{s1}} \cdot (d_{{s1}} - x) = N \cdot \frac{{x}}{{σ_{{c0}}}}")
    st.write("Momentide tasakaalu tingimus")
    st.latex(fr"\footnotesize \frac{{b \cdot x \cdot σ_{{c0}}}}{{2}} \cdot \left( \frac{{2}}{{3}}x + d_{{s1}} - x \right) + α_{{s}} \cdot σ_{{c0}} \cdot A_{{s2}} \cdot \frac{{x - d_{{s2}}}}{{x}} \cdot (d_{{s1}} - d_{{s2}}) = N \cdot e_{{s1}}")
    st.write("milles saab avaldada")
    st.latex(fr"\footnotesize \frac{{b \cdot x^3}}{{3}} + \frac{{b \cdot x^2}}{{2}} \cdot (d_{{s1}} - x) + α_{{s}} \cdot A_{{s2}} \cdot (x - d_{{s2}}) \cdot (d_{{s1}} - d_{{s2}}) = N \cdot e_{{s1}} \cdot \frac{{x}}{{σ_{{c0}}}}")
    st.write("Pikijõudude ja momentide tasakaalu võrrandite kokkupanemisel saame kuupvõrrandi, millest saame leida survetsooni kõrguse")
    st.latex(fr"\footnotesize \frac{{b}}{{6}} \cdot x^3 + \frac{{b}}{{2}} \cdot (e_{{s1}} - d_{{s1}}) \cdot x^2 + α_{{s}} \cdot (A_{{s1}} \cdot e_{{s1}} + A_{{s2}} \cdot e_{{s2}}) \cdot x - α_{{s}} \cdot (A_{{s1}} \cdot d_{{s1}} \cdot e_{{s1}} + A_{{s2}} \cdot d_{{s2}} \cdot e_{{s2}}) = 0")

    if N != 0:    
        st.latex(fr"\footnotesize σ_{{c0}} = \frac{{N}}{{ \frac{{b \cdot x}}{{2}} - α_{{s}} \cdot A_{{s1}} \cdot \left( \frac{{d_{{s1}}}}{{x}} - 1 \right) + α_{{s}} \cdot A_{{s2}} \cdot \left( 1 - \frac{{d_{{s2}}}}{{x}} \right) }}")
        st.markdown(fr"$\footnotesize \text{{Mille lahend on }} x = {x_cr_eff} \text{{ mm}}$")
        st.markdown(fr"$\footnotesize \text{{kus }} e_{{s1}} \text{{ on pikijõu eksentrilisus }} A_{{s1}} \text{{ suhtes}}$", unsafe_allow_html=True)
        st.markdown(fr"$\footnotesize e_{{s1}} = e_{{0}} + d_{{s1}} - \frac{{h}}{{2}} = \frac{{{M} \cdot 10^3}}{{{abs(N)}}} + {d_s1} - \frac{{{h}}}{{2}} = {e_s1} \text{{ mm}}$", unsafe_allow_html=True)
        st.markdown(fr"$\footnotesize \text{{kus }} e_{{s2}} = e_{{s1}} - d_{{s1}} + d_{{s2}} = {e_s1} - {d_s1} + {d_s2} = {e_s2} \text{{ mm}}$", unsafe_allow_html=True)

        st.write("Redutseeritud ristlõike pindala")
        st.latex(fr"\footnotesize A_{{cr,Red}} = b \cdot x + α_{{s}} \cdot A_{{s1}} + α_{{s}} \cdot A_{{s2}} = {b} \cdot {x_cr_eff} + {α_s_eff} \cdot {A_s1} + {α_s_eff} \cdot {A_s2} = {A_cr_Red_eff} \text{{ mm}}^2")
        st.latex(fr"\footnotesize y_{{cr,Red}} = \frac{{b \cdot x \cdot (d_{{s1}} - \frac{{x}}{{2}}) + α_{{s}} \cdot A_{{s2}} \cdot (d_{{s1}} - d_{{s2}})}}{{A_{{cr,Red}}}}")
        st.latex(fr"\footnotesize y_{{cr,Red}} = \frac{{{b} \cdot {x_cr_eff} \cdot ({d_s1} - \frac{{{x_cr_eff}}}{{2}}) + {α_s_eff} \cdot {A_s2} \cdot ({d_s1} - {d_s2})}}{{{A_cr_Red_eff}}} = {y_cr_Red_eff} \text{{ mm}}")
        st.latex(fr"\footnotesize I_{{cr,Red}} = \frac{{b \cdot x^3}}{{12}} + b \cdot x \cdot (d_{{s1}} - \frac{{x}}{{2}} - y_{{cr,Red}})^2 + α_{{s}} \cdot A_{{s1}} \cdot y_{{cr,Red}}^2 + α_{{s}} \cdot A_{{s2}} \cdot (d_{{s1}} - d_{{s2}} - y_{{cr,Red}})^2")
        st.latex(fr"\footnotesize I_{{cr,Red}} = \frac{{{b} \cdot {x_cr_eff}^3}}{{12}} + {b} \cdot {x_cr_eff} \cdot ({d_s1} - \frac{{{x_cr_eff}}}{{2}} - {y_cr_Red_eff})^2 + {α_s_eff} \cdot {A_s1} \cdot {y_cr_Red_eff}^2 + {α_s_eff} \cdot {A_s2} \cdot ({d_s1} - d_{{s2}} - {y_cr_Red_eff})^2")
        st.latex(fr"\footnotesize I_{{cr,Red}} = {I_cr_Red_eff} \text{{ mm}} ^4")

        st.write("Betooni pinged leitakse")
        st.latex(fr"\footnotesize σ_{{c}} = - \frac{{N}}{{A_{{cr,Red}}}} \pm \frac{{N \cdot e_{{0}} \cdot y_{{0}}}}{{I_{{cr,Red}}}} = - \frac{{{abs(N) * 1000}}}{{{A_cr_Red_eff}}} \pm \frac{{{abs(N) * 1000} \cdot {e_0} \cdot {x_cr_eff}}}{{{I_cr_Red_eff}}} = {σ_cr_c_eff} \text{{ MPa}}")
        st.write("Armatuuri pinged leitakse")
        st.latex(fr"\footnotesize σ_{{s1}} = α_{{s}} \cdot \left( - \frac{{N}}{{A_{{cr,Red}}}} + \frac{{N \cdot e_{{0}} \cdot y_{{s1}}}}{{I_{{cr,Red}}}} \right) = {α_s_eff} \cdot \left( - \frac{{{abs(N)} \cdot 10^3}}{{{A_cr_Red_eff}}} + \frac{{{abs(N)} \cdot 10^3 \cdot {e_0} \cdot ({d_s1} - {x_cr_eff})}}{{{I_cr_Red_eff}}} \right) = {σ_cr_s1_eff} \text{{ MPa}}")
        st.latex(fr"\footnotesize σ_{{s2}} = α_{{s}} \cdot \left( - \frac{{N}}{{A_{{cr,Red}}}} - \frac{{N \cdot e_{{0}} \cdot y_{{s2}}}}{{I_{{cr,Red}}}} \right) = {α_s_eff} \cdot \left( - \frac{{{abs(N)} \cdot 10^3}}{{{A_cr_Red_eff}}} - \frac{{{abs(N)} \cdot 10^3 \cdot {e_0} \cdot ({x_cr_eff} - {d_s2})}}{{{I_cr_Red_eff}}} \right) = {σ_cr_s2_eff} \text{{ MPa}}")

    else:
        st.latex(fr"\footnotesize σ_{{c0}} = \frac{{N}}{{ \frac{{b \cdot x}}{{2}} - α_{{s}} \cdot A_{{s1}} \cdot \left( \frac{{d_{{s1}}}}{{x}} - 1 \right) + α_{{s}} \cdot A_{{s2}} \cdot \left( 1 - \frac{{d_{{s2}}}}{{x}} \right) }}")
        st.latex(fr"\footnotesize A_{{cr,Red}} = b \cdot x + α_{{s}} \cdot A_{{s1}} + α_{{s}} \cdot A_{{s2}} = {b} \cdot {x_cr_eff} + {α_s_eff} \cdot {A_s1} + {α_s_eff} \cdot {A_s2} = {A_cr_Red_eff} \text{{ mm}}^2")
        st.latex(fr"\footnotesize y_{{cr,Red}} = \frac{{b \cdot x \cdot (d_{{s1}} - \frac{{x}}{{2}}) + α_{{s}} \cdot A_{{s2}} \cdot (d_{{s1}} - d_{{s2}})}}{{A_{{cr,Red}}}}")
        st.latex(fr"\footnotesize I_{{cr,Red}} = \frac{{b \cdot x^3}}{{12}} + b \cdot x \cdot (d_{{s1}} - \frac{{x}}{{2}} - y_{{cr,Red}})^2 + α_{{s}} \cdot A_{{s1}} \cdot y_{{cr,Red}}^2 + α_{{s}} \cdot A_{{s2}} \cdot (d_{{s1}} - d_{{s2}} - y_{{cr,Red}})^2")

        st.latex(fr"\footnotesize σ_{{c}} = - \frac{{N}}{{A_{{cr,Red}}}} \pm \frac{{N \cdot e_{{0}} \cdot y_{{0}}}}{{I_{{cr,Red}}}}")
        st.latex(fr"\footnotesize σ_{{s1}} = α_{{s}} \cdot \left( - \frac{{N}}{{A_{{cr,Red}}}} + \frac{{N \cdot e_{{0}} \cdot y_{{s1}}}}{{I_{{cr,Red}}}} \right)")
        st.latex(fr"\footnotesize σ_{{s2}} = α_{{s}} \cdot \left( - \frac{{N}}{{A_{{cr,Red}}}} - \frac{{N \cdot e_{{0}} \cdot y_{{s2}}}}{{I_{{cr,Red}}}} \right)")    
        st.write("Kuna N = 0, siis kuupvõrrand taandub ruutvõrrandiks ja ristlõike peatelg ühtib nulljoonega")
        st.latex(fr"\footnotesize x = - \frac{{α_{{s}}(A_{{s1}} + A_{{s2}})}}{{b}} + \sqrt{{ \left( \frac{{α_{{s}}(A_{{s1}} + A_{{s2}})}}{{b}} \right)^2 + \frac{{2α_{{s}}(A_{{s1}} \cdot d_{{s1}} + A_{{s2}} \cdot d_{{s2}})}}{{b}} }}")
        st.latex(fr"\footnotesize x = - \frac{{{α_s_eff}({A_s1} + {A_s2})}}{{{b}}} + \sqrt{{ \left( \frac{{{α_s_eff}({A_s1} + {A_s2})}}{{{b}}} \right)^2 + \frac{{2 \cdot {α_s_eff}({A_s1} \cdot {d_s1} + {A_s2} \cdot {d_s2})}}{{{b}}} }} = {x_cr_eff} \text{{ mm}}")

        st.write("Inertsimomendi saab leida")
        st.latex(fr"\footnotesize I_{{cr,red}} = \frac{{b \cdot x^3}}{{3}} + α_{{s}} \cdot A_{{s1}} \cdot (x - d_{{s1}})^2 + α_{{s}} \cdot A_{{s2}} \cdot (x - d_{{s2}})^2")
        st.latex(fr"\footnotesize I_{{cr,red}} = \frac{{{b} \cdot {x_cr_eff}^3}}{{3}} + {α_s_eff} \cdot {A_s1} \cdot ({x_cr_eff} - {d_s1})^2 + {α_s_eff} \cdot {A_s2} \cdot ({x_cr_eff} - {d_s2})^2 = {I_cr_Red_eff} \text{{ mm}}^4")

        st.write("Betooni suurim pinge leitakse")
        st.latex(fr"\footnotesize σ_{{c,max}} = - \frac{{M \cdot x}}{{I_{{cr,red}}}} = - \frac{{{M} \cdot 10^6 \cdot {x_cr_eff}}}{{{I_cr_Red_eff}}} = {σ_cr_c_eff} \text{{ MPa}}")

        st.write("Armatuuri pinged leitakse")
        st.latex(fr"\footnotesize σ_{{s1}} = α_{{s}} \cdot \frac{{M \cdot (d_{{s1}} - x)}}{{I_{{cr,red}}}} = {α_s_eff} \cdot \frac{{{M} \cdot 10^6 \cdot ({d_s1} - {x_cr_eff})}}{{{I_cr_Red_eff}}} = {σ_cr_s1_eff} \text{{ MPa}}")
        st.latex(fr"\footnotesize σ_{{s2}} = α_{{s}} \cdot \frac{{M \cdot (d_{{s2}} - x)}}{{I_{{cr,red}}}} = {α_s_eff} \cdot \frac{{{M} \cdot 10^6 \cdot ({d_s2} - {x_cr_eff})}}{{{I_cr_Red_eff}}} = {σ_cr_s2_eff} \text{{ MPa}}")





    # 1. Kogume Sinu arvutatud muutujad ridade kaupa kokku
    rida_σ_c = [σ_c, σ_c_eff, σ_cr_c, σ_cr_c_eff]
    rida_σ_t = [σ_ct, σ_ct_eff, "-", "-"]
    rida_σ_s1 = [σ_s1, σ_s1_eff, σ_cr_s1, σ_cr_s1_eff]

    # 2. Survearmatuuri kontroll: kui A_s2 on 0, kuvatakse terve rida tekstina
    if A_s2 == 0:
        rida_σ_s2 = ["Survearmatuur puudub", "Survearmatuur puudub", "Survearmatuur puudub", "Survearmatuur puudub"]
    else:
        rida_σ_s2 = [σ_s2, σ_s2_eff, σ_cr_s2, σ_cr_s2_eff]

    # 3. Uus rida pragunemismomendi jaoks
    rida_M_cr = [M_cr, M_cr_eff, "-", "-"]

    tabeli_maatriks = [rida_σ_c, rida_σ_t, rida_σ_s1, rida_σ_s2, rida_M_cr]

    # 4. Muutujate nimed HTML alaindeksitega (lisatud M_cr)
    rea_nimed = ["σ<sub>c</sub>", "σ<sub>t</sub>", "σ<sub>s1</sub>", "σ<sub>s2</sub>", "M<sub>cr</sub>"]

    # 5. Päise ja struktuuri vormistamine ilma index.name lisareata
    veergude_nimed = pd.MultiIndex.from_tuples([
        ("Pragunemata", "Enne roomet"),
        ("Pragunemata", "Pärast roomet"),
        ("Pragunenud", "Enne roomet"),
        ("Pragunenud", "Pärast roomet")
    ])

    df = pd.DataFrame(tabeli_maatriks, index=rea_nimed, columns=veergude_nimed)

    # 6. Teisendame HTML-iks ja tõstame ühiku [Mpa] otse nurgalahtrisse
    html_tabel = df.to_html(escape=False, justify='center')
    html_tabel = html_tabel.replace('<th></th>', '<th style="text-align: center;">[Mpa]</th>', 1)

    # 7. Kuvamine Streamlitis
    st.subheader("Betooni ja armatuuri pingete koondtabel")
    st.write(html_tabel, unsafe_allow_html=True)









def labipainde_funktsioon():
    st.title("Läbipaine")
    st.write("Sinu peatüki 3 kood...")

def pragudekindlus_funktsioon():
    st.title("Pragudekindlus")
    st.write("Sinu peatüki 4 kood...")

def peatukk5_funktsioon():
    st.title("Peatükk 5")
    st.write("Sinu peatüki 5 kood...")

def peatukk6_funktsioon():
    st.title("Peatükk 6")
    st.write("Sinu peatüki 6 kood...")

def peatukk7_funktsioon():
    st.title("Peatükk 7")
    st.write("Sinu peatüki 7 kood...")

def peatukk8_funktsioon():
    st.title("Peatükk 8")
    st.write("Sinu peatüki 8 kood...")

def peatukk9_funktsioon():
    st.title("Peatükk 9")
    st.write("Sinu peatüki 9 kood...")

def peatukk10_funktsioon():
    st.title("Peatükk 10")
    st.write("Sinu peatüki 10 kood...")


# =====================================================================
# 3. LEHED JA VAIKIMISI MENÜÜ PEITMINE
# =====================================================================
leht_1 = st.Page(kandevoime_funktsioon, title="Kandevõime")
leht_2 = st.Page(roometegur_funktsioon, title="Roometegur")
leht_3 = st.Page(pingete_funktsioon, title="Betooni ja armatuuri pinged")
leht_4 = st.Page(labipainde_funktsioon, title="Läbipaine")
leht_5 = st.Page(pragudekindlus_funktsioon, title="Pragudekindlus")
leht_6 = st.Page(peatukk5_funktsioon, title="Peatükk 5")
leht_7 = st.Page(peatukk6_funktsioon, title="Peatükk 6")
leht_8 = st.Page(peatukk7_funktsioon, title="Peatükk 7")
leht_9 = st.Page(peatukk8_funktsioon, title="Peatükk 8")
leht_10 = st.Page(peatukk9_funktsioon, title="Peatükk 9")
leht_11 = st.Page(peatukk10_funktsioon, title="Peatükk 10")

# Asukoht "hidden" kaotab ära Streamliti enda menüüriba vasakult
pg = st.navigation([leht_1, leht_2, leht_3, leht_4, leht_5, leht_6, leht_7, leht_8, leht_9, leht_10, leht_11], position="hidden")


# =====================================================================
# 4. KOHANDATUD CSS LIIKUMISEKS JA LINKIDE STIILIMISEKS
# =====================================================================
st.markdown("""
    <style>
        /* =====================================================================
           1. PEAMISE SISUPLOKI (KESKOSA) PAIGUTUS SUUREL EKRAANIL
           ===================================================================== */
        @media (min-width: 993px) {
            [data-testid="stMainBlockContainer"] {
                /* LAIUS: Määrab, kui palju ruumi keskmine tekst/valemid ekraanist võtavad. 
                   Suurenda (nt 75%), kui tekst on liiga kitsas, või vähenda, kui see sõidab sisukorrale peale. */
                max-width: 80% !important;
                
                /* VASAK VEERIS: Surub keskmise kasti otse vasaku menüüriba (Sidebar) külge.
                   Kui tahad sisu ja vasaku menüü vahele rohkem tühjust, suurenda seda (nt 4rem). */
                margin-left: 2rem !important;
                
                /* PAREM VEERIS: Vaikimisi automaatne, et jätta paremale poole vaba ruumi sisukorra jaoks. */
                margin-right: auto !important;
            }
        }

        /* =====================================================================
           2. SISUKORRA KASTI ÜLDISE KESTA (KONTEINERI) DISAIN JA ASUKOHT
           ===================================================================== */
        div[data-testid="stVerticalBlockBorderWrapper"]:has(div[data-keys="parem_sisukord"]),
        div[data-testid="element-container"]:has(div[data-keys="parem_sisukord"]),
        .st-key-parem_sisukord {
            /* POSITSIOON: "fixed" tähendab, et kast püsib kerimisel alati ekraanil samas kohas. */
            position: fixed !important;
            
            /* KAUGUS PAREMAST ÄÄREST: Kui soovid kasti ekraani servale lähemale, vähenda (nt 1rem). 
               Kui tahad seda rohkem vasakule (keskme poole) tuua, suurenda. */
            right: 2rem !important;
            
            /* KAUGUS ÜLEMISEST ÄÄREST: Kui tahad kasti ekraanil kõrgemale nihutada, vähenda (nt 2rem). 
               Kui see jääb ette Streamliti ülamenüüle, suurenda (nt 6rem). */
            top: 5rem !important;
            
            /* KASTI LAIUS: Määrab sisukorra kasti laiuse pikslites. 
               Kui sul on pikad peatükkide nimed, mis ei mahu ära, suurenda seda (nt 300px). */
            width: 250px !important;
            
            /* TAUSTAVÄRV: Praegu helehall (#f9f9f9). Võid muuta nt valgeks (#ffffff) 
               või kasutada hex-koode lehelt htmlcolorcodes.com */
            background-color: #f9f9f9 !important; 
            
            /* SISEMINE POLSTERDUS: Ruumi suurus kasti piirjoone ja teksti vahel. 
               Suurendamine teeb kasti õhulisemaks, vähendamine kompaktsemaks. */
            padding: 1.2rem !important;
            
            /* NURKADE ÜMARUS: Mida suurem number, seda ümaramad on kasti nurgad (0px on täiesti kandiline). */
            border-radius: 8px !important;
            
            /* KASTI PIIRJOON: Paksus (1px), stiil (solid ehk pidev joon) ja värv (hele hall #e6e6e6). */
            border: 1px solid #e6e6e6 !important;
            
            /* KIHTIDE JÄRJEKORD: Tagab, et sisukord jääb alati lehe teksti peale ega kattu valemitega. */
            z-index: 999999 !important;
            
            /* MAKSIMAALNE KÕRGUS: Kast võtab maksimaalselt 80% brauseri akna kõrgusest. 
               See hoiab ära kasti venimise üle ekraani ääre, kui peatükke on väga palju. */
            max-height: 80vh !important; 
            
            /* KERIMISRIBA: Kui peatükke on rohkem kui max-height lubab, tekib kasti sisse automaatselt kerimisriba. */
            overflow-y: auto !important;
            
            /* KASTI VARI: Annab kastile õrna 3D efekti (varju). 
               Viimane number (0.08) määrab varju tumeduse/tugevuse (suurem number = tumedam vari). */
            box-shadow: 0px 4px 12px rgba(0, 0, 0, 0.08) !important;
        }
        
        /* =====================================================================
           3. LINGIÜMBRUSTE PUHASTAMINE STREAMLITI VAIKIMISI NUPUSTIILIDEST
           ===================================================================== */
        .st-key-parem_sisukord div[data-testid="stPageLink-Inline"] {
            /* Eemaldab nuputausta, et link ei näeks välja nagu hall vajutatav klots. */
            background-color: transparent !important;
            /* Eemaldab nupu ümber oleva vaike-raami. */
            border: none !important;
            /* Kaotab nupu sees oleva kohustusliku tühimiku. */
            padding: 0 !important;
            /* VAHEMAA LINKIDE VAHEL: Määrab, kui palju ruumi on kahe lingi vahel vertikaalselt. 
               Kui tahad peatükke tihedamalt, vähenda (nt 0.1rem). */
            margin-bottom: 0.2rem !important;
            display: block !important;
        }

        /* =====================================================================
           4. LINGI TEKSTI JA VÄLIMUSE STIILIMINE (TAVALINE OLEK)
           ===================================================================== */
        .st-key-parem_sisukord div[data-testid="stPageLink-Inline"] a {
            /* Eemaldab tekstilt vaikimisi allajoonimise. (allajoonitud tekst tekiks "underline" korral). */
            text-decoration: none !important;
            
            /* TEKSTI VÄRV: Praegu peaaegu must tüüpiline tekstivärv (#333333). 
               Võid muuta näiteks siniseks (#0066cc) või halliks (#666666). */
            color: #333333 !important; 
            
            /* TEKSTI SUURUS: Muuda seda, kui soovid sisukorra kirja suuremaks või väiksemaks (nt 0.85rem või 1.1rem). */
            font-size: 0.95rem !important;
            
            /* LINGI KLIKITAV ALA: Esimene number (6px) on ruum teksti peal/all, teine (10px) teksti külgedel. 
               See muudab terve rea klikitavaks nupuks, mitte ainult tähed. */
            padding: 6px 10px !important;
            display: block !important;
            
            /* Lingi klikitava ala nurkade ümarus, kui hiirega peale minna. */
            border-radius: 4px !important;
            
            /* ANIMATSIOONI KIIRUS: Kui suunad hiire lingile, siis taustavärv vahetub sujuvalt 0.15 sekundi jooksul. */
            transition: background-color 0.15s ease;
        }
        
        /* =====================================================================
           5. LINGI STIIL KUI HIIREGA PEALE MINNA (HOVER OLEK)
           ===================================================================== */
        .st-key-parem_sisukord div[data-testid="stPageLink-Inline"] a:hover {
            /* LINGI TAUST HIIREGA PEAL OLLES: Muutub õrnalt hallikaks (#f0f2f6). 
               Võid panna mis tahes värvi, et oleks selge, millisele lingile hiir suunatud on. */
            background-color: #f0f2f6 !important;
            
            /* TEKSTI VÄRV HIIREGA PEAL OLLES: Muutub punaseks (#ff4b4b). 
               Kui soovid näiteks klassikalist sinist, asenda see koodiga #0066cc. */
            color: #ff4b4b !important;
        }

        /* =====================================================================
           6. MOBIILI JA VÄIKESTE EKRAANIDE KOHANDUS (Mobiilis ei tohi kast paigal püsida)
           ===================================================================== */
        @media (max-width: 992px) {
            [data-testid="stMainBlockContainer"] {
                /* Mobiilis võtab keskmine sisu 100% ekraani laiusest. */
                max-width: 100% !important;
                /* Tsentreerib sisu mobiiliekraani keskele. */
                margin-left: auto !important;
            }
            .st-key-parem_sisukord {
                /* Kaotab ekraanile kleepumise ("static"), et sisukord käituks tavalise tekstiplokina. */
                position: static !important;
                /* Sisukorra kast venib mobiilis üle terve ekraani laiuse. */
                width: 100% !important;
                /* Eemaldab kõrguse piirangu, et kõik peatükid oleksid korraga näha ilma kasti sees kerimata. */
                max-height: none !important;
                /* Eemaldab varju, et sulanduks puhtalt ülejäänud mobiilivaate disainiga. */
                box-shadow: none !important;
                /* Jätab sisukorra kasti alla tühja ruumi enne, kui peatüki sisu pihta hakkab. */
                margin-bottom: 2rem !important;
            }
        }
    </style>
""", unsafe_allow_html=True)

# =====================================================================
# 6. SISUKORD PAREMAL ÄÄREL (Konteinerisse pakitud stabiilsuse jaoks)
# =====================================================================
with st.container(key="parem_sisukord"):
    st.subheader("📖 Sisukord")
    st.page_link(leht_1, label="Kandevõime")
    st.page_link(leht_2, label="Roometegur")
    st.page_link(leht_3, label="Betooni ja armatuuri pinged")
    st.page_link(leht_4, label="Läbipaine")
    st.page_link(leht_5, label="Pragudekindlus")
    st.page_link(leht_6, label="Peatükk 5")
    st.page_link(leht_7, label="Peatükk 6")
    st.page_link(leht_8, label="Peatükk 7")
    st.page_link(leht_9, label="Peatükk 8")
    st.page_link(leht_10, label="Peatükk 9")
    st.page_link(leht_11, label="Peatükk 10")


# =====================================================================
# 7. AKTIIVSE LEHE SISU KÄIVITAMINE
# =====================================================================
pg.run()
