from flask import Flask, request, abort
import os
import json
import tempfile
import pandas as pd
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
import requests
from dotenv import load_dotenv
import logging
import datetime
import re
from io import StringIO

# Setup logging
log_dir = 'logs'
if not os.path.exists(log_dir):
    os.makedirs(log_dir)
log_file = os.path.join(log_dir, f'app_{datetime.datetime.now().strftime("%Y%m%d")}.log')
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Memuat variabel lingkungan dari file .env jika ada
load_dotenv()

app = Flask(__name__)

# Konfigurasi Line Bot
LINE_CHANNEL_SECRET = os.environ.get('LINE_CHANNEL_SECRET', 'your_line_channel_secret')
LINE_CHANNEL_ACCESS_TOKEN = os.environ.get('LINE_CHANNEL_ACCESS_TOKEN', 'your_line_channel_access_token')

line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)

# Konfigurasi Dify API
DIFY_API_KEY = os.environ.get('DIFY_API_KEY', 'your_dify_api_key')
DIFY_API_ENDPOINT = os.environ.get('DIFY_API_ENDPOINT', 'https://api.dify.ai/v1/chat-messages')

# Path ke kredensial Google Drive
GOOGLE_DRIVE_CREDENTIALS_FILE = os.environ.get('GOOGLE_DRIVE_CREDENTIALS_FILE', 'credentials.json')
GOOGLE_DRIVE_FOLDER_ID = os.environ.get('GOOGLE_DRIVE_FOLDER_ID', 'your_google_drive_folder_id')


def create_drive_service():
    """Membuat layanan Google Drive API."""
    credentials = service_account.Credentials.from_service_account_file(
        GOOGLE_DRIVE_CREDENTIALS_FILE,
        scopes=['https://www.googleapis.com/auth/drive']
    )
    return build('drive', 'v3', credentials=credentials)


def upload_to_drive(file_path, file_name):
    """Mengunggah file ke Google Drive dan mengembalikan link yang bisa diakses."""
    drive_service = create_drive_service()
    
    file_metadata = {
        'name': file_name,
        'parents': [GOOGLE_DRIVE_FOLDER_ID]
    }
    
    media = MediaFileUpload(file_path, resumable=True)
    file = drive_service.files().create(
        body=file_metadata,
        media_body=media,
        fields='id'
    ).execute()
    
    # Mengatur izin file agar dapat diakses oleh siapa saja dengan link
    drive_service.permissions().create(
        fileId=file.get('id'),
        body={'type': 'anyone', 'role': 'reader'},
        fields='id'
    ).execute()
    
    # Mendapatkan link yang bisa diakses
    file_link = f"https://drive.google.com/file/d/{file.get('id')}/view"
    return file_link


def generate_csv_from_text(text_data, filename="data.csv"):
    """Mengubah data teks menjadi file CSV."""
    try:
        # Parse data dari teks
        lines = text_data.strip().split('\n')
        
        # Cek apakah ada header di baris pertama
        if len(lines) < 2:
            raise ValueError("Data tidak cukup untuk dikonversi ke CSV")
        
        # Deteksi pemisah (koma atau tab)
        header = lines[0]
        delimiter = ',' if ',' in header else '\t'
        
        # Log informasi delimiter
        logger.info(f"Menggunakan delimiter: '{delimiter}' untuk konversi CSV")
        logger.info(f"Header terdeteksi: {header}")
        
        # Siapkan data dengan pemisah yang tepat
        data = []
        for line in lines:
            row = [cell.strip() for cell in line.split(delimiter)]
            data.append(row)
            
        # Hitung jumlah kolom dari header
        header_cols = len(data[0])
        logger.info(f"Jumlah kolom header: {header_cols}")
        
        # Log panjang kolom untuk baris pertama sebagai sampel
        if len(data) > 1:
            logger.info(f"Jumlah kolom baris pertama data: {len(data[1])}")
        
        # Pastikan semua baris memiliki jumlah kolom yang sama
        clean_data = []
        for i, row in enumerate(data):
            original_len = len(row)
            # Sesuaikan panjang baris dengan header
            if len(row) < header_cols:
                # Tambahkan kolom kosong jika kurang
                row.extend([''] * (header_cols - len(row)))
                logger.warning(f"Baris {i+1} memiliki {original_len} kolom (kurang dari {header_cols}). Ditambahkan kolom kosong.")
            elif len(row) > header_cols:
                # Potong jika terlalu panjang
                logger.warning(f"Baris {i+1} memiliki {original_len} kolom (lebih dari {header_cols}). Dipotong.")
                row = row[:header_cols]
            clean_data.append(row)
        
        # Konversi ke DataFrame dan simpan sebagai CSV
        df = pd.DataFrame(clean_data[1:], columns=clean_data[0])
        
        temp_dir = tempfile.gettempdir()
        file_path = os.path.join(temp_dir, filename)
        
        df.to_csv(file_path, index=False)
        logger.info(f"File CSV berhasil dibuat: {file_path}")
        return file_path
    except Exception as e:
        # Tambahkan logging untuk debug
        logger.error(f"Error saat mengonversi teks ke CSV: {str(e)}")
        # Simpan data mentah jika gagal parsing
        temp_dir = tempfile.gettempdir()
        raw_file_path = os.path.join(temp_dir, "raw_" + filename)
        with open(raw_file_path, 'w', encoding='utf-8') as f:
            f.write(text_data)
        logger.info(f"Data mentah disimpan di: {raw_file_path}")
        
        # Coba metode alternatif menggunakan pandas
        try:
            logger.info("Mencoba metode alternatif dengan pandas.read_csv")
            df = pd.read_csv(pd.StringIO(text_data), sep=None, engine='python')
            file_path = os.path.join(temp_dir, filename)
            df.to_csv(file_path, index=False)
            logger.info(f"File CSV berhasil dibuat dengan metode alternatif: {file_path}")
            return file_path
        except Exception as alt_e:
            logger.error(f"Metode alternatif juga gagal: {str(alt_e)}")
            raise ValueError(f"Tidak dapat mengonversi data ke CSV: {str(e)}")


