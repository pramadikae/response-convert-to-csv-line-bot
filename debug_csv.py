#!/usr/bin/env python3
"""
Utility untuk debug format CSV dari respons Dify.
Gunakan file ini untuk menguji respons secara langsung.
"""

import sys
import json
import pandas as pd
from io import StringIO
import tempfile
import os
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def debug_csv_format(text_data):
    """Menganalisis format data dan mencoba mengonversi ke CSV."""
    logger.info("Analisis format data:")
    
    # Hitung jumlah baris
    lines = text_data.strip().split('\n')
    logger.info(f"Jumlah baris: {len(lines)}")
    
    # Deteksi pemisah
    if len(lines) > 0:
        first_line = lines[0]
        comma_count = first_line.count(',')
        tab_count = first_line.count('\t')
        
        logger.info(f"Baris pertama: {first_line}")
        logger.info(f"Jumlah koma: {comma_count}")
        logger.info(f"Jumlah tab: {tab_count}")
        
        # Tentukan pemisah
        delimiter = '\t' if tab_count > 0 else ','
        logger.info(f"Pemisah terdeteksi: '{delimiter}'")
        
        # Analisis konsistensi jumlah kolom
        column_counts = []
        for i, line in enumerate(lines):
            cols = line.split(delimiter)
            column_counts.append(len(cols))
            logger.info(f"Baris {i+1}: {len(cols)} kolom")
        
        # Cek konsistensi jumlah kolom
        if len(set(column_counts)) > 1:
            logger.warning("PERINGATAN: Jumlah kolom tidak konsisten di seluruh data!")
            logger.warning(f"Jumlah kolom bervariasi: {set(column_counts)}")
        else:
            logger.info("Jumlah kolom konsisten di seluruh data.")
        
        # Coba konversi dengan pandas
        try:
            logger.info("Mencoba konversi dengan pandas...")
            df = pd.read_csv(StringIO(text_data), sep=delimiter)
            logger.info(f"Konversi berhasil. Dimensi DataFrame: {df.shape}")
            
            # Tampilkan beberapa baris pertama
            logger.info("\nBeberapa baris pertama data:")
            logger.info(f"\n{df.head(3)}")
            
            # Simpan ke file temporary
            temp_file = os.path.join(tempfile.gettempdir(), "debug_csv_output.csv")
            df.to_csv(temp_file, index=False)
            logger.info(f"Data berhasil disimpan ke: {temp_file}")
            
            return True
        except Exception as e:
            logger.error(f"Gagal mengonversi dengan pandas: {str(e)}")
            
            # Coba metode alternatif
            try:
                logger.info("Mencoba metode alternatif dengan engine 'python'...")
                df = pd.read_csv(StringIO(text_data), sep=None, engine='python')
                logger.info(f"Konversi dengan metode alternatif berhasil. Dimensi DataFrame: {df.shape}")
                
                # Tampilkan beberapa baris pertama
                logger.info("\nBeberapa baris pertama data:")
                logger.info(f"\n{df.head(3)}")
                
                # Simpan ke file temporary
                temp_file = os.path.join(tempfile.gettempdir(), "debug_csv_output.csv")
                df.to_csv(temp_file, index=False)
                logger.info(f"Data berhasil disimpan ke: {temp_file}")
                
                return True
            except Exception as alt_e:
                logger.error(f"Metode alternatif juga gagal: {str(alt_e)}")
                return False
    
    return False

def main():
    """Fungsi utama untuk menjalankan debug dari command line."""
    if len(sys.argv) < 2:
        print("Penggunaan: python debug_csv.py <file_json_atau_teks>")
        return
    
    input_file = sys.argv[1]
    
    try:
        # Coba baca sebagai file JSON
        with open(input_file, 'r', encoding='utf-8') as f:
            content = f.read()
            
            # Cek apakah ini file JSON
            try:
                data = json.loads(content)
                if 'answer' in data:
                    # Ini adalah respons Dify
                    logger.info("File JSON respons Dify terdeteksi")
                    text_data = data['answer']
                else:
                    # JSON lain, coba gunakan seluruh konten
                    logger.warning("Format JSON tidak dikenal, mencoba menggunakan seluruh konten")
                    text_data = content
            except json.JSONDecodeError:
                # Bukan JSON, anggap sebagai file teks biasa
                logger.info("Bukan file JSON, menggunakan sebagai teks biasa")
                text_data = content
        
        # Debug format CSV
        success = debug_csv_format(text_data)
        if success:
            logger.info("Analisis format CSV selesai dengan sukses")
        else:
            logger.error("Gagal menganalisis atau mengonversi data ke format CSV")
            
    except Exception as e:
        logger.error(f"Error: {str(e)}")

if __name__ == "__main__":
    main() 