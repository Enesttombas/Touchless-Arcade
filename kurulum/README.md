# Stant kablolu kurulum (laptop ⇄ HP 440 G3, doğrudan Ethernet)

Laptop `192.168.77.1`, HP `192.168.77.2`, ağ geçidi yok (internet laptopta Wi-Fi'dan devam eder).
Standart RJ45 Ethernet kablosu yeter; çapraz kablo gerekmez.
Ekran: laptop Sunshine → HP Moonlight (1080p60, 20 Mbps). Kamera: HP kamerası → `kamera_kopru.py` TCP :8090 → laptop.

## Bir kez: HP ilk kurulum (USB ile)
1. USB'ye bir klasör aç. İçine `kurulum/` altındaki her şeyi ve `prototipler/kamera_kopru.py`'yi kopyala.
2. Kabloyu tak. HP'de USB klasöründeki `HP-KUR.cmd` dosyasına sağ tıkla, **Yönetici olarak çalıştır**:
   - dosyaları `C:\stand`'e kopyalar, masaüstüne `Stant-HP.bat` koyar;
   - HP'ye 192.168.77.2 adresini verir, 8090 için güvenlik duvarı kuralı ekler;
   - Python ve OpenCV'yi kontrol eder, kamerayı tarar (`C:\stand\kamera_tara.txt`);
   - Moonlight'ı laptopla eşler: laptopta `https://localhost:47990` → PIN → `4821`.
   - Bağdaştırıcının adı "Ethernet" değilse betik adları listeler. Doğru adla yeniden çalıştır: `HP-KUR.cmd "Ad"`.

## Her gün
1. **Laptop:** yönetici PowerShell'de `kurulum\Stant-Laptop.ps1` çalıştır.
   - İlk çalıştırmada Ethernet'e IP verir ve güvenlik duvarını açar (`ag_kur_laptop.ps1`).
   - Sunshine'ı NVENC P1 ve 1080p60'a ayarlar (`sunshine.conf.stant-yedek` yedeğini bir kez alır) ve başlatır.
   - HP kamerasını 90 sn bekler, sonra `Stant.exe`'yi `KAMERA=tcp://192.168.77.2:8090` ile açar.
2. **HP:** masaüstündeki `Stant-HP.bat`'e çift tıkla. Kamera köprüsü küçük pencerede açılır
   (log: `C:\stand\kopru.log`), ardından Moonlight tam ekran gelir.

## Sorun olursa
| Belirti | Bak |
|---|---|
| `Stant-HP.bat`: "Laptop yanıt vermiyor" | Kablo takılı mı? Laptopta `Stant-Laptop.ps1` çalıştı mı? |
| Laptop 90 sn'de kamerayı bulamadı | HP `C:\stand\kopru.log`. Kamerayı başka uygulama tutuyorsa (Kamera uygulaması, eski `kamera_yayin.py`), betik bunları kapatır. |
| Moonlight "eşleşmemiş" diyor | HP'de `Moonlight.exe pair 192.168.77.1 --pin 4821` + laptopta Sunshine web arayüzünde PIN |
| Görüntü 1080p değil | Sunshine web arayüzü → Audio/Video: çıkış ekranı ve çözünürlük |

## Notlar
- Laptop güvenlik duvarı şu an üç profilde kapalı. `ag_kur_laptop.ps1` hepsini açar ve yalnız
  192.168.77.2'den gelen Sunshine ve 8090 trafiğine izin verir. Laptopa dışarıdan bağlanan başka bir
  hizmet varsa (ör. Tailscale üzerinden SSH/RDP), onun kuralı ayrıca gerekir.
- Bu betikler kablo takılmadan çalıştırılmadı. Laptopta yalnız kuru deneme yapıldı (Stant-HP.bat
  ping adımına kadar). Gecikme ölçümü: `../codex/OLCUM-PROTOKOLU.md`.
- Görüntü diske yazılmaz. Köprü belleği tek kareliktir, kuyruk tutmaz.
