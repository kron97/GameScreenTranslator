# 🎮 GameTranslator ID - Panduan Penggunaan Aplikasi

Aplikasi **GameTranslator ID** dibuat khusus untuk memungkinkan Anda bermain video game dalam **Bahasa Indonesia** secara *real-time* tanpa perlu menginstal mod game! Aplikasi ini membaca teks subtitle pada layar game menggunakan OCR (*Optical Character Recognition*) dan menampilkan terjemahannya di jendela subtitle melayang (*overlay*) di atas layar game Anda.

---

## 🚀 Fitur Utama

1. **Tanpa Mod Game**: Tidak perlu membongkar file game atau khawatir risiko banned/error.
2. **Dukungan Model AI Lokal Qwen 2.5 3B (Offline LLM)**:
   - 🧠 **Qwen 2.5 3B Local LLM via Ollama**: Menerjemahkan dialog game secara **100% offline & pintar memahami konteks/jargon game** menggunakan AI lokal di PC Anda.
   - ⚡ **0ms Local Cache**: Frasa/kalimat yang sudah pernah diterjemahkan atau sering muncul otomatis tersimpan di database SQLite lokal. Saat kalimat tersebut muncul kembali, hasil terjemahan langsung tampil **0 milidetik (tanpa delay & tanpa kuota internet)**!
   - 🚀 **DeepL API Integration**: Terjemahan kalimat baru menggunakan DeepL untuk hasil yang **sangat natural, akurat, dan halus**.
   - 🌐 **Google GTX Fallback**: Penggunaan gratis tanpa kuota jika tanpa API Key.
3. **3 Modus Deteksi Tangkapan Layar (Capture Mode)**:
   - 🎯 **Area Spesifik**: Pilih area kotak subtitle secara manual dengan alat *snip* visual.
   - 🤖 **Auto Subtitle Zone**: Otomatis memindai area 30% bawah tengah layar tempat subtitle game umumnya berada.
   - 🌐 **Deteksi Otomatis Seluruh Layar**: Otomatis memindai teks dialog di seluruh layar game dengan penyaringan pintar.
4. **Overlay Subtitle 100% Transparan & Bening**:
   - Opsi tampilan **Bening / Tanpa Latar Belakang** (hanya teks terjemahan melayang di atas game).
   - Pengaturan opasitas latar belakang fleksibel (Bening 0%, Redup 40%, Gelap Pekat 80%, atau Slider Kustom 0-100%).
   - Dilengkapi garis tepi (*outline*) 360° yang tajam agar teks selalu mudah dibaca di *scene* terang maupun gelap.
   - **Auto-Expanding Height**: Tinggi kotak subtitle menyesuaikan secara otomatis ke bawah jika teks dialog panjang (multi-baris) sehingga teks tidak pernah terpotong.
5. **Pembersihan Teks Instan**: Teks subtitle melayang dan cache OCR otomatis dibersihkan seketika begitu terjemahan di-pause/diberhentikan.
6. **Dua Mesin OCR Berkecepatan Tinggi**:
   - **Windows Native OCR**: Sangat cepat, ringan, dan menggunakan fitur OCR bawaan Windows 10/11.
   - **RapidOCR**: Mesin OCR offline berbasis model ONNX untuk akurasi tinggi.
7. **Kustomisasi Tampilan Subtitle**:
   - Sesuaikan ukuran font (14pt - 48pt).
   - Pilih warna teks (Kuning Subtitle `#FFD700`, Putih Bersih `#FFFFFF`, Hijau Cyan `#00E676`, Kuning Cerah `#FFFF00`).
   - Ketebalan outline dapat disesuaikan.
8. **Bilah Judul Terkunci (Lock Position)**:
   - Kunci posisi overlay agar tidak mengganggu klik mouse saat bermain game.
   - Fitur menyembunyikan bilah judul (*header bar*) saat terkunci agar layar game 100% bersih.

---

## 🛠️ Cara Menggunakan Aplikasi

### Langkah 1: Jalankan Game & Aplikasi
1. Buka game yang ingin Anda mainkan. Disarankan mengatur game ke mode **Borderless Windowed** atau **Windowed Mode** agar aplikasi penerjemah dapat tampil mulus di atas layar game.
2. Buka folder aplikasi dan klik ganda **`Buka_GameTranslator.vbs`** (atau `Buka_GameTranslator.bat`).

### Langkah 2: Pilih Modus Deteksi Subtitle & Mesin Penerjemah
1. Di panel kontrol utama (bagian **1. Modus Tangkapan Layar**), pilih modus deteksi (misal: *🎯 Area Spesifik* atau *🤖 Auto Subtitle Zone*).
2. Di bagian **4. Pengaturan Bahasa & Mesin OCR**:
   - Pilih Mesin Penerjemah: **🧠 Qwen 2.5 3B (Local LLM Offline - Ollama)**, **🌐 Google GTX**, atau **🚀 DeepL API**.

### Langkah 3: Atur Tampilan Subtitle (Opsional)
- **Model Latar**: Pilih **👻 Bening / Tanpa Latar** jika Anda ingin teks melayang tanpa kotak background.
- **Ukuran & Warna Font**: Sesuaikan ukuran font dan warna yang paling nyaman untuk mata Anda.
- **Atur Posisi Overlay**: Geser kotak subtitle melayang ke posisi yang pas di layar game Anda, lalu klik **`🔒 Kunci / Buka Posisi`**.

### Langkah 4: Mulai Penerjemahan
1. Klik tombol hijau **`▶ MULAI MENTERJEMAHKAN`**.
2. Kembali ke game Anda dan nikmati dialog game dalam **Bahasa Indonesia**!
3. Jika ingin menghentikan penerjemahan, cukup klik **`⏹ HENTIKAN TERJEMAHAN`**. Teks subtitle di layar akan langsung dibersihkan.

---

## 📂 Berkas Peluncur (Launcher Files)

| Nama Berkas | Fungsi |
| :--- | :--- |
| **`Buka_GameTranslator.vbs`** | **[Direkomendasikan]** Buka aplikasi secara bersih tanpa jendela konsol CMD. |
| **`Buka_GameTranslator.bat`** | Peluncur standar Windows batch. |
| **`Buka_GameTranslator_Debug.bat`** | Peluncur mode debug (menampilkan log terminal jika ingin memeriksa error). |

---

*GameTranslator ID - Dibuat untuk Pengalaman Bermain Game Terbaik dalam Bahasa Indonesia.*
