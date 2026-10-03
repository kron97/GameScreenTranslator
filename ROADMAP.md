# 💡 Roadmap & Rencana Fitur Pengembangan GameScreenTranslator

Dokumen ini mencatat ide-ide dan strategi teknis untuk pembaruan (*updates*) versi **GameScreenTranslator** selanjutnya.

---

## 🚀 1. Akselerasi Kecepatan Penerjemahan (Memangkas Delay)

### Masalah Saat Ini
Proses pemindaian OCR dan panggilan HTTP API terjemahan Google GTX memerlukan waktu ~0.8s - 1.5s per kalimat.

### Strategi & Solusi Teknis
* **Image Hash Diffing (Deteksi Perubahan Subtitle)**:
  - Sebelum menjalankan OCR, lakukan komparasi *perceptual hash* (`dhash`/`phash`) pada area subtitle.
  - Jika piksel tidak berubah (scene diam atau dialog belum berganti), batalkan OCR & HTTP request secara instant (0ms CPU delay).
* **Caching Terjemahan Lokal (Dictionary LRU Cache)**:
  - Simpan frasa/kalimat yang sudah pernah diterjemahkan ke dalam memori *cache* atau database SQLite lokal.
  - Kalimat yang sering berulang (seperti *"Yes"*, *"No"*, *"Press Space to continue"*, dialog berulang) akan langsung tampil 0ms tanpa menunggu koneksi internet.
* **HTTP Connection Pooling (`requests.Session`)**:
  - Gunakan koneksi *persistent Keep-Alive* HTTP Session agar tidak membuka TLS handshake baru setiap kali terjemahan dikirim.
* **Opsional: Offline NMT Engine**:
  - Riset integrasi model terjemahan offline ringan (*CTranslate2* / *MarianMT*) untuk opsi penerjemahan tanpa internet dengan latensi ultra-rendah.

---

## 📌 2. Fitur Berjalan di Background System Tray (Minimize to Tray)

### Solusi Teknis
* **`QSystemTrayIcon` PyQt6**:
  - Menambahkan ikon **GameTranslator ID** di *System Tray* Windows (di sebelah jam taskbar).
* **Menu Kustom System Tray**:
  - Klik kanan pada ikon tray:
    - 🟢 *Mulai / Jeda Terjemahan*
    - ⚙️ *Tampilkan Panel Utama*
    - ❌ *Keluar dari Aplikasi*
* **Minimize ke Tray**:
  - Saat tombol silang `[X]` diklik, aplikasi menyembunyikan jendela utama ke tray agar tidak mengotori *taskbar* Windows saat Anda fokus bermain game.

---

## ⌨️ 3. Global Hotkey yang Dapat Dikonfigurasi (Customizable Hotkey)

### Solusi Teknis
* **Pengaturan Tombol Pintas via UI**:
  - Menambahkan widget pemilih tombol pintas (`QKeySequenceEdit`) pada panel pengaturan.
  - Pengguna bebas memilih tombol pintas sesuai keinginan (misal: `F9`, `F10`, `Ctrl + Shift + T`, `Alt + Z`).
* **Penyimpanan di `config.json`**:
  - Kode Virtual Key (`vk_code`) tombol yang dipilih pengguna tersimpan secara permanen di file konfigurasi.
* **Thread Hook Bebas Crash**:
  - Penggunaan *listener thread* yang terisolasi dari *main GUI event loop* untuk menjamin tombol pintar merespons instan di dalam game apapun tanpa menyebabkan *freeze* / *Not Responding*.

---

*Catatan: Dokumen ini akan diperbarui seiring berjalannya pengembangan proyek.*
