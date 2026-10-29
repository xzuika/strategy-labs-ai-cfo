"""Strategy Labs · AI CFO – pagrindinis Streamlit puslapis.

Paleidimas:  streamlit run app.py
Puslapis sujungia 4 modulius: duomenų įkėlimas -> analizė -> prognozė -> „Paklausk CFO“.
"""
import plotly.graph_objects as go
import streamlit as st

from analize import analizuoti, eur, men_pav, proc
from cfo_pokalbis import atsakyti
from duomenys_ikelimas import DUOMENU_APLANKAS, demo_rinkiniai, ikelti_demo, nuskaityti_faila
from prognoze import prognozuoti

st.set_page_config(page_title="Strategy Labs · AI CFO", page_icon="📊", layout="wide")
st.title("📊 Strategy Labs · AI CFO")
st.caption("Prototipas: iš įmonės transakcijų – į vadovų sprendimus per kelias sekundes")

# ---------- 1. DUOMENŲ ŠALTINIS (šoninė juosta) ----------
rinkiniai = demo_rinkiniai()
with st.sidebar:
    st.header("1. Duomenys")
    saltinis = st.radio("Šaltinis", ["Demo duomenys", "Įkelti savo failą"])
    if saltinis == "Demo duomenys":
        pasirinktas = st.selectbox("Pavyzdinė įmonė", rinkiniai, format_func=lambda r: r["name"])
        df = ikelti_demo(pasirinktas["id"])
        pradinis = st.number_input("Pradinis pinigų likutis (€)", value=pasirinktas["opening"], step=50_000)
        st.warning("PAVYZDINIAI DUOMENYS: įmonė išgalvota, mastai pagal viešus sektoriaus duomenis, mėnesio transakcijos sumodeliuotos.")
        st.info("Istorija: " + pasirinktas["story"])
        pavadinimas = pasirinktas["name"]
    else:
        failas = st.file_uploader("Excel arba CSV", type=["xlsx", "xls", "csv"])
        st.caption("Stulpeliai: data, kontrahentas, kategorija, padalinys, suma (+ pajamos, − išlaidos); neprivaloma: PVM, mokejimo_terminas, apmoketa")
        pradinis = st.number_input("Pradinis pinigų likutis (€)", value=500_000, step=50_000)
        df, pavadinimas = None, None
        if failas:
            try:
                df, pavadinimas = nuskaityti_faila(failas, failas.name), f"Įkeltas failas: {failas.name}"
            except ValueError as e:
                st.error(str(e))
    st.divider()
    st.caption("Atsisiųsti pavyzdinius failus:")
    for r in rinkiniai:
        c1, c2 = st.columns(2)
        c1.download_button(f"{r['id']}.xlsx", (DUOMENU_APLANKAS / f"pavyzdys_{r['id']}.xlsx").read_bytes(), f"pavyzdys_{r['id']}.xlsx", key="x" + r["id"])
        c2.download_button(f"{r['id']}.csv", (DUOMENU_APLANKAS / f"pavyzdys_{r['id']}.csv").read_bytes(), f"pavyzdys_{r['id']}.csv", key="c" + r["id"])

if df is None:
    st.info("⬅ Pasirinkite demo duomenis arba įkelkite Excel / CSV failą.")
    st.stop()

a = analizuoti(df, pradinis)
m = a.menesiai
st.subheader(pavadinimas)
st.caption(f"Išanalizuota {len(df)} transakcijų · {men_pav(m.index[0])} – {men_pav(m.index[-1])}")

# ---------- 2. SKYDELIS: KPI kortelės ----------
k = st.columns(5)
k[0].metric("Pajamos", eur(m.pajamos.sum()), f"{(m.pajamos.iloc[-1] / m.pajamos.iloc[-2] - 1) * 100:+.1f}% pask. mėn.")
k[1].metric("Sąnaudos", eur(m.visos_sanaudos.sum()))
marza = 1 - m.tiesiogines.sum() / m.pajamos.sum()
k[2].metric("Bendroji marža", proc(marza), f"{(m.marza.iloc[-1] - m.marza.iloc[-2]) * 100:+.1f} p.p.")
k[3].metric("Veiklos rezultatas", eur(m.rezultatas.sum()))
k[4].metric("Pinigų likutis", eur(a.pinigai_pabaigoje))

