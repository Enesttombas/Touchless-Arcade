# Stant kablolu kurulum (Ana Bilgisayar ⇄ Stant Terminali, doğrudan Ethernet)

Ana bilgisayar `<LAPTOP_IP>` (ör. `192.168.77.1`), stant terminali `<BOOTH_HOST_IP>` (ör. `192.168.77.2`), ağ geçidi yok (internet ana bilgisayarda Wi-Fi'dan devam eder).
Standart RJ45 Ethernet kablosu yeterlidir; çapraz kablo gerekmez.
Ekran: ana bilgisayar Sunshine → stant terminali Moonlight (1080p60, 20 Mbps). Kamera: terminal kamerası → `kamera_kopru.py` TCP :`<PORT>` (varsayılan 8090) → ana bilgisayar.

Eski terminal kurulum betikleri örnek `192.168.77.*` adreslerini kullanır. `<...>` işaretleri bu belgedeki yer tutuculardır; betikler bunları otomatik istemez. Farklı bir ağda kullanmadan önce betiklerin ağ ve eşleştirme ayarlarını operatörün yapılandırması gerekir.

## Bir kez: Terminal ilk kurulumu (USB ile)
1. USB belleğe bir klasör açın. İçine `kurulum/` altındaki dosyaları ve `prototipler/kamera_kopru.py`'yi kopyalayın.
2. Kabloyu takın. Terminalde USB klasöründeki `HP-KUR.cmd` (veya ilgili terminal kurulum betiği) dosyasına sağ tıklayıp **Yönetici olarak çalıştır** seçin:
   - dosyaları `C:\stand` klasörüne kopyalar, masaüstüne `Stant-HP.bat` kısayolunu koyar;
   - terminale `<BOOTH_HOST_IP>` adresini atar ve `<PORT>` (8090) için yerel güvenlik duvarı kuralı ekler;
   - Python ve OpenCV çalışma ortamını kontrol eder, kamerayı tarar (`C:\stand\kamera_tara.txt`);
   - Moonlight istemcisini ana bilgisayarla eşler: ana bilgisayarda `https://localhost:47990` açın → PIN ekranına terminaldeki `<PAIRING_PIN>` kodunu girin (operatör tarafından Sunshine arayüzünde üretilir).
   - Ağ bağdaştırıcısının adı standart "Ethernet" değilse betik adları listeler. Doğru adla yeniden çalıştırın: `HP-KUR.cmd "<BAGDASTIRICI_ADI>"`.

## Her gün
1. **Ana Bilgisayar (Laptop/İş İstasyonu):** yönetici PowerShell oturumunda `kurulum\Stant-Laptop.ps1` çalıştırın.
   - İlk çalıştırmada Ethernet arabirimine IP tanımlar ve güvenlik duvarını açar (`ag_kur_laptop.ps1`).
   - Sunshine servisini NVENC P1 ve 1080p60 profiline ayarlar (`sunshine.conf.stant-yedek` yedeği alır) ve başlatır.
   - Terminal kamerasını 90 saniye boyunca bekler, ardından uygulamayı `KAMERA=tcp://<BOOTH_HOST_IP>:8090` parametresiyle başlatır.
2. **Stant Terminali:** masaüstündeki `Stant-HP.bat` kısayoluna çift tıklayın. Kamera köprüsü küçük pencerede açılır
   (log: `C:\stand\kopru.log`), ardından Moonlight tam ekran görüntüleme moduna geçer.

## Sorun olursa
| Belirti | Bak |
|---|---|
| `Stant-HP.bat`: "Laptop yanıt vermiyor" | Ethernet kablosu takılı mı? Ana bilgisayarda `Stant-Laptop.ps1` çalıştırıldı mı? |
| Ana bilgisayar 90 sn içinde kamerayı bulamadı | Terminal `C:\stand\kopru.log`. Kamerayı başka bir uygulama kullanıyorsa (Windows Kamera, eski servisler), kapatılmalıdır. |
| Moonlight "eşleşmemiş" uyarısı veriyor | Terminalde `Moonlight.exe pair <LAPTOP_IP> --pin <PAIRING_PIN>` komutunu çalıştırın ve ana bilgisayarda Sunshine web arayüzünde onaylayın. |
| Görüntü çözünürlüğü beklenen değerde değil | Sunshine web arayüzü → Audio/Video: çıkış ekranı ve çözünürlük ayarlarını kontrol edin. |

## Notlar
- Güvenlik duvarı kuralları yalnızca `<BOOTH_HOST_IP>` adresinden gelen Sunshine ve `<PORT>` (8090) trafiğine izin verecek şekilde yapılandırılmalıdır. Dışarıdan bağlanan başka bir servis varsa (ör. Tailscale üzerinden SSH/RDP), kuralları ayrıca tanımlanmalıdır.
- Görüntü hiçbir aşamada diske yazılmaz. Kamera köprüsü belleği tek kareliktir ve kuyruk biriktirmez.
