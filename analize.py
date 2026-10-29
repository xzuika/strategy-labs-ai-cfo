"""2 žingsnis: finansų analizė ir automatinė vadovų santrauka.

Skaičiuoja mėnesio pajamas, sąnaudas, maržą, pinigų likutį, pradelstas skolas
ir iš jų suformuluoja 3–5 įžvalgas lietuviškai (be DI – grynai iš skaičių).
"""
import re
from dataclasses import dataclass, field

import pandas as pd

# Tiesioginės (kintamos) sąnaudos – jos lemia BENDRĄJĄ maržą
TIESIOGINES = re.compile(r"žaliav|medžiag|savikain|degal|subrang|prekių|trąš|sėkl|pašar|komponent|aparat", re.I)
# Ne veiklos išmokos – mažina pinigus, bet ne pelną (investicijos, paskolų grąžinimas)
NE_VEIKLOS = re.compile(r"investic|paskol", re.I)
SIANDIEN = pd.Timestamp("2026-10-29")
MENESIAI = ["sausis", "vasaris", "kovas", "balandis", "gegužė", "birželis", "liepa",
            "rugpjūtis", "rugsėjis", "spalis", "lapkritis", "gruodis"]


def men_pav(p: pd.Period) -> str:
    return f"{MENESIAI[p.month - 1]} {p.year}"


def eur(v: float) -> str:
    """Gražus sumos formatas: 1,25 M€ / 350 k€ / 9 800 €."""
    if abs(v) >= 1e6:
        return f"{v / 1e6:.2f} M€".replace(".", ",")
    if abs(v) >= 1e4:
        return f"{v / 1e3:.0f} k€"
    return f"{v:,.0f} €".replace(",", " ")


def proc(v: float) -> str:
    return f"{v * 100:.1f}%".replace(".", ",")


@dataclass
class Analize:
    menesiai: pd.DataFrame          # viena eilutė = vienas mėnuo
    kategorijos: pd.Series          # sąnaudos pagal kategoriją
    klientai: pd.Series             # pajamos pagal klientą
    padaliniai: pd.DataFrame        # pajamos ir sąnaudos pagal padalinį
    pradelsta: pd.DataFrame         # pradelstos gautinos sumos
    pinigai_pabaigoje: float
    izvalgos: list = field(default_factory=list)


def analizuoti(df: pd.DataFrame, pradinis_likutis: float) -> Analize:
    pajamos = df[df.suma > 0]
    islaidos = df[df.suma < 0].assign(suma=lambda x: -x.suma)
    veiklos = islaidos[~islaidos.kategorija.str.contains(NE_VEIKLOS)]
    tiesiog = veiklos[veiklos.kategorija.str.contains(TIESIOGINES)]

    m = pd.DataFrame({
        "pajamos": pajamos.groupby("menuo").suma.sum(),
        "tiesiogines": tiesiog.groupby("menuo").suma.sum(),
        "visos_sanaudos": veiklos.groupby("menuo").suma.sum(),
        "ne_veiklos": islaidos[islaidos.kategorija.str.contains(NE_VEIKLOS)].groupby("menuo").suma.sum(),
    }).fillna(0).sort_index()
    m["marza"] = (m.pajamos - m.tiesiogines) / m.pajamos.where(m.pajamos != 0)
    m["rezultatas"] = m.pajamos - m.visos_sanaudos

    # Pinigai juda tą mėnesį, kai suėjo mokėjimo terminas – ir tik jei apmokėta
    apmoketa = df[df.apmoketa != "Ne"].copy()
    apmoketa["pinigu_men"] = apmoketa.terminas.dt.to_period("M").clip(lower=m.index.min())
    srautas = apmoketa.groupby("pinigu_men").suma.sum().reindex(m.index, fill_value=0)
    m["pinigu_srautas"] = srautas
    m["pinigai"] = pradinis_likutis + srautas.cumsum()

    neapm = pajamos[(pajamos.apmoketa == "Ne") & (pajamos.terminas < SIANDIEN)]
    pradelsta = neapm.groupby("kontrahentas").agg(suma=("suma", "sum"), seniausias=("terminas", "min")).sort_values("suma", ascending=False)

    pad = pd.DataFrame({"pajamos": pajamos.groupby("padalinys").suma.sum(),
                        "sanaudos": veiklos.groupby("padalinys").suma.sum()}).fillna(0)

    a = Analize(m, veiklos.groupby("kategorija").suma.sum().sort_values(ascending=False),
                pajamos.groupby("kontrahentas").suma.sum().sort_values(ascending=False),
                pad, pradelsta, float(m.pinigai.iloc[-1]))
    a.izvalgos = sugeneruoti_izvalgas(a, veiklos)
    return a


