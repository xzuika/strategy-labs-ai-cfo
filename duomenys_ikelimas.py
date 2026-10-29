"""1 žingsnis: duomenų įkėlimas ir sutvarkymas.

Priima Excel (.xlsx) arba CSV failą ir paverčia jį vienoda lentele (pandas DataFrame)
su stulpeliais: data, menuo, kontrahentas, kategorija, padalinys, suma, terminas, apmoketa.
Taisyklė: suma > 0 – pajamos, suma < 0 – išlaidos (EUR be PVM).
"""
import json
import unicodedata
from pathlib import Path

import pandas as pd

DUOMENU_APLANKAS = Path(__file__).parent / "duomenys"


def _svarus_pavadinimas(tekstas: str) -> str:
    """Stulpelio pavadinimą paverčia mažosiomis raidėmis be lietuviškų ženklų (pvz. 'Mokėjimo terminas' -> 'mokejimo terminas')."""
    t = unicodedata.normalize("NFD", str(tekstas).strip().lower())
    return "".join(c for c in t if unicodedata.category(c) != "Mn")


def demo_rinkiniai() -> list[dict]:
    """Grąžina pavyzdinių rinkinių sąrašą (pavadinimas, pradinis pinigų likutis, istorija)."""
    return json.loads((DUOMENU_APLANKAS / "rinkiniai.json").read_text(encoding="utf-8"))


def nuskaityti_faila(failas, pavadinimas: str) -> pd.DataFrame:
    """Nuskaito įkeltą failą (Excel arba CSV) ir grąžina sutvarkytą lentelę."""
    if pavadinimas.lower().endswith((".xlsx", ".xls")):
        df = pd.read_excel(failas)
    else:
        # sep=None leidžia automatiškai atpažinti kablelį arba kabliataškį
        df = pd.read_csv(failas, sep=None, engine="python", encoding="utf-8-sig")
    return sutvarkyti(df)


def sutvarkyti(df: pd.DataFrame) -> pd.DataFrame:
    """Suvienodina stulpelius, datas ir sumas, kad toliau analizė visada gautų tą patį formatą."""
    df = df.rename(columns={c: _svarus_pavadinimas(c) for c in df.columns})
    # Leidžiami alternatyvūs stulpelių pavadinimai
    df = df.rename(columns={"aprasymas": "kontrahentas", "padalinys/projektas": "padalinys",
                            "projektas": "padalinys", "mokejimo_terminas": "terminas",
                            "mokejimo terminas": "terminas"})
    if "data" not in df or "suma" not in df:
        raise ValueError("Faile būtini stulpeliai: data ir suma (taip pat rekomenduojami: kontrahentas, kategorija, padalinys).")

    df["data"] = pd.to_datetime(df["data"], errors="coerce", dayfirst=False)
    df["suma"] = pd.to_numeric(df["suma"].astype(str).str.replace(" ", "").str.replace(",", "."), errors="coerce")
    df = df.dropna(subset=["data", "suma"])

    # Jei yra stulpelis 'tipas' (Pajamos/Išlaidos), ženklą nustatome pagal jį
    if "tipas" in df:
        islaidos = df["tipas"].astype(str).str.lower().str.startswith(("išl", "isl"))
        df["suma"] = df["suma"].abs().where(~islaidos, -df["suma"].abs())

    df["kontrahentas"] = df.get("kontrahentas", "—")
    df["kategorija"] = df.get("kategorija", pd.Series(["Pardavimai" if s > 0 else "Kitos" for s in df["suma"]], index=df.index))
    df["padalinys"] = df.get("padalinys", "Bendra")
    df["terminas"] = pd.to_datetime(df.get("terminas", df["data"]), errors="coerce").fillna(df["data"])
    df["apmoketa"] = df.get("apmoketa", "Taip").astype(str).str.strip().str.capitalize()
    df["menuo"] = df["data"].dt.to_period("M")
    return df[["data", "menuo", "kontrahentas", "kategorija", "padalinys", "suma", "terminas", "apmoketa"]].sort_values("data")


def ikelti_demo(rinkinio_id: str) -> pd.DataFrame:
    """Įkelia vieną iš pavyzdinių rinkinių iš aplanko duomenys/."""
    return nuskaityti_faila(DUOMENU_APLANKAS / f"pavyzdys_{rinkinio_id}.xlsx", "x.xlsx")
