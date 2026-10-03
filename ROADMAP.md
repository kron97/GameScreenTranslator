# 💡 Roadmap & Rencana Fitur Pengembangan GameScreenTranslator

Dokumen ini mencatat ide-ide dan status implementasi untuk pembaruan (*updates*) **GameScreenTranslator**.

---

## 🚀 1. Akselerasi Kecepatan Penerjemahan (Memangkas Delay) - ✅ SELESAI & IMPLEMENTED

### Status
**SELESAI (Completed)** - Seluruh strategi optimasi latensi telah diterapkan pada `ocr_engine.py` dan `translation_cache.py`.

### Fitur yang Telah Diimplementasikan
* ✅ **0ms Image Hash Diffing (`compute_image_dhash`)**:
  - Menggunakan algoritma *dhash* (difference hash) 64-bit pada area subtitle.
  - Jika piksel layar tidak berubah (scene diam atau dialog belum berganti), aplikasi secara instant melewati (*skip*) proses OCR & HTTP request (0ms CPU delay).
* ✅ **Local SQLite Translation Cache (`TranslationCache`)**:
  - Menyimpan otomatis hasil terjemahan ke database SQLite lokal `translation_cache.db`.
  - Frasa atau dialog yang sudah pernah muncul langsung tampil **0ms instan tanpa kuota & tanpa internet**.
* ✅ **HTTP Connection Pooling (`requests.Session`)**:
  - Menggunakan *persistent Keep-Alive* HTTP Session untuk memangkas overhead TLS handshake (menghemat ~150-300ms per request ke DeepL & Google GTX).
* ✅ **Integrasi DeepL Free/Pro API**:
  - Dukungan penuh untuk DeepL API Key dengan fallback gratis otomatis ke Google GTX.

---

## 📌 2. Fitur Berjalan di Background System Tray (Minimize to Tray) - ⏳ SELANJUTNYA

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

## ⌨️ 3. Global Hotkey yang Dapat Dikonfigurasi (Customizable Hotkey) - ⏳ AKAN DATANG

### Solusi Teknis
* **Pengaturan Tombol Pintas via UI**:
  - Menambahkan widget pemilih tombol pintas (`QKeySequenceEdit`) pada panel pengaturan.
  - Pengguna bebas memilih tombol pintas sesuai keinginan (misal: `F9`, `F10`, `Ctrl + Shift + T`, `Alt + Z`).
* **Penyimpanan di `config.json`**:
  - Kode Virtual Key (`vk_code`) tombol yang dipilih pengguna tersimpan secara permanen di file konfigurasi.
* **Thread Hook Bebas Crash**:
  - Penggunaan *listener thread* yang terisolasi dari *main GUI event loop* untuk menjamin tombol pintar merespons instan di dalam game apapun tanpa menyebabkan *freeze* / *Not Responding*.

---

*Catatan: Dokumen ini diperbarui seiring berjalannya pengembangan proyek.*
