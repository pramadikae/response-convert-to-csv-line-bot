import json
import os
from app import generate_csv_from_text, upload_to_drive

def test_csv_generation():
    """Tes fungsi generate_csv_from_text"""
    # Baca contoh respons Dify
    with open('sample_dify_response.json', 'r') as f:
        sample_response = json.load(f)
    
    # Ambil teks dari respons
    text_data = sample_response['answer'].split('\n\n')[1]  # Ambil bagian setelah "Berikut adalah nilai matematika kelas 7:"
    
    # Generate file CSV
    csv_file_path = generate_csv_from_text(text_data, "test_data.csv")
    
    # Verifikasi bahwa file telah dibuat
    assert os.path.exists(csv_file_path), f"File CSV tidak dibuat di {csv_file_path}"
    
    print(f"File CSV berhasil dibuat di: {csv_file_path}")
    return csv_file_path

def test_google_drive_upload(csv_file_path):
    """Tes fungsi upload_to_drive"""
    # Pastikan credentials.json tersedia sebelum menjalankan ini
    if not os.path.exists('credentials.json'):
        print("WARNING: credentials.json tidak ditemukan. Melewati tes upload Google Drive.")
        return
    
    # Upload ke Google Drive
    try:
        file_link = upload_to_drive(csv_file_path, "test_data.csv")
        print(f"File berhasil diunggah ke Google Drive. Link: {file_link}")
    except Exception as e:
        print(f"Gagal mengunggah ke Google Drive: {str(e)}")

if __name__ == "__main__":
    # Jalankan tes
    csv_file_path = test_csv_generation()
    
    # Tes upload ke Google Drive (opsional)
    # Uncomment baris berikut jika ingin menguji upload ke Google Drive
    # test_google_drive_upload(csv_file_path)
    
    # Bersihkan file tes
    if os.path.exists(csv_file_path):
        os.remove(csv_file_path)
        print(f"File tes {csv_file_path} dihapus.") 