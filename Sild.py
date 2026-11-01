import math
import streamlit as st
import numpy as np

st.set_page_config(layout="wide")

st.title("Teraskonstruktsiooni projekt")

# --- KOOSTAVAD KONSTANTID (Mitte-muudetavad) ---
g_plekk_kg = 10.0
g_roov_kg = 10.0
g_fassaad_kg = 20.0

mu = 0.80
gamma_M0 = 1.00
gamma_M1 = 1.00
gamma_M2 = 1.25

E = 210000.0  # N/mm²
eta = 1.2
L = 16.0      # Ava pikkus meetrites
rho = 7850.0  # Terase tihedus kg/m³

# --- MUDELI KOORMUSED JA MÕÕTMED (Sinu arvutusmudeli järgi) ---
F = 211.5       # Koondkoormus (kN)
q_pusi = 21.19  # Ühtlaselt jaotatud püsikoormus (kN/m)
a = 7.4         # Kaugus tugedest koondkoormusteni (meetrites)

# =====================================================================
# Külgriba lähteandmed
# =====================================================================

with st.sidebar:
    st.header("Lähteandmed")

    st.subheader("Terase omadused")
    steel_grade = st.selectbox("Vali terase mark:", ["S235", "S275", "S355"], index=0)
    survetugevused = {"S235": 235.0, "S275": 275.0, "S355": 355.0}
    f_y = survetugevused[steel_grade]
    epsilon = round((235 / f_y) ** 0.5, 3)

    st.markdown(f"##### $f_y$ = {f_y:.0f} MPa")
    st.markdown(f"##### $\\varepsilon$ = {epsilon:.3f}")

    st.subheader("Ristlõike mõõtmed")
    h = st.number_input("Kõrgus h (mm):", min_value=10.0, max_value=2000.0, value=295.0, step=5.0)
    tw = st.number_input("Seina paksus tw (mm):", min_value=1.0, max_value=100.0, value=5.0, step=0.5)
    b_prof = st.number_input("Vöö laius b (mm):", min_value=10.0, max_value=2000.0, value=300.0, step=5.0)
    tf = st.number_input("Vöö paksus tf (mm):", min_value=1.0, max_value=100.0, value=10.0, step=0.5)
    r_val = 0

# =====================================================================
# Arvutused ja kuvamine
# =====================================================================

# Avame kogu lehte hõlmava footnotesize konteineri
st.markdown('<div style="font-size: 0.85rem; line-height: 1.5;">', unsafe_allow_html=True)

# Abimuutujad geomeetria jaoks
c_sein_karakt = h - 2 * tf - 2 * r_val
A_f = b_prof * tf
z_f = (h - tf) / 2

# --- 1. TAUSTAL TOIMUV OK JA MUDELIKOHASE MOMENDI ARVUTUS TALA KESKEL ---
# Ristlõike kogupindala A (mm²)
A_kogu = 2 * A_f + (tw * c_sein_karakt)
# Jooksva meetri mass p (kg/m), teisendades mm² -> m² (jagades 10^6)
p_ok_kg = (A_kogu / 10**6) * rho
# Joonkoormus kN/m (g_ok = p * 10 / 1000 = p * 0.01)
g_ok_kn = p_ok_kg * 0.01

# Summaarne jaotatud koormus mudelis (püsikoormus + profiili OK)
q_kogu = q_pusi + g_ok_kn

# Paindemoment tala täpses keskkohas (x = 8.0 m)
M_koond = F * a
M_jaotatud = (q_kogu * (L ** 2)) / 8
M_Ed = M_koond + M_jaotatud

