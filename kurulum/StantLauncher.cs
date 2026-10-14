// Stant.exe başlatıcısı. Derleme: kurulum\stant-exe-derle.ps1
// Tek kopya: açılırken önceki Stant.exe ve stant_app.py süreçlerini (ağacıyla) kapatır; böylece
// eski sürüm arkada tam ekranda kalıp kamerayı tutmaz (Enes 2026-10-13: "gereksiz exeler açılıyor").
using System;
using System.Diagnostics;
using System.IO;
using System.Management;
using System.Windows.Forms;

namespace MemeKamera
{
    static class StantLauncher
    {
        static readonly object Kilit = new object();
        static StreamWriter log;

        static void Yaz(string s)
        {
            lock (Kilit) { try { log.WriteLine(s); log.Flush(); } catch { } }
        }

        static void Oldur(int pid)
        {
            try
            {
                var p = Process.Start(new ProcessStartInfo("taskkill", "/PID " + pid + " /T /F")
                { CreateNoWindow = true, UseShellExecute = false });
                p.WaitForExit(5000);
            }
            catch { }
        }

        static void EskileriKapat()
        {
            int ben = Process.GetCurrentProcess().Id;
            foreach (var p in Process.GetProcessesByName("Stant"))
                if (p.Id != ben) { Yaz("Eski Stant.exe kapatildi: " + p.Id); Oldur(p.Id); }
            try
            {
                var ara = new ManagementObjectSearcher(
                    "SELECT ProcessId, CommandLine FROM Win32_Process WHERE Name = 'python.exe'");
                foreach (ManagementObject m in ara.Get())
                {
                    var cmd = (m["CommandLine"] as string) ?? "";
                    if (cmd.IndexOf("stant_app.py", StringComparison.OrdinalIgnoreCase) >= 0)
                    {
                        int pid = Convert.ToInt32(m["ProcessId"]);
                        Yaz("Eski stant_app kapatildi: " + pid);
                        Oldur(pid);
                    }
                }
            }
            catch (Exception e) { Yaz("WMI taramasi yapilamadi: " + e.Message); }
        }

        static bool HpKameraAcik()
        {
            for (int i = 0; i < 3; i++)  // köprü yeni açılıyorsa ~4,5 sn bekler
            {
                try
                {
                    using (var c = new System.Net.Sockets.TcpClient())
                        if (c.ConnectAsync("192.168.77.2", 8090).Wait(1500) && c.Connected) return true;
                }
                catch { }
            }
            return false;
        }

        [STAThread]
        static int Main()
        {
            string klasor = Path.Combine(Environment.GetEnvironmentVariable("LOCALAPPDATA"), "MemeKamera");
            Directory.CreateDirectory(klasor);
            string logYol = Path.Combine(klasor, "stant.log");
            try { if (File.Exists(logYol) && new FileInfo(logYol).Length > 2000000) File.Delete(logYol); } catch { }
            try  // eski kopya log'u açık tutarken de açılabilsin (paylaşımlı); olmazsa log'suz devam
            {
                log = new StreamWriter(new FileStream(logYol, FileMode.Append, FileAccess.Write,
                    FileShare.ReadWrite | FileShare.Delete));
            }
            catch { log = StreamWriter.Null; }
            Yaz(string.Format("--- Baslatma: {0:yyyy-MM-dd HH:mm:ss} ---", DateTime.Now));
            try
            {
                EskileriKapat();
                string kok = AppDomain.CurrentDomain.BaseDirectory;
                string py = Path.Combine(kok, "app", ".venv", "Scripts", "python.exe");
                string betik = Path.Combine(kok, "prototipler", "stant_app.py");
                if (!File.Exists(py) || !File.Exists(betik))
                {
                    string eksik = File.Exists(py) ? betik : py;
                    Yaz("HATA: bulunamadi: " + eksik);
                    MessageBox.Show("Bulunamadi:\n" + eksik + "\n\nDetaylar icin log dosyasi:\n" + logYol, "Hata");
                    return 1;
                }
                var bilgi = new ProcessStartInfo(py, "\"" + betik + "\"")
                {
                    WorkingDirectory = Path.Combine(kok, "prototipler"),
                    UseShellExecute = false, CreateNoWindow = true,
                    RedirectStandardOutput = true, RedirectStandardError = true
                };
                // KAMERA verilmemişse: kablodaki HP kamera köprüsü açıksa onu, değilse laptop kamerasını kullan
                if (string.IsNullOrEmpty(Environment.GetEnvironmentVariable("KAMERA")))
                {
                    string kamera = HpKameraAcik() ? "tcp://192.168.77.2:8090" : "1";
                    bilgi.EnvironmentVariables["KAMERA"] = kamera;
                    Yaz("KAMERA=" + kamera);
                }
                bilgi.EnvironmentVariables["TAM_EKRAN"] = "1";
                bilgi.EnvironmentVariables["PYTHONUNBUFFERED"] = "1";
                var surec = new Process { StartInfo = bilgi };
                surec.OutputDataReceived += (s, e) => { if (e.Data != null) Yaz("[STDOUT] " + e.Data); };
                surec.ErrorDataReceived += (s, e) => { if (e.Data != null) Yaz("[STDERR] " + e.Data); };
                surec.Start();
                surec.BeginOutputReadLine();
                surec.BeginErrorReadLine();
                surec.WaitForExit();
                Yaz(string.Format("Surec tamamlandi. Cikis kodu: {0}", surec.ExitCode));
                // taskkill ile kapatılan eski kopya (1) uyarı göstermez; yalnız gerçek çökme gösterir
                if (surec.ExitCode != 0 && surec.ExitCode != 1)
                    MessageBox.Show(string.Format("Stant uygulamasi hata ile kapandi (Kod: {0}).\n\nDetaylar icin log dosyasi:\n{1}",
                        surec.ExitCode, logYol), "Hata");
                return surec.ExitCode;
            }
            catch (Exception e)
            {
                Yaz("BEKLENMEYEN HATA: " + e);
                MessageBox.Show("Stant baslatilirken beklenmeyen bir hata olustu:\n" + e.Message +
                    "\n\nDetaylar icin log dosyasi:\n" + logYol, "Hata");
                return 1;
            }
        }
    }
}