c1, c2 = st.columns([2, 1])
x = [str(i) for i in m.index]
fig = go.Figure()
fig.add_bar(x=x, y=m.pajamos, name="Pajamos", marker_color="#93c5fd")
fig.add_bar(x=x, y=m.visos_sanaudos, name="Sąnaudos", marker_color="#fca5a5")
fig.add_scatter(x=x, y=m.marza * 100, name="Marža %", yaxis="y2", line=dict(color="#1d4ed8", width=3))
fig.update_layout(title="Mėnesio tendencijos", height=380, yaxis2=dict(overlaying="y", side="right", ticksuffix="%"), legend=dict(orientation="h"))
c1.plotly_chart(fig, width="stretch")
pie = go.Figure(go.Pie(labels=a.kategorijos.index, values=a.kategorijos.values, hole=0.5))
pie.update_layout(title="Sąnaudų struktūra", height=380, showlegend=False)
c2.plotly_chart(pie, width="stretch")

# ---------- 3. VADOVŲ SANTRAUKA ----------
st.subheader("🧠 Vadovų santrauka (sugeneruota automatiškai)")
zenklas = {"rizika": "🔴 RIZIKA", "demesio": "🟠 DĖMESIO", "gerai": "🟢 GERAI"}
for lygis, tekstas in a.izvalgos:
    st.markdown(f"**{zenklas[lygis]}** – {tekstas}")

# ---------- 4. PROGNOZĖ SU „O KAS, JEI?“ ----------
st.subheader("📈 Pinigų srautų prognozė 6 mėn. · „O kas, jei?“")
s = st.columns(4)
kainos = s[0].slider("Kainų pokytis, %", -20, 20, 0)
sanaudos = s[1].slider("Sąnaudų pokytis, %", -20, 30, 0)
investicija = s[2].slider("Vienkartinė investicija, €", 0, int(max(100_000, m.pajamos.mean() * 2)), 0, step=10_000)
inv_men = s[2].selectbox("Investicijos mėnuo", range(1, 7), format_func=lambda i: f"{i}-as mėnuo")
terminas = s[3].slider("Apmokėjimo terminas klientams, d.", 0, 90, 0, step=15)

bazine = prognozuoti(a)
scen = prognozuoti(a, kainos / 100, sanaudos / 100, investicija, inv_men, terminas)
f2 = go.Figure()
f2.add_scatter(x=x[-6:], y=m.pinigai.tail(6), name="Faktas", line=dict(color="#0f172a", width=3))
f2.add_scatter(x=[x[-1]] + [str(i) for i in bazine.index], y=[a.pinigai_pabaigoje] + list(bazine.pinigai), name="Bazinė prognozė", line=dict(dash="dash", color="#94a3b8"))
f2.add_scatter(x=[x[-1]] + [str(i) for i in scen.index], y=[a.pinigai_pabaigoje] + list(scen.pinigai), name="Scenarijus", line=dict(color="#1d4ed8", width=3),
               marker=dict(size=10, color=["#1d4ed8"] + ["#dc2626" if v < 0 else "#1d4ed8" for v in scen.pinigai]))
f2.add_hline(y=0, line_color="#dc2626", line_dash="dot")
f2.update_layout(height=380, legend=dict(orientation="h"))
st.plotly_chart(f2, width="stretch")
neig = scen[scen.pinigai < 0]
if len(neig):
    st.error(f"⚠ Pinigų likutis taps neigiamas {men_pav(neig.index[0])} ({eur(neig.pinigai.iloc[0])}). Reikia finansavimo arba veiksmų prieš tai.")
else:
    st.success(f"✓ Pinigų pakanka visus 6 mėn. Mažiausias likutis {eur(scen.pinigai.min())}, po 6 mėn. {eur(scen.pinigai.iloc[-1])} "
               f"({eur(scen.pinigai.iloc[-1] - bazine.pinigai.iloc[-1])} vs bazinė).")

# ---------- 5. PAKLAUSK CFO ----------
st.subheader("💬 Paklausk CFO")
raktas = f"pokalbis_{pavadinimas}"
st.session_state.setdefault(raktas, [])
greiti = ["Kodėl krito marža?", "Kas vėluoja mokėti?", "Kada pritrūks pinigų?", "Kokios didžiausios sąnaudos?", "Kas didžiausias klientas?"]
mygt = st.columns(len(greiti))
paspaustas = next((q for i, q in enumerate(greiti) if mygt[i].button(q)), None)
klausimas = st.chat_input("Pvz.: Kokia buvo marža gegužę?") or paspaustas
if klausimas:
    ats, saltinis_txt = atsakyti(klausimas, a, scen)
    st.session_state[raktas].append((klausimas, ats, saltinis_txt))
for q, ats, src in reversed(st.session_state[raktas]):
    st.chat_message("user").write(q)
    st.chat_message("assistant").markdown(ats.replace("\n", "  \n") + f"\n\n*{src}*")

st.divider()
st.caption("Strategy Labs · AI CFO koncepcijos prototipas. Demo duomenys išgalvoti. Sprendimas nepakeičia buhalterio ar mokesčių konsultanto.")