st.write("Leian terasprofiili OK ja maksimaalse paindemomendi tala keskkohas ($x = 8.0\\text{ m}$):")
st.latex(rf"A = 2 \cdot ({b_prof:.1f} \cdot {tf:.1f}) + ({tw:.1f} \cdot {c_sein_karakt:.1f}) = {A_kogu:,.1f}\text{{ mm}}^2")
st.latex(rf"g_{{OK}} = A \cdot \rho = {A_kogu:,.1f}\text{{ mm}}^2 \cdot {rho:.0f}\text{{ kg/m}}^3 \cdot 10^{{-6}} = {p_ok_kg:.4f}\text{{ kg/m}} \rightarrow {g_ok_kn:.4f}\text{{ kN/m}}")
st.latex(rf"M_{{Ed}} = {M_Ed:.2f}\text{{ kNm}}")


# --- 9. DÜNAAMILINE SKEEM, PAINDEMOMENDI JA PÕIKJÕU DIAGRAMMID ---
st.markdown("<b style='font-size: 1rem;'>Arvutusskeem, paindemomendi ja põikjõu diagrammid</b>", unsafe_allow_html=True)

import matplotlib.pyplot as plt
import matplotlib.patches as patches

# Genereerime x-telje punktid piki tala (0 kuni 16 meetrit, sammuga 0.1m)
x_telg = np.arange(0, L + 0.1, 0.1)
y_moment = []
y_poikjoud = []

# Arvutame toereaktsioonid (sümmeetriline mudel)
R_A = F + (q_kogu * L) / 2

for x_koord in x_telg:
    # Paindemomendi arvutus
    M_punktis = R_A * x_koord - (q_kogu * (x_koord ** 2)) / 2
    if x_koord > a:
        M_punktis -= F * (x_koord - a)
    if x_koord > (L - a):
        M_punktis -= F * (x_koord - (L - a))
    y_moment.append(M_punktis)
    
    # Põikjõu arvutus
    V_punktis = R_A - q_kogu * x_koord
    if x_koord > a:
        V_punktis -= F
    if x_koord > (L - a):
        V_punktis -= F
    y_poikjoud.append(V_punktis)

# Luuakse kolm joonist üksteise alla, mis jagavad x-telge
fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(10, 8.5), sharex=True, 
                                    gridspec_kw={'height_ratios': [1, 1.2, 1.2]})

# =====================================================================
# ÜLEMINE JOONIS: TALA JA KOORMUSTE SKEEM
# =====================================================================
ax1.plot([0, L], [0, 0], color='blue', linewidth=4, zorder=3)

# Toed
ax1.plot([0, -0.3, 0.3, 0], [0, -0.4, -0.4, 0], color='black', linewidth=1.5)
ax1.plot([L, L-0.3, L+0.3, L], [0, -0.4, -0.4, 0], color='black', linewidth=1.5)
ax1.plot([L-0.3, L+0.3], [-0.47, -0.47], color='black', linewidth=1.5)

# Ühtlaselt jaotatud koormus
q_kõrgus = 0.5
rect = patches.Rectangle((0, 0), L, q_kõrgus, linewidth=1, edgecolor='green', facecolor='green', alpha=0.15)
ax1.add_patch(rect)
ax1.plot([0, L], [q_kõrgus, q_kõrgus], color='green', linewidth=1)
for x_q in np.linspace(0, L, 17):
    ax1.annotate('', xy=(x_q, 0), xytext=(x_q, q_kõrgus), arrowprops=dict(arrowstyle="->", color='green', lw=0.8))

# Jaotatud koormuse tekst vasakus ääres
ax1.text(0.5, q_kõrgus + 0.1, f"q + g_OK = {q_kogu:.2f} kN/m", ha='left', color='green', fontsize=8, weight='bold')

# Koondkoormused F (punased nooled)
noole_kõrgus = 1.2
ax1.annotate('', xy=(a, 0.05), xytext=(a, noole_kõrgus), arrowprops=dict(arrowstyle="fancy", color='red', lw=1.5))
ax1.annotate('', xy=(L-a, 0.05), xytext=(L-a, noole_kõrgus), arrowprops=dict(arrowstyle="fancy", color='red', lw=1.5))

ax1.text(a, noole_kõrgus + 0.1, f"F = {F:.1f} kN", ha='center', color='red', fontsize=8, weight='bold')
ax1.text(L - a, noole_kõrgus + 0.1, f"F = {F:.1f} kN", ha='center', color='red', fontsize=8, weight='bold')

