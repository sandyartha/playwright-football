import csv
import json
import os
import logging
import chardet
from datetime import datetime

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)

# Fungsi determine_type, detect_encoding, try_read_csv tetap sama
def determine_type(value, field_name):
    """Menentukan tipe data berdasarkan nama field dan nilai"""
    if value is None or value == "":
        return None
    
    value = value.strip()
    
    integer_fields = {
        'rank_goals', 'rank_assists', 'rank', 'appearances', 'goals', 'assists', 'minutes_played',
        'yellow_cards', 'red_cards'
    }
    
    string_fields = {
        'name', 'full_name', 'first_period', 'second_period', 'jersey_name',
        'club', 'position', 'nation', 'nation_code', 'profile_url', 
        'image_url', 'club_logo_url', 'date_of_birth', 'place_of_birth', 'jersey_number', 'status'
    }
    
    try:
        if field_name in integer_fields:
            cleaned_value = value.replace('.', '').replace(',', '')
            if cleaned_value.isdigit():
                return int(cleaned_value)
            return int(float(cleaned_value))
            
        elif field_name == 'height':
            if value:
                cleaned_height = value.replace(' m', '').replace(',', '.').strip()
                return float(cleaned_height)
            return None
            
        elif field_name in string_fields:
            return value
            
    except (ValueError, TypeError):
        return value
    
    return value

def detect_encoding(file_path):
    """Mendeteksi encoding file menggunakan chardet"""
    with open(file_path, 'rb') as file:
        raw_data = file.read()
        result = chardet.detect(raw_data)
        encoding = result['encoding']
        confidence = result['confidence']
        logging.info(f"Detected encoding: {encoding} (confidence: {confidence:.2%})")
        return encoding if confidence > 0.7 else 'utf-8'

def try_read_csv(file_path):
    """Mencoba membaca CSV dengan encoding yang terdeteksi dan mengembalikan data"""
    detected_encoding = detect_encoding(file_path)
    encodings = [detected_encoding, 'utf-8-sig', 'latin-1', 'windows-1252', 'iso-8859-1']
    
    for encoding in encodings:
        try:
            with open(file_path, 'r', encoding=encoding, newline='') as csvf:
                csv_reader = csv.DictReader(csvf)
                if not csv_reader.fieldnames:
                    logging.error(f"Tidak ada header dengan encoding {encoding}")
                    continue
                data = list(csv_reader)
                fieldnames = [name.strip('\ufeff') if name.startswith('\ufeff') else name 
                            for name in csv_reader.fieldnames]
                logging.info(f"Berhasil membaca dengan encoding: {encoding}")
                return data, fieldnames, encoding
        except UnicodeDecodeError as e:
            logging.warning(f"Gagal decoding dengan {encoding}: {str(e)}")
        except Exception as e:
            logging.warning(f"Error dengan {encoding}: {str(e)}")
    raise Exception("Gagal membaca file dengan semua encoding yang dicoba")

# Membuat folder output
input_folder = "input"
output_folder = "output"
if not os.path.exists(output_folder):
    os.makedirs(output_folder)

# Mengambil semua file CSV
csv_files = [f for f in os.listdir(input_folder) if f.endswith('.csv')]

for csv_file in csv_files:
    try:
        input_path = os.path.join(input_folder, csv_file)
        output_path = os.path.join(output_folder, f"{os.path.splitext(csv_file)[0]}.json")
        
        if os.stat(input_path).st_size == 0:
            logging.warning(f"File {csv_file} kosong")
            continue
        
        # Membaca data CSV
        csv_data, fieldnames, used_encoding = try_read_csv(input_path)
        
        # Batasi hanya 30 baris pertama
        limited_data = csv_data[:30]
        
        # Mengkonversi data langsung ke list
        converted_data = []
        for row in limited_data:
            converted_row = {
                key: determine_type(row[key], key)
                for key in fieldnames
            }
            converted_data.append(converted_row)
        
        # Menulis JSON langsung sebagai array
        with open(output_path, 'w', encoding='utf-8') as jsonf:
            json.dump(converted_data, jsonf, ensure_ascii=False, indent=2)

        logging.info(f"Berhasil mengkonversi 30 baris pertama dari {csv_file} ke {os.path.basename(output_path)}")

    except Exception as e:
        logging.error(f"Error processing {csv_file}: {str(e)}")