def sugeneruoti_izvalgas(a: Analize, veiklos: pd.DataFrame) -> list[tuple[str, str]]:
    """Grąžina sąrašą (lygis, tekstas). Lygis: 'rizika', 'demesio' arba 'gerai'."""
    m, out = a.menesiai, []
    puse = len(m) // 2
    p1, p2 = m.iloc[:puse], m.iloc[puse:]
    marza1 = 1 - p1.tiesiogines.sum() / p1.pajamos.sum()
    marza2 = 1 - p2.tiesiogines.sum() / p2.pajamos.sum()

    # 1) Marža: kuri kategorija labiausiai padidino savo dalį pajamose?
    if marza2 - marza1 < -0.01:
        dalis = veiklos.pivot_table(index="menuo", columns="kategorija", values="suma", aggfunc="sum").fillna(0)
        d1 = dalis.iloc[:puse].sum() / p1.pajamos.sum()
        d2 = dalis.iloc[puse:].sum() / p2.pajamos.sum()
        kalte = (d2 - d1).idxmax()
        suolis = (m.marza.shift(1) - m.marza).idxmax()
        out.append(("rizika", f"Bendroji marža krito {abs(marza2 - marza1) * 100:.1f} p.p.".replace(".", ",", 1) + f" (nuo {proc(marza1)} iki {proc(marza2)}). "
                    f"Pagrindinė priežastis – „{kalte}“ dalis pajamose išaugo nuo {proc(d1[kalte])} iki {proc(d2[kalte])}, "
                    f"ryškiausias šuolis {men_pav(suolis)}. Metinis poveikis pelnui ≈ {eur((d2[kalte] - d1[kalte]) * p2.pajamos.sum() * 2)}."))
    else:
        pastaba = " Verslas labai sezoniškas – pusmečių marža nepalyginama, vertinkite metinę." if marza2 - marza1 > 0.2 else ""
        out.append(("gerai", f"Bendroji marža stabili arba gerėja: {proc(marza1)} → {proc(marza2)}.{pastaba}"))

    # 2) Pradelstos skolos
    if len(a.pradelsta):
        k, eil = a.pradelsta.index[0], a.pradelsta.iloc[0]
        dienos = (SIANDIEN - eil.seniausias).days
        out.append(("rizika", f"Pradelstos gautinos sumos: {eur(a.pradelsta.suma.sum())}. Didžiausias skolininkas – {k}: "
                    f"{eur(eil.suma)}, seniausia sąskaita vėluoja {dienos} d. Rekomendacija: priminimas šią savaitę, "
                    f"stabdyti naujus užsakymus kreditan, svarstyti faktoringą."))

    # 3) Silpniausias pinigų srautų mėnuo
    blog = m.pinigu_srautas.idxmin()
    vid = m.pajamos.mean()
    if m.loc[blog, "ne_veiklos"] > 0.15 * m.loc[blog, "visos_sanaudos"]:
        kodel = "Priežastis – investicijos ar paskolų įmokos."
    else:
        kodel = "Tai sezoninis pinigų tarpas – verta iš anksto susitarti dėl kredito linijos."
    out.append(("demesio", f"Silpniausias pinigų srautų mėnuo – {men_pav(blog)} (grynasis srautas {eur(m.loc[blog, 'pinigu_srautas'])}). {kodel}"))

    # 4) Kliento koncentracija
    dalis = a.klientai.iloc[0] / a.klientai.sum()
    if 0.2 < dalis < 0.9:
        out.append(("demesio", f"Koncentracijos rizika: {a.klientai.index[0]} sudaro {proc(dalis)} visų pajamų."))

    # 5) Rezultatas
    rez = m.rezultatas.sum()
    out.append(("gerai" if rez > 0 else "rizika", f"Veiklos rezultatas per {len(m)} mėn.: {eur(rez)} ({proc(rez / m.pajamos.sum())} pajamų)."))
    return out[:5]