# Mõõduketi tähised skeemil
ax1.text(a/2, -0.3, f"{a:.1f} m", ha='center', fontsize=8, color='gray')
ax1.text(L/2, -0.3, f"{(L-2*a):.1f} m", ha='center', fontsize=8, color='gray')
ax1.text(L - a/2, -0.3, f"{a:.1f} m", ha='center', fontsize=8, color='gray')

ax1.set_ylim(-0.8, noole_kõrgus + 0.8)
ax1.axis('off')
ax1.set_title("Arvutusskeem ja koormused", fontsize=9, loc='left', color='gray')

# =====================================================================
# KESKMINE JOONIS: PAINDEMOMENDI DIAGRAMM
# =====================================================================
ax2.plot(x_telg, y_moment, color='red', linewidth=2)
ax2.fill_between(x_telg, y_moment, color='red', alpha=0.1)

ax2.set_xlim(0, L)
ax2.set_ylabel('Paindemoment (kNm)', fontsize=9)
ax2.grid(True, linestyle=':', alpha=0.6)
ax2.invert_yaxis()

# Max M nihutatud madalale puhtale valgele pinnale joone alla (+380)
ax2.text(8.0, M_Ed + 380, f"Max M = {M_Ed:.2f} kNm", ha='center', color='red', weight='bold', fontsize=9)

# Vertikaalsed punktiirjooned koormuste kohalt diagrammile
M_koormuse_all = R_A * a - (q_kogu * (a ** 2)) / 2
ax2.plot([a, a], [0, M_koormuse_all], linestyle='--', color='gray', alpha=0.5)
ax2.plot([L - a, L - a], [0, M_koormuse_all], linestyle='--', color='gray', alpha=0.5)

# Koormusalused punktid punase diagrammi sees
ax2.text(a, M_koormuse_all - 350, f"{M_koormuse_all:.1f}", ha='center', fontsize=8, color='black')
ax2.text(L - a, M_koormuse_all - 350, f"{M_koormuse_all:.1f}", ha='center', fontsize=8, color='black')

# PARANDATUD KOHT: Eemaldatud potentsiaalselt vigane matemaatiline tekst pealkirjast
ax2.set_title("Paindemomendi diagramm M_Ed", fontsize=9, loc='left', color='gray')

# =====================================================================
# ALUMINE JOONIS: PÕIKJÕU DIAGRAMM
# =====================================================================
ax3.plot(x_telg, y_poikjoud, color='orange', linewidth=2)
ax3.fill_between(x_telg, y_poikjoud, color='orange', alpha=0.1)
ax3.plot([0, L], [0, 0], color='black', linewidth=1)  # Nulltelg

ax3.set_xlim(0, L)
ax3.set_xlabel('Tala pikkus (m)', fontsize=9)
ax3.set_ylabel('Põikjõud (kN)', fontsize=9)
ax3.grid(True, linestyle=':', alpha=0.6)

# Põikjõu väärtused otspunktides ja koormuste all
V_max_tugi = abs(y_poikjoud[0])
V_enne_koormust = R_A - q_kogu * a
V_parast_koormust = V_enne_koormust - F

# Ääretoed nihutatud vabale alale joonte alla/peale
ax3.text(0.2, V_max_tugi - 50, f"{V_max_tugi:.1f}", ha='left', fontsize=8, color='black', weight='bold')
ax3.text(L - 0.2, -V_max_tugi + 20, f"-{V_max_tugi:.1f}", ha='right', fontsize=8, color='black', weight='bold')

# Kõrgeim väärtus enne esimest koormust (224.6) astme kohal vasakul
ax3.text(a - 0.1, V_enne_koormust + 25, f"{V_enne_koormust:.1f}", ha='right', fontsize=8, color='black')
# Väärtus kohe pärast koormust hüppest allpool
ax3.text(a + 0.2, V_parast_koormust - 45, f"{V_parast_koormust:.1f}", ha='left', fontsize=8, color='black')

