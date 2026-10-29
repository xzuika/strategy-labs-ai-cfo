"""3 žingsnis: pinigų srautų prognozė 6 mėnesiams su „O kas, jei?“ scenarijais.

Logika paprasta ir paaiškinama:
- pajamos = vidutinės mėnesio pajamos × sezoniškumas (tas pats mėnuo pernai) × (1 + kainų pokytis);
- tiesioginės sąnaudos kinta proporcingai pajamoms (paskutinių 3 mėn. santykis);
- pastovios sąnaudos = paskutinių 3 mėn. vidurkis;
- ilgesnis apmokėjimo terminas klientams atitolina pinigų gavimą;
- vienkartinė investicija sumažina pinigus pasirinktą mėnesį.
"""
import pandas as pd

from analize import Analize


def prognozuoti(a: Analize, kainu_pokytis=0.0, sanaudu_pokytis=0.0,
                investicija=0.0, investicijos_men=1, terminas_d=0, menesiu=6) -> pd.DataFrame:
    m = a.menesiai
    vid_pajamos = m.pajamos.mean()
    p3 = m.tail(3)
    tiesiog_santykis = p3.tiesiogines.sum() / p3.pajamos.sum()
    pastovios = (p3.visos_sanaudos - p3.tiesiogines + p3.ne_veiklos).mean()

    velavimas = terminas_d / 30          # kiek mėnesių vėliau ateina pinigai
    pinigai = a.pinigai_pabaigoje
    eil = []
    for i in range(1, menesiu + 1):
        men = m.index[-1] + i
        pernai = m[m.index.month == men.month]
        sezonas = pernai.pajamos.iloc[-1] / vid_pajamos if len(pernai) else 1.0
        pajamos = vid_pajamos * sezonas * (1 + kainu_pokytis)
        sanaudos = (vid_pajamos * sezonas * tiesiog_santykis + pastovios) * (1 + sanaudu_pokytis)

        # Apmokėjimo terminas: pirmus mėnesius dalis pajamų dar negaunama
        if i <= int(velavimas):
            gauta = 0.0
        elif i == int(velavimas) + 1:
            gauta = pajamos * (1 - (velavimas - int(velavimas)))
        else:
            gauta = pajamos
        pinigai += gauta - sanaudos - (investicija if i == investicijos_men else 0)
        eil.append({"menuo": men, "pajamos": pajamos, "sanaudos": sanaudos, "pinigai": pinigai})
    return pd.DataFrame(eil).set_index("menuo")
