# Strategy Labs · AI CFO – kaip tai veikia (paprastai)

> Streamlit Cloud: pagrindinis failas `app.py`. DI raktą (neprivaloma) dėkite į Streamlit „Secrets“, ne į kodą.

**Idėja:** įmonė įkelia savo transakcijas (Excel arba CSV), o programa per kelias sekundes parodo finansinį vaizdą, vadovams skirtą santrauką, 6 mėn. pinigų prognozę su „o kas, jei?“ scenarijais ir leidžia užduoti klausimus („Paklausk CFO“). Įkvėpta Noewe Accounting modelio (DI apskaita ir finansų vadovo lygio įžvalgos), bet tai savarankiška Strategy Labs koncepcija.

## Kaip paleisti (vienas kartas + viena komanda)
```bash
cd strategy-labs-ai-cfo
pip install -r requirements.txt
streamlit run app.py
```
Atsidaro naršyklėje: http://localhost:8501
Neprivaloma: jei nustatysite `OPENAI_API_KEY` (arba `AI_GATEWAY_API_KEY`), „Paklausk CFO“ atsakinės DI modelis. Be rakto veikia taisyklių variklis, kuris skaičiuoja atsakymus tiesiai iš duomenų.

## Failai (repozitorijos šaknis)
| Failas | Ką daro (paprastai) |
|---|---|
| `app.py` | **Puslapis.** Sudeda viską į vieną ekraną: šoninė juosta su duomenimis, KPI kortelės, grafikai, santrauka, prognozės slankikliai ir pokalbis. Čia nėra skaičiavimų, tik išdėstymas. |
| `duomenys_ikelimas.py` | **1 žingsnis – duomenys.** Nuskaito Excel/CSV, suvienodina stulpelių pavadinimus, datas ir sumas. Taisyklė: + pajamos, − išlaidos. |
| `analize.py` | **2 žingsnis – analizė.** Suskaičiuoja mėnesio pajamas, sąnaudas, maržą, pinigų likutį, pradelstas skolas ir automatiškai parašo 3–5 įžvalgas (pvz. kodėl krito marža). |
| `prognoze.py` | **3 žingsnis – prognozė.** 6 mėn. pinigų srautai: vidutinės pajamos × sezoniškumas, sąnaudos pagal paskutinius 3 mėn., plius slankiklių poveikis (kaina, sąnaudos, investicija, apmokėjimo terminas). |
| `cfo_pokalbis.py` | **4 žingsnis – „Paklausk CFO“.** Pirma bando DI modelį, jei rakto nėra, atpažįsta klausimo temą (marža, skolos, pinigai, sąnaudos, klientai...) ir suskaičiuoja atsakymą. |
| `generuoti_duomenis.py` | Sukuria 4 pavyzdinius rinkinius aplanke `duomenys/`. |
| `duomenys/` | Pavyzdiniai failai `.xlsx` ir `.csv` (CSV tinka ir Google Sheets) + `rinkiniai.json` (pavadinimai, pradinis pinigų likutis, „istorija“). |
| `requirements.txt` | Reikalingos bibliotekos: streamlit, pandas, plotly, openpyxl. |

## Pavyzdiniai duomenys (VISI IŠGALVOTI)
Įmonės ir kontrahentai išgalvoti. Metiniai mastai parinkti pagal viešus sektoriaus duomenis, o mėnesio transakcijos sumodeliuotos.
1. **Gamintojas** „Nerio mišiniai“: ~4,8 M€, 24 darb., vid. bruto ~3 000 €, nedidelis nuostolis. Istorija: žaliavos brango, marža krito ~5,5 p.p., didžiausias klientas vėluoja ~315 k€.
2. **Žemės ūkis** „Lygumų ūkis“: ~8,6 M€, 69 darb., ~16 % pelningumas. Istorija: pavasario sąnaudų ir rudens pajamų sezoninis pinigų tarpas, kombaino investicija, eksportuotojas vėluoja.
3. **Technologijos** „Robotikos sprendimai“: ~1,9 M€, 14 darb., vid. bruto ~5 400 €, apie lūžio tašką, sparčiai auga.
4. **Įmonių grupė** „Šiaurės grupė“: ~28 M€ konsoliduotai, ~2 M€ nuostolis, 3 dukterinės + valdymas. Istorija: statybos kainos, palūkanų našta, investuotojas vėluoja.

Šaltiniai mastams: viešos įmonių finansinės ataskaitos ir darbuotojų / atlyginimų duomenys (rekvizitai.vz.lt, tax.lt, Sodros duomenys, apibendrinta faile `clients-research.csv`). Vidutinis šalies bruto darbo užmokestis 2026 m. II ketv. siekė 2 628 € (Valstybės duomenų agentūra, https://osp.stat.gov.lt/darbo-uzmokestis-ir-darbo-sanaudos).

## 3 paprasti „gyvi“ pakeitimai pokalbio metu (po kiekvieno: išsaugoti failą, puslapis pasiūlys „Rerun“)
1. **Pakeisti slankiklio ribas.** `app.py` eilutėje `kainos = s[0].slider("Kainų pokytis, %", -20, 20, 0)` pakeiskite `-20, 20` į `-50, 50`. Slankiklis iškart leis platesnį scenarijų.
2. **Pridėti naują KPI kortelę.** `app.py` pakeiskite `k = st.columns(5)` į `k = st.columns(6)` ir po `k[4]...` eilute pridėkite:
   `k[5].metric("Vid. mėn. pajamos", eur(m.pajamos.mean()))`
3. **Pridėti naują klausimą „Paklausk CFO“.** `cfo_pokalbis.py` funkcijoje `atsakyti_taisyklemis` prieš paskutinį `return` įrašykite:
   ```python
   if "darbuotoj" in q or "atlygin" in q:
       return f"Darbo užmokesčio sąnaudos: {eur(a.kategorijos.get('Darbo užmokestis', 0))}."
   ```
   ir paklauskite „Kiek kainuoja darbuotojai?“.

## Kas tikra, kas imituota
- **Tikra:** failų nuskaitymas, visi skaičiavimai, įžvalgų generavimas, prognozė ir slankikliai, taisyklių variklio atsakymai (viskas skaičiuojama iš įkelto failo).
- **Imituota:** duomenys (išgalvoti). DI pokalbis veikia tik nustačius API raktą, kitaip atsako taisyklių variklis.
- **Supaprastinta:** prognozė remiasi vidurkiais ir sezoniškumu (ne buhalterine apskaita), PVM tik informacinis, pradelstos skolos prognozėje nesurenkamos (konservatyvus požiūris).