# Kuvatakse ainult üks ja kõige olulisem puhas väärtus täpselt keskkohas (0.0 kN)
ax3.text(8.0, 20, "0.0", ha='center', fontsize=8, color='black', weight='bold')

# PARANDATUD KOHT: Eemaldatud potentsiaalselt vigane matemaatiline tekst pealkirjast
ax3.set_title("Põikjõu diagramm V_Ed", fontsize=9, loc='left', color='gray')

# Tihendame jooniste vahet ja kuvame Streamlitis
plt.tight_layout()
st.pyplot(fig)




# --- 2. GEOMEETRILISED KARAKTERISTIKUD ---
I_web = (tw * (c_sein_karakt ** 3)) / 12
steiner_part = A_f * (z_f ** 2)

# Inertsimoment ühe tehtega ja vastupanumomendid
I_y = I_web + 2 * ((b_prof * (tf ** 3)) / 12 + steiner_part)
I_y_cm4 = I_y / 10000

W_el_y = (I_y / (h / 2)) / 1000

# Plastse vastupanumomendi arvutus osade kaupa (St = Sc)
S_web_half = (tw * (c_sein_karakt ** 2)) / 8
S_flange_half = tf * b_prof * z_f
S_pool = (S_web_half + S_flange_half) / 1000  # teisendus cm³
W_pl_y = 2 * S_pool

st.write("Leian ristlõike inertsimomendi:")
st.latex(
    rf"I_y = \frac{{{tw:.1f} \cdot {c_sein_karakt:.1f}^3}}{{12}} + "
    rf"2 \cdot \left( \frac{{{b_prof:.1f} \cdot {tf:.1f}^3}}{{12}} + {A_f:.1f} \cdot {z_f:.1f}^2 \right) = "
    rf"{I_y:,.1f}\text{{ mm}}^4 \quad \rightarrow \quad \mathbf{{I_y = {I_y_cm4:,.2f}\text{{ cm}}^4}}"
)

st.write("Leian vastupanumomendid:")
st.latex(rf"W_{{el,y}} = \frac{{I_y}}{{h/2}} = \frac{{{I_y:,.1f}}}{{{h/2:.1f}}} \cdot 10^{{-3}} = {W_el_y:,.1f}\text{{ cm}}^3")

st.latex(rf"W_{{pl,y}} = S_t + S_c")
st.latex(rf"S_t = S_c = \left( \frac{{{tw:.1f} \cdot {c_sein_karakt:.1f}^2}}{{8}} + ({tf:.1f} \cdot {b_prof:.1f}) \cdot {z_f:.1f} \right) \cdot 10^{{-3}} = {S_pool:,.1f}\text{{ cm}}^3")
st.latex(rf"W_{{pl,y}} = {S_pool:,.1f} + {S_pool:,.1f} = {W_pl_y:,.1f}\text{{ cm}}^3")

# --- 4. RISTLÕIKEKLASSI MÄÄRAMINE ---
st.markdown("<b style='font-size: 1rem;'>4. Ristlõikeklassi määramine</b>", unsafe_allow_html=True)

# 1. VÖÖ (Surutud element)
c_voo = (b_prof - tw - 2 * r_val) / 2
suhe_voo = c_voo / tf

if suhe_voo <= 9 * epsilon:
    klass_voo = 1
    vordlus_voo = f"≤ 9·ε = {9 * epsilon:.2f}"
elif suhe_voo <= 10 * epsilon:
    klass_voo = 2
    vordlus_voo = f"≤ 10·ε = {10 * epsilon:.2f}"
elif suhe_voo <= 14 * epsilon:
    klass_voo = 3
    vordlus_voo = f"≤ 14·ε = {14 * epsilon:.2f}"
else:
    klass_voo = 4
    vordlus_voo = f"> 14·ε = {14 * epsilon:.2f}"

# 2. SEIN (Painutatud element)
c_sein = h - 2 * tf - 2 * r_val
suhe_sein = c_sein / tw

