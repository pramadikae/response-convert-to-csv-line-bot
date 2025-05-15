#!/usr/bin/env python3
"""
Utilitas untuk menguji ekstraksi tabel dari respons teks.
Gunakan file ini untuk memeriksa apakah tabel dapat diekstraksi dengan benar.
"""

import sys
import os
import json
import pandas as pd
from io import StringIO
import tempfile
import logging
import argparse

# Import fungsi-fungsi dari app.py
from app import extract_table_from_text, clean_table_text, create_csv_from_table

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_extract_table(text_data):
    """Menguji ekstraksi tabel dari teks."""
    logger.info("Menguji ekstraksi tabel...")
    
    # Ekstrak tabel
    table_text = extract_table_from_text(text_data)
    
    if table_text:
        logger.info("Tabel berhasil diekstrak:")
        logger.info(f"\n{table_text}")
        
        # Bersihkan dan konversi ke format CSV
        clean_text, delimiter = clean_table_text(table_text)
        logger.info("Hasil pembersihan tabel:")
        logger.info(f"\n{clean_text}")
        logger.info(f"Delimiter terdeteksi: {delimiter}")
        
        # Coba konversi ke CSV
        try:
            if delimiter == '|':
                df = pd.read_csv(StringIO(clean_text), sep='|')
            else:
                df = pd.read_csv(StringIO(clean_text), sep=None, engine='python')
            
            logger.info("Data berhasil dikonversi ke DataFrame:")
            logger.info(f"\n{df.head()}")
            
            # Simpan ke file CSV
            temp_file = os.path.join(tempfile.gettempdir(), "test_table_output.csv")
            df.to_csv(temp_file, index=False)
            logger.info(f"File CSV berhasil dibuat: {temp_file}")
            
            # Tampilkan path file CSV
            print(f"\nFile CSV disimpan di: {temp_file}")
            
            return True, temp_file
        except Exception as e:
            logger.error(f"Gagal mengkonversi ke DataFrame: {str(e)}")
            return False, None
    else:
        logger.warning("Tidak dapat mengekstrak tabel dari teks")
        return False, None

def main():
    """Fungsi utama untuk menjalankan pengujian ekstraksi tabel."""
    parser = argparse.ArgumentParser(description='Uji ekstraksi tabel dari teks')
    parser.add_argument('file', help='Path ke file teks atau JSON yang berisi respons')
    args = parser.parse_args()
    
    if not os.path.exists(args.file):
        print(f"File tidak ditemukan: {args.file}")
        return
    
    # Baca file
    with open(args.file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Cek apakah ini file JSON
    text_data = content
    try:
        data = json.loads(content)
        if 'answer' in data:
            logger.info("File JSON respons Dify terdeteksi")
            text_data = data['answer']
    except json.JSONDecodeError:
        logger.info("Bukan file JSON, menggunakan sebagai teks biasa")
    
    # Uji ekstraksi tabel
    success, csv_file = test_extract_table(text_data)
    
    if success:
        logger.info("Pengujian ekstraksi tabel berhasil")
    else:
        logger.error("Pengujian ekstraksi tabel gagal")

if __name__ == "__main__":
    main() 