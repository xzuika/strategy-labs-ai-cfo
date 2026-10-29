"""4 žingsnis: „Paklausk CFO“ – atsakymai į klausimus apie įkeltus duomenis.

Du režimai:
1) DI modelis (jei nustatytas OPENAI_API_KEY arba AI_GATEWAY_API_KEY) – gauna duomenų santrauką ir atsako laisvai.
2) Taisyklių variklis (veikia visada, be interneto) – atpažįsta klausimo temą ir suskaičiuoja atsakymą iš lentelių.
"""
import json
import os
import urllib.request

from analize import Analize, MENESIAI, eur, men_pav, proc


def _kontekstas(a: Analize, progn) -> str:
    """Suspaudžia duomenis į trumpą JSON, kurį perduodame DI modeliui."""
    m = a.menesiai
    return json.dumps({
        "menesiai": [{"men": str(i), "pajamos": round(r.pajamos), "tiesiogines": round(r.tiesiogines),
                      "marza_proc": round(r.marza * 100, 1), "pinigai": round(r.pinigai)} for i, r in m.iterrows()],
        "kategorijos": a.kategorijos.round().to_dict(), "klientai": a.klientai.round().to_dict(),
        "pradelsta": {k: round(v) for k, v in a.pradelsta.suma.items()},
        "izvalgos": [t for _, t in a.izvalgos],
        "prognoze": {str(i): round(r.pinigai) for i, r in progn.iterrows()},
    }, ensure_ascii=False)


def klausti_di(klausimas: str, a: Analize, progn) -> tuple[str, str] | None:
    """Bando paklausti DI modelio. Grąžina (atsakymas, modelis) arba None, jei rakto nėra ar įvyko klaida."""
    if os.getenv("OPENAI_API_KEY"):
        url, raktas, modelis = "https://api.openai.com/v1/chat/completions", os.getenv("OPENAI_API_KEY"), "gpt-4o-mini"
    elif os.getenv("AI_GATEWAY_API_KEY"):
        url, raktas, modelis = "https://ai-gateway.vercel.sh/v1/chat/completions", os.getenv("AI_GATEWAY_API_KEY"), "openai/gpt-4o-mini"
    else:
        return None
    uzklausa = {"model": modelis, "temperature": 0.2, "messages": [
        {"role": "system", "content": "Tu esi Strategy Labs AI CFO. Atsakyk lietuviškai, glaustai, su konkrečiais skaičiais iš duomenų. "
                                      "Neišgalvok skaičių. Pabaigoje – viena praktinė rekomendacija."},
        {"role": "user", "content": f"Duomenys: {_kontekstas(a, progn)}\n\nKlausimas: {klausimas}"}]}
    try:
        req = urllib.request.Request(url, json.dumps(uzklausa).encode(), {"Content-Type": "application/json", "Authorization": f"Bearer {raktas}"})
        with urllib.request.urlopen(req, timeout=20) as r:
            return json.load(r)["choices"][0]["message"]["content"], modelis
    except Exception:
        return None


def atsakyti_taisyklemis(klausimas: str, a: Analize, progn) -> str:
    """Atpažįsta temą pagal raktinius žodžius ir suskaičiuoja atsakymą."""
    q, m = klausimas.lower(), a.menesiai
    # Ar paminėtas konkretus mėnuo? (pvz. „gegužę“)
    men = next((i for i in reversed(m.index) if MENESIAI[i.month - 1][:4] in q), None)

    if any(z in q for z in ("marž", "pelning")):
        if men is not None and m.index.get_loc(men) > 0:
            pr = m.index[m.index.get_loc(men) - 1]
            return f"{men_pav(men)} bendroji marža buvo {proc(m.loc[men, 'marza'])} (prieš tai {proc(m.loc[pr, 'marza'])})."
        return next(t for _, t in a.izvalgos if "marža" in t)
    if any(z in q for z in ("skol", "vėluo", "pradels", "neapmok")):
        if a.pradelsta.empty:
            return "Pradelstų gautinų sumų nėra."
        return "Pradelstos sumos:\n" + "\n".join(f"• {k}: {eur(r.suma)} (terminas nuo {r.seniausias:%Y-%m-%d})" for k, r in a.pradelsta.iterrows())
    if any(z in q for z in ("pritrūk", "pinig", "likut", "prognoz", "neigiam")):
        neig = progn[progn.pinigai < 0]
        kada = f"pinigai taps neigiami {men_pav(neig.index[0])} ({eur(neig.pinigai.iloc[0])})" if len(neig) else f"pinigų pakaks, po 6 mėn. bus {eur(progn.pinigai.iloc[-1])}"
        return f"Dabartinis pinigų likutis {eur(a.pinigai_pabaigoje)}. Pagal pasirinktą scenarijų {kada}."
    if any(z in q for z in ("sąnaud", "išlaid", "kašt")):
        return "Didžiausios sąnaudos:\n" + "\n".join(f"• {k}: {eur(v)} ({proc(v / m.pajamos.sum())} pajamų)" for k, v in a.kategorijos.head(5).items())
    if any(z in q for z in ("klient", "pirkėj")):
        return "Didžiausi klientai:\n" + "\n".join(f"• {k}: {eur(v)} ({proc(v / a.klientai.sum())})" for k, v in a.klientai.head(5).items())
    if any(z in q for z in ("padalin", "dukter", "projekt")):
        return "Padaliniai (pajamos / sąnaudos):\n" + "\n".join(f"• {k}: {eur(r.pajamos)} / {eur(r.sanaudos)}" for k, r in a.padaliniai.iterrows())
    if any(z in q for z in ("geriaus", "blogiaus", "mėnuo")):
        g, b = m.pajamos.idxmax(), m.pajamos.idxmin()
        return f"Geriausias mėnuo – {men_pav(g)} ({eur(m.loc[g, 'pajamos'])}), silpniausias – {men_pav(b)} ({eur(m.loc[b, 'pajamos'])})."
    if any(z in q for z in ("pajam", "apyvart", "pardavim")):
        if men is not None:
            return f"{men_pav(men)} pajamos: {eur(m.loc[men, 'pajamos'])}."
        return f"Pajamos per {len(m)} mėn.: {eur(m.pajamos.sum())}, vidutiniškai {eur(m.pajamos.mean())} per mėnesį."
    if any(z in q for z in ("rekomend", "patar", "daryti")):
        return "Prioritetai:\n" + "\n".join(f"{i}. {t}" for i, (lyg, t) in enumerate([x for x in a.izvalgos if x[0] != "gerai"], 1))
    return "Galiu atsakyti apie maržą, sąnaudas, klientus, skolas, padalinius, geriausią mėnesį ir pinigų prognozę."


def atsakyti(klausimas: str, a: Analize, progn) -> tuple[str, str]:
    """Pirma bando DI; jei nepavyksta – taisyklių variklis. Grąžina (atsakymas, šaltinis)."""
    di = klausti_di(klausimas, a, progn)
    if di:
        return di[0], f"DI modelis ({di[1]})"
    return atsakyti_taisyklemis(klausimas, a, progn), "Apskaičiuota iš duomenų (taisyklių variklis)"