def check_csv_request(user_message):
    """Memeriksa apakah pesan pengguna meminta data yang mungkin berformat tabel."""
    keywords = [
        'nilai', 'data', 'daftar', 'tabel', 'csv', 'file', 
        'export', 'download', 'simpan', 'kirim', 'berikan',
        'matematika', 'kelas', 'siswa', 'murid', 'pelajaran',
        'ulangan', 'ujian', 'uts', 'uas'
    ]
    return any(keyword in user_message.lower() for keyword in keywords)


def get_response_from_dify(user_message):
    """Mendapatkan respons dari API Dify."""
    headers = {
        'Authorization': f'Bearer {DIFY_API_KEY}',
        'Content-Type': 'application/json'
    }
    
    payload = {
        'inputs': {},
        'query': user_message,
        'response_mode': 'blocking',
        'user': 'user-001'
    }
    
    response = requests.post(DIFY_API_ENDPOINT, headers=headers, json=payload)
    
    if response.status_code == 200:
        return response.json()
    else:
        return {'error': f'Failed to get response: {response.status_code}'}


@app.route('/callback', methods=['POST'])
def callback():
    """Callback dari Line."""
    signature = request.headers['X-Line-Signature']
    body = request.get_data(as_text=True)
    
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)
    
    return 'OK'


def extract_table_from_text(text):
    """
    Mengekstrak tabel dari teks respons.
    Mendeteksi tabel berdasarkan pola tertentu.
    """
    logger.info("Mencoba mengekstrak tabel dari respons")
    
    lines = text.strip().split('\n')
    table_start = -1
    table_end = -1
    
    # Deteksi awal tabel
    for i, line in enumerate(lines):
        # Cek jika baris berisi header tabel
        if "Daftar" in line and "Nilai" in line:
            table_start = i
            break
        # Cek pola tabel dengan kolom No dan Nama
        elif re.search(r'No\s+Nama', line, re.IGNORECASE):
            table_start = i
            break
        # Cek jika baris berisi deretan header yang dibatasi |
        elif '|' in line and len(line.split('|')) > 2:
            table_start = i
            break
    
    # Jika tidak menemukan tanda tabel, coba cari pola lainnya
    if table_start == -1:
        for i, line in enumerate(lines):
            # Cari baris dengan beberapa kata yang mungkin jadi header tabel
            if any(keyword in line.lower() for keyword in ["nama", "siswa", "nilai", "uts", "uas", "tugas"]) and any(char.isdigit() for char in line):
                table_start = i
                break
    
    # Jika masih tidak menemukan tabel, kembalikan None
    if table_start == -1:
        logger.warning("Tidak dapat menemukan tabel dalam teks")
        return None
    
    # Mencari akhir tabel
    for i in range(table_start + 1, len(lines)):
        # Jika menemukan baris kosong setelah beberapa baris data
        if not lines[i].strip() and i > table_start + 2:
            table_end = i
            break
        # Jika menemukan baris yang tidak seperti data tabel (tidak ada angka)
        elif i > table_start + 3 and not any(char.isdigit() for char in lines[i]):
            table_end = i
            break
    
    # Jika tidak menemukan akhir tabel, ambil sampai akhir
    if table_end == -1:
        table_end = len(lines)
    
    # Ekstrak tabel
    table_text = '\n'.join(lines[table_start:table_end])
    logger.info(f"Tabel yang diekstrak:\n{table_text}")
    
    return table_text