if suhe_sein <= 72 * epsilon:
    klass_sein = 1
    vordlus_sein = f"≤ 72·ε = {72 * epsilon:.2f}"
elif suhe_sein <= 83 * epsilon:
    klass_sein = 2
    vordlus_sein = f"≤ 83·ε = {83 * epsilon:.2f}"
elif suhe_sein <= 124 * epsilon:
    klass_sein = 3
    vordlus_sein = f"≤ 124·ε = {124 * epsilon:.2f}"
else:
    klass_sein = 4
    vordlus_sein = f"> 124·ε = {124 * epsilon:.2f}"

kogu_klass = max(klass_voo, klass_sein)

st.write(f"Vöö: c/t = {c_voo:.1f}/{tf:.1f} = {suhe_voo:.2f} {vordlus_voo} $\\Rightarrow$ ristlõikeklass {klass_voo}")
st.write(f"Sein: c/t = {c_sein:.1f}/{tw:.1f} = {suhe_sein:.2f} {vordlus_sein} $\\Rightarrow$ ristlõikeklass {klass_sein}")
st.write(f"**Kogu profiili ristlõikeklass: {kogu_klass}**")

# --- 5. PAINDEVÕIME ARVUTUS ---
st.markdown("<b style='font-size: 1rem;'>5. Paindekandevõime</b>", unsafe_allow_html=True)

if kogu_klass == 1 or kogu_klass == 2:
    W_määrav = W_pl_y
    M_Rd = (W_pl_y * 1000 * f_y) / gamma_M0 / 10**6
    valem_tekst = r"M_{c,Rd} = \frac{W_{pl,y} \cdot f_y}{\gamma_{M0}}"
    tehe_tekst = f"\\frac{{{W_pl_y:.1f} \\cdot 10^3 \\cdot {f_y:.0f}}}{{{gamma_M0:.2f}}} \\cdot 10^{{-6}} = {M_Rd:.2f} \\text{{ kNm}}"
else:
    W_määrav = W_el_y
    M_Rd = (W_el_y * 1000 * f_y) / gamma_M0 / 10**6
    valem_tekst = r"M_{c,Rd} = \frac{W_{el,y} \cdot f_y}{\gamma_{M0}}"
    tehe_tekst = f"\\frac{{{W_el_y:.1f} \\cdot 10^3 \\cdot {f_y:.0f}}}{{{gamma_M0:.2f}}} \\cdot 10^{{-6}} = {M_Rd:.2f} \\text{{ kNm}}"

st.latex(rf"{valem_tekst}")
st.latex(rf"M_{{c,Rd}} = {tehe_tekst}")

# --- 6. PÕIKJÕUKINDLUSE ARVUTUS JA KONTROLL ---
st.markdown("<b style='font-size: 1rem;'>6. Põikjõukandevõime ja kontroll</b>", unsafe_allow_html=True)

# Lõikepindala arvutus ja selle lahtikirjutamine
A_v = eta * c_sein * tw
V_pl_Rd = (A_v * (f_y / math.sqrt(3))) / gamma_M0 / 1000

st.write("Leian plastse lõikepindala Av:")
st.latex(rf"A_v = \eta \cdot c_{{sein}} \cdot t_w = {eta:.1f} \cdot {c_sein:.1f} \cdot {tw:.1f} = {A_v:.1f}\text{{ mm}}^2")

st.write("Kontrollin plastset põikjõukandevõmet:")
st.latex(r"V_{pl,Rd} = \frac{A_v \cdot (f_y / \sqrt{3})}{\gamma_{M0}}")
st.latex(rf"V_{{pl,Rd}} = \frac{{{A_v:.1f} \cdot ({f_y:.0f} / \sqrt{{3}})}}{{{gamma_M0:.2f}}} \cdot 10^{{-3}} = {V_pl_Rd:.2f} \text{{ kN}}")

