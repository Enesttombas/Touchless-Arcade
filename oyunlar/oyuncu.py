"""Bütün menü ve oyunlar için tek aday/oyuncu kapısı ve kısa kayıp takibi."""
from types import SimpleNamespace
import numpy as np
from cekirdek import Algi, G, Y
from filtre import NoktaTakip


class OyuncuKapisi:
    def __init__(self, ayar=None):
        self.ayar = ayar or {}
        self.izler = {t: {} for t in ("el", "yuz", "poz")}
        self.sayac = 0
        self.filtre = NoktaTakip()

    @staticmethod
    def _veri(noktalar, tur):
        a = np.array([(p.x * G, p.y * Y, getattr(p, "z", 0) * G) for p in noktalar])
        i, j = {"el": (0, 9), "yuz": (33, 263), "poz": (11, 12)}[tur]
        return a, a[:, :2].mean(axis=0), np.linalg.norm(a[i, :2] - a[j, :2])

    def _neden(self, pts, tur, boy, merkez, skor, gevsek, ayar=None):
        oran = sum(.01 <= p.x <= .99 and .01 <= p.y <= .99 for p in pts) / len(pts)
        esik = ((ayar or {}).get('poz_omuz_min', .060) if tur == 'poz' else (ayar or {}).get('yuz_goz_min', .035) if tur == 'yuz' else .030) * G
        if boy < esik * (.7 if gevsek else 1):
            return "küçük"
        if tur == "poz":
            if sum(getattr(pts[i], "visibility", 0) > .6 and 0 <= pts[i].x <= 1 and 0 <= pts[i].y <= 1 for i in (11, 12, 23, 24)) < 3:
                return "gövde görünmüyor"
        elif oran < ({"el": .6, "yuz": .7}[tur] if gevsek else {"el": .85, "yuz": .9}[tur]):
            return "kare dışında"
        if not gevsek and tur != "poz" and not (.04 * G <= merkez[0] <= .96 * G and .04 * G <= merkez[1] <= Y - .04 * G):
            return "kenarda"
        if tur == "el" and not gevsek and skor < .7:
            return "güven düşük"
        return None

    def suz(self, algi, simdi, kural=None):
        ayar = self.ayar | (kural or {})
        out = Algi()
        out.adaylar, out.redler, out.tahmini = [], [], []
        out.kisi_id = {}
        aktif_filtreler = set()
        for tur, alan, yanlar in (("yuz", "yuzler", ("blend",)), ("poz", "pozlar", ()), ("el", "eller", ("jestler", "el_taraf", "el_skor", "jest_skor"))):
            izler = self.izler[tur]
            tut = .6 if tur == "el" else 1.0
            izler = self.izler[tur] = {k: v for k, v in izler.items() if simdi - v["son"] <= tut}
            bos = set(izler)
            gorulen = set()
            for i, pts in enumerate(getattr(algi, alan)):
                try:
                    a, merkez, boy = self._veri(pts, tur)
                except (IndexError, AttributeError, ValueError):
                    out.redler.append((tur, "eksik noktalar"))
                    continue
                if not np.isfinite(a).all():
                    out.redler.append((tur, "geçersiz noktalar"))
                    continue
                kimlik = min(bos, key=lambda k: np.linalg.norm(merkez - (izler[k]["merkez"] + izler[k]["hiz"] * min(simdi - izler[k]["son"], .2))), default=None)
                if kimlik is not None and (np.linalg.norm(merkez - izler[kimlik]["merkez"]) > max(140, boy * 2) or not .4 <= boy / max(1, izler[kimlik]["boy"]) <= 2.5):
                    kimlik = None
                iz = izler.get(kimlik)
                skorlar = getattr(algi, "el_skor", [])
                skor = skorlar[i] if tur == "el" and i < len(skorlar) else 1.0
                neden = self._neden(pts, tur, boy, merkez, skor, bool(iz and iz["aktif"]), ayar)
                sahibi = None
                if tur == "el":
                    aday_sahipler = [(np.linalg.norm(a[0, :2] - self._veri(p, "poz")[0][j, :2]), "poz", k) for k, p in zip(out.poz_id, out.pozlar) for j in (15, 16)]
                    aday_sahipler += [(np.linalg.norm(a[0, :2] - self._veri(p, "yuz")[1]), "yuz", k) for k, p in zip(out.yuz_id, out.yuzler)]
                    for uzaklik, st, sk in sorted(aday_sahipler):
                        limit = .08 * G if st == "poz" else 3 * self.izler[st][sk]["boy"]
                        if uzaklik <= limit:
                            sahibi = out.kisi_id.get((st, sk), sk)
                            break
                    if ayar.get("el_sahip_sart", True) and (algi.yuzler or algi.pozlar) and sahibi is None and not (iz and iz["aktif"]):
                        neden = "sahipsiz"
                if neden:
                    out.redler.append((tur, neden))
                    if iz and not iz["aktif"]:
                        iz["bas"] = simdi
                    continue
                if kimlik is None:
                    self.sayac += 1
                    kimlik = self.sayac
                    iz = dict(bas=simdi, son=simdi, aktif=False, merkez=merkez, hiz=np.zeros(2), boy=boy, durgun=simdi, blok=-1)
                    izler[kimlik] = iz
                else:
                    bos.remove(kimlik)
                dt = simdi - iz["son"]
                if dt > 0:
                    iz["hiz"] = .5 * iz["hiz"] + .5 * (merkez - iz["merkez"]) / dt
                yan = {ad: (getattr(algi, ad)[i] if i < len(getattr(algi, ad)) else ({} if ad == "blend" else None)) for ad in yanlar}
                if tur == "yuz":
                    degisim = np.linalg.norm(merkez - iz["merkez"])
                    if degisim >= .002 * G or yan.get("blend", {}) != iz.get("yan", {}).get("blend", {}):
                        iz["durgun"] = simdi
                    if simdi >= iz["blok"] and simdi - iz["durgun"] >= 8:
                        iz["blok"], iz["durgun"] = simdi + 30, simdi
                iz.update(son=simdi, merkez=merkez, boy=boy, pts=pts, yan=yan, sahibi=sahibi)
                iz["aktif"] |= simdi - iz["bas"] >= {"el": .35, "yuz": .30, "poz": .40}[tur]
                gorulen.add(kimlik)
            ids = []
            for kimlik, iz in izler.items():
                if not iz["aktif"]:
                    if kimlik in gorulen:
                        out.adaylar.append((tur, kimlik, iz["merkez"], simdi - iz["bas"]))
                    else:
                        iz["bas"] = simdi
                    continue
                if tur == "yuz" and simdi < iz["blok"]:
                    out.redler.append((tur, "durgun"))
                    continue
                tahmin = kimlik not in gorulen
                a, _, _ = self._veri(iz["pts"], tur)
                if not tahmin:
                    a = self.filtre.suz((tur, kimlik), a, simdi)
                pts = [SimpleNamespace(x=q[0] / G, y=q[1] / Y, z=q[2] / G, visibility=getattr(p, "visibility", 1)) for q, p in zip(a, iz["pts"])]
                getattr(out, alan).append(pts)
                for ad in yanlar:
                    getattr(out, ad).append(iz["yan"][ad])
                ids.append(kimlik)
                out.kisi_id[(tur, kimlik)] = iz["sahibi"] or kimlik
                if tahmin:
                    out.tahmini.append((tur, kimlik))
                aktif_filtreler.add((tur, kimlik))
            setattr(out, tur + "_id", ids)
        self.filtre.temizle(aktif_filtreler)
        return out