def clean_table_text(table_text):
    """
    Membersihkan teks tabel dan mengonversinya ke format CSV yang sesuai.
    """
    lines = table_text.strip().split('\n')
    clean_lines = []
    
    # Deteksi delimiter
    first_line = lines[0]
    if '|' in first_line:
        # Format tabel dengan batasan vertikal
        for line in lines:
            # Hapus batasan vertikal dan spasi berlebih
            clean_line = "|".join([cell.strip() for cell in line.split('|')[1:-1] if cell.strip()])
            if clean_line:
                clean_lines.append(clean_line)
        processed_text = '\n'.join(clean_lines)
        delimiter = '|'
    else:
        # Format tabel tanpa batasan vertikal (spasi)
        processed_text = table_text
        delimiter = None  # Akan mengandalkan pandas untuk deteksi otomatis
    
    return processed_text, delimiter


def create_csv_from_table(table_text, filename="data.csv"):
    """
    Membuat file CSV dari teks tabel.
    """
    try:
        if not table_text:
            return None
            
        # Bersihkan tabel
        clean_text, delimiter = clean_table_text(table_text)
        
        # Konversi ke DataFrame berdasarkan delimiter
        if delimiter == '|':
            df = pd.read_csv(StringIO(clean_text), sep='|')
        else:
            # Coba deteksi delimiter otomatis
            df = pd.read_csv(StringIO(clean_text), sep=None, engine='python')
        
        # Simpan ke file CSV
        temp_dir = tempfile.gettempdir()
        file_path = os.path.join(temp_dir, filename)
        df.to_csv(file_path, index=False)
        
        logger.info(f"File CSV berhasil dibuat: {file_path}")
        return file_path
    except Exception as e:
        logger.error(f"Gagal membuat CSV dari tabel: {str(e)}")
        return None


@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    """Menangani pesan dari pengguna."""
    user_message = event.message.text
    user_id = event.source.user_id
    
    logger.info(f"Menerima pesan dari {user_id}: {user_message}")
    
    # Mendapatkan respons dari Dify
    dify_response = get_response_from_dify(user_message)
    
    # Memeriksa apakah pengguna meminta data yang mungkin berisi tabel
    if check_csv_request(user_message) and 'answer' in dify_response:
        logger.info("Permintaan data terdeteksi")
        
        # Ambil respons
        answer = dify_response['answer']
        logger.info(f"Respons dari Dify:\n{answer}")
        
        # Ekstrak tabel dari respons
        table_text = extract_table_from_text(answer)
        
        if table_text:
            # Buat file CSV dari tabel
            csv_file_path = create_csv_from_table(table_text, f"data_requested_by_{user_id}.csv")
            
            if csv_file_path:
                # Upload ke Google Drive
                logger.info(f"Mengunggah file {csv_file_path} ke Google Drive")
                file_link = upload_to_drive(csv_file_path, f"data_requested_by_{user_id}.csv")
                logger.info(f"File berhasil diunggah. Link: {file_link}")
                
                # Kirim pesan dengan respons asli dan link
                combined_response = f"{answer}\n\nFile CSV dapat diunduh di: {file_link}"
                
                # Jika terlalu panjang, potong respons dan tambahkan link
                if len(combined_response) > 4000:  # Batas karakter message Line
                    shortened_response = f"{answer[:3500]}...\n\nFile CSV dapat diunduh di: {file_link}"
                    line_bot_api.reply_message(
                        event.reply_token,
                        TextSendMessage(text=shortened_response)
                    )
                else:
                    line_bot_api.reply_message(
                        event.reply_token,
                        TextSendMessage(text=combined_response)
                    )
                
                # Hapus file temporary
                os.remove(csv_file_path)
                logger.info(f"File temporary {csv_file_path} dihapus")
                return
            else:
                # Jika gagal membuat CSV, kirim respons normal dengan pesan error
                line_bot_api.reply_message(
                    event.reply_token,
                    TextSendMessage(text=f"{answer}\n\nMaaf, tidak dapat menghasilkan file CSV dari data.")
                )
                return
        else:
            # Jika tidak ada tabel yang ditemukan, kirim respons normal
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text=answer)
            )
            return
    
    # Jika bukan permintaan data atau tidak ada tabel, kirim respons normal
    if 'answer' in dify_response:
        logger.info("Mengirim respons normal dari Dify")
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=dify_response['answer'])
        )
    else:
        logger.error("Tidak ada respons dari Dify atau terjadi error")
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text="Maaf, saya tidak dapat memproses permintaan Anda saat ini.")
        )


if __name__ == '__main__':
    app.run(debug=True, port=5000) 