# Kontroll Sinu esitatud toereaktsiooni (829.38 kN) suhtes
V_Ed = 829.38
suhe_V = V_Ed / V_pl_Rd
st.latex(rf"\frac{{V_{{Ed}}}}{{V_{{pl,Rd}}}} = \frac{{{V_Ed:.2f}}}{{{V_pl_Rd:.2f}}} = {suhe_V:.3f}")

if suhe_V < 1.00:
    st.success(f"Põikjõukandevõime on tagatud (Kasutusaste: {suhe_V * 100:.1f}%)")
else:
    st.error(f"Põikjõukandevõime EI OLE tagatud! (Kasutusaste: {suhe_V * 100:.1f}%)")

# --- 7. PAINDKANDEVÕIME KASUTUSASTE ---
st.markdown("<b style='font-size: 1rem;'>7. Paindekandevõime kontroll</b>", unsafe_allow_html=True)

suhe_M = M_Ed / M_Rd
st.latex(rf"\frac{{M_{{Ed}}}}{{M_{{c,Rd}}}} = \frac{{{M_Ed:.2f}}}{{{M_Rd:.2f}}} = {suhe_M:.3f}")

if suhe_M < 1.00:
    st.success(f"Paindekandevõime on tagatud (Kasutusaste: {suhe_M * 100:.1f}%)")
else:
    st.error(f"Paindekandevõime EI OLE tagatud! (Kasutusaste: {suhe_M * 100:.1f}%)")

# --- 8. LÄBIPAINDE ARVUTUS (SLS) ---
st.markdown("<b style='font-size: 1rem;'>8. Läbipainde kontroll (SLS)</b>", unsafe_allow_html=True)

# Teisendame ühikud valemite põhiühikutesse (mm ja N)
L_mm = L * 1000
a_mm = a * 1000
F_N = F * 1000
q_Nmm = q_kogu

# 1. Koondkoormuste läbipaine (mm)
w_F = (F_N * a_mm / (24 * E * I_y)) * (3 * (L_mm ** 2) - 4 * (a_mm ** 2))
# 2. Jaotatud koormuse läbipaine (mm)
w_q = (5 * q_Nmm * (L_mm ** 4)) / (384 * E * I_y)
# Kogu läbipaine summa
w_max = w_F + w_q

# Lubatav läbipaine vastavalt piirangule L/400
w_lubatav = L_mm / 400
suhe_w = w_max / w_lubatav

st.write("Leian läbipandesse panustavad osad tala keskel:")

# w_F lahtikirjutatud tehe
st.latex(
    rf"w_F = \frac{{{F_N:.1f} \cdot {a_mm:.1f}}}{{24 \cdot {E:.0f} \cdot {I_y:,.1f}}} \cdot "
    rf"\left( 3 \cdot {L_mm:.0f}^2 - 4 \cdot {a_mm:.0f}^2 \right) = {w_F:.2f}\text{{ mm}}"
)

# w_q lahtikirjutatud tehe
st.latex(
    rf"w_q = \frac{{5 \cdot {q_Nmm:.4f} \cdot {L_mm:.0f}^4}}{{384 \cdot {E:.0f} \cdot {I_y:,.1f}}} = {w_q:.2f}\text{{ mm}}"
)

st.latex(rf"w_{{max}} = {w_F:.2f} + {w_q:.2f} = {w_max:.2f}\text{{ mm}}")

st.write(f"Kontrollin läbipainet piirväärtuse $L/400 = {w_lubatav:.1f}\\text{{ mm}}$ suhtes:")
st.latex(rf"\frac{{w_{{max}}}}{{w_{{lubatav}}}} = \frac{{{w_max:.2f}}}{{{w_lubatav:.1f}}} = {suhe_w:.3f}")

if suhe_w < 1.00:
    st.success(f"Läbipaine on lubatavates piirides (Kasutusaste: {suhe_w * 100:.1f}%)")
else:
    st.error(f"Läbipaine ÜLETAB lubatava piiri! (Kasutusaste: {suhe_w * 100:.1f}%)")

# Sulgeme kogu lehte katva footnotesize konteineri
st.markdown('</div>', unsafe_allow_html=True)

















