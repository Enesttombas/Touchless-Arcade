# Stant Kamera Oyunları

Kulüp standı için kamerayla oynanan Python oyunları (MediaPipe + OpenCV). Menü `prototipler/stant_app.py`,
başlatıcı `Stant.exe` (kaynağı `kurulum/StantLauncher.cs`).

Menüde 11 oyun var; yeni ikisi **İşlem Dizisi** ve **Cümle Dizisi** (hoca isteği, şartname
`codex/12-OYUN-INSAN-DIZISI.md`).

## Yeni bilgisayarda kurulum (Windows)
1. Python **3.11** kur (python.org, kurulumda "py launcher" açık).
2. Bu klasörde `KUR.bat` çalıştır (internet gerekir, ~1 GB indirir, bir kez).
3. `Stant.exe` ile aç. Klasörün yeri önemli değil ama `Stant.exe` kök klasörde kalmalı.

Kamera: `KAMERA` ortam değişkeni verilmezse başlatıcı laptop kamerasını seçer. HP + laptop kablolu kurulum: `kurulum/README.md`.

## Test
```
app\.venv\Scripts\python.exe -m pytest -q kabul_prototip -p no:cacheprovider
```

## Durum
İşlem Dizisi / Cümle Dizisi: otomatik kabul yeşil; gerçek kamerayla 3–5 kişilik saha kabulü bekliyor
(`codex/DIZI-OLCUM.md`). Cümle bankası Enes onayı bekliyor (`prototipler/veri/dizi_cumleler_inceleme.md`).

Gizlilik: ziyaretçi görüntüsü diske yazılmaz.
