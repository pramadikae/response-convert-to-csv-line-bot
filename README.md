# Line Bot dengan Integrasi CSV dan Google Drive

Bot Line ini dapat menerima permintaan pengguna, memproses permintaan melalui Dify API (menggunakan model Gemini), dan mengirimkan file CSV melalui Google Drive jika diperlukan.

## Setup

### 1. Instal Dependensi

```bash
pip install -r requirements.txt
```

### 2. Setup Google Drive API

1. Buat project di Google Cloud Console
2. Aktifkan Google Drive API
3. Buat Service Account dan download credentials.json
4. Letakkan file credentials.json di direktori yang sama dengan app.py
5. Buat folder di Google Drive untuk menyimpan file CSV dan catat ID folder tersebut

### 3. Setup Line Messaging API

1. Buat akun Line Developer dan buat Provider
2. Buat Channel untuk Messaging API
3. Dapatkan Channel Secret dan Channel Access Token

### 4. Setup Dify

1. Pastikan Anda memiliki aplikasi di Dify yang menggunakan model Gemini
2. Dapatkan API Key dari Dify
3. Catat endpoint API (biasanya: https://api.dify.ai/v1/chat-messages)

### 5. Setup Environment Variables

Anda perlu mengatur variabel lingkungan dengan salah satu dari dua cara:

#### A. Menggunakan file .env

1. Salin template env.template menjadi .env:
```bash
cp env.template .env
```

2. Edit file .env dan isi dengan nilai yang sesuai:
```
LINE_CHANNEL_SECRET=your_line_channel_secret
LINE_CHANNEL_ACCESS_TOKEN=your_line_channel_access_token
DIFY_API_KEY=your_dify_api_key
DIFY_API_ENDPOINT=https://api.dify.ai/v1/chat-messages
GOOGLE_DRIVE_FOLDER_ID=your_google_drive_folder_id
```

#### B. Mengatur variabel lingkungan secara langsung

Atur variabel berikut di sistem Anda:
```
LINE_CHANNEL_SECRET=your_line_channel_secret
LINE_CHANNEL_ACCESS_TOKEN=your_line_channel_access_token
DIFY_API_KEY=your_dify_api_key
DIFY_API_ENDPOINT=your_dify_api_endpoint
GOOGLE_DRIVE_FOLDER_ID=your_google_drive_folder_id
```

### 6. Menjalankan Aplikasi

```bash
python app.py
```

### 7. Setup Webhook URL

1. Gunakan tool seperti ngrok untuk membuat public URL: `ngrok http 5000`
2. Atur Webhook URL di Line Developer Console: `https://your-ngrok-url/callback`

## Cara Penggunaan

1. Tambahkan bot Line Anda sebagai teman
2. Kirim pesan berupa pertanyaan data, contoh:
   - "Berikan nilai matematika kelas 7"
   - "Tampilkan daftar nilai ulangan siswa"
   - "Daftar siswa dengan nilai tertinggi"
3. Bot akan merespons dengan:
   - Penjelasan lengkap dari chatbot (AI)
   - Tabel data (jika ada)
   - Link Google Drive untuk mengunduh data dalam format CSV

### Cara Kerja

Bot akan secara otomatis:
1. Mendeteksi jika pesan pengguna meminta data/nilai
2. Meneruskan permintaan ke Dify (yang menggunakan model Gemini)
3. Mendeteksi dan mengekstrak tabel dari respons AI
4. Mengkonversi tabel menjadi file CSV yang terstruktur
5. Mengunggah CSV ke Google Drive dan membagikan link-nya
6. Mengirimkan respons AI lengkap beserta link untuk mengunduh CSV

## Pengujian

### Pengujian Ekstraksi Tabel

Untuk menguji kemampuan bot dalam mengekstrak tabel dari respons teks:

```bash
python test_table_extraction.py sample_dify_response.json
```

Ini akan:
1. Mengekstrak tabel dari respons Dify
2. Membersihkan dan memformat tabel
3. Mengkonversi ke CSV
4. Menyimpan hasilnya ke file temporary

Anda bisa melihat output di terminal untuk memahami proses ekstraksi tabel.

### Pengujian Konversi CSV

Untuk menguji fungsionalitas konversi CSV tanpa perlu menjalankan seluruh aplikasi:

```bash
python test_csv_conversion.py
```

## Catatan Penting

- Bot dirancang untuk mengenali berbagai format tabel, termasuk:
  - Tabel dengan header baris "Daftar Nilai..."
  - Tabel dengan kolom "No", "Nama Siswa", dll.
  - Tabel dengan data numerik (seperti nilai UTS, UAS)

- Bot tetap akan mengirimkan respons teks lengkap dari AI, sehingga pengguna mendapatkan informasi lengkap beserta file CSV untuk data terstruktur.

- Format tabel yang didukung:
  - Tabel terstruktur dengan spasi
  - Tabel Markdown dengan pemisah `|`
  - Tabel berbasis teks biasa

## Troubleshooting

- Jika bot tidak mengenali tabel dalam respons, coba ubah prompt untuk meminta data dalam format tabel yang lebih jelas
- Jika tabel diekstrak tapi formatnya salah, periksa apakah tabel di respons AI memiliki header yang jelas dan konsisten
- Pastikan permintaan yang Anda buat cukup spesifik, misalnya "berikan nilai matematika kelas 7" bukan hanya "berikan nilai"

### Debug Format CSV

Jika Anda mengalami masalah dengan konversi CSV, gunakan utilitas debug khusus:

```bash
python debug_csv.py sample_dify_response.json
```

Utilitas ini akan:
1. Menganalisis format data yang diterima
2. Memeriksa konsistensi jumlah kolom
3. Menampilkan detail tentang masalah yang mungkin terjadi
4. Mencoba mengonversi data ke CSV

Anda juga dapat menguji file teks biasa:

```bash
python debug_csv.py data.txt
```

Output debug akan ditampilkan di terminal dan dapat membantu Anda mengidentifikasi masalah format data.

## Catatan Penting

- Pastikan model AI Anda (Gemini di Dify) dilatih untuk menghasilkan data terstruktur yang dapat dikonversi ke CSV
- Format data CSV yang diharapkan adalah teks yang mengandung koma sebagai pemisah dan baris baru untuk tiap entri
- **PENTING**: Format data harus konsisten! Setiap baris harus memiliki jumlah kolom yang sama dengan header

### Format CSV yang Benar

Contoh format yang benar:
```
Nama,Nilai UTS,Nilai UAS,Nilai Akhir
Ahmad Ramadhan,85,90,87.5
Budi Santoso,78,82,80
```

Pastikan Dify (Gemini) menghasilkan data dengan format yang konsisten seperti ini.

## Troubleshooting

- Jika bot tidak dapat mengirim file CSV, periksa bahwa respons dari Dify berisi data yang terstruktur dengan koma dan baris baru
- Jika link Google Drive tidak berfungsi, periksa izin di Service Account dan folder Google Drive
- **Error "columns passed"**: Ini terjadi karena jumlah kolom di beberapa baris tidak konsisten. Pastikan model AI menghasilkan data di mana setiap baris memiliki jumlah kolom yang sama.

### Mengatasi Error Format CSV

Jika Anda mendapatkan error tentang jumlah kolom, berikut beberapa langkah yang dapat dilakukan:

1. Pastikan Anda memberikan prompt yang jelas ke bot tentang struktur data yang diinginkan. Contoh:
   ```
   Berikan data nilai matematika kelas 7 dalam format CSV dengan kolom: Nama, Nilai UTS, Nilai UAS, Nilai Akhir
   ```

2. Jika Dify (Gemini) tidak konsisten dalam menghasilkan format, Anda dapat mempertimbangkan untuk:
   - Menambahkan instruksi khusus di aplikasi Dify Anda
   - Menggunakan template prompt spesifik
   - Memperbarui model prompt engineering di Dify

3. Uji respons Dify secara langsung sebelum digunakan di Line Bot:
   - Buat permintaan langsung ke Dify API
   - Periksa apakah respons memiliki format CSV yang valid
   - Perbaiki prompt jika respons tidak konsisten 