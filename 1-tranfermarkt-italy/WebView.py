import os
import json
from flask import Flask, jsonify, render_template_string, request

def get_json_files(folder_path):
    return [f for f in os.listdir(folder_path) if f.endswith(".json")]

def load_json_file(folder_path, filename):
    file_path = os.path.join(folder_path, filename)
    try:
        with open(file_path, "r", encoding="utf-8") as file:
            data = json.load(file)
            return data if isinstance(data, list) else [data]
    except json.JSONDecodeError:
        print(f"Gagal membaca {filename}, pastikan formatnya benar.")
        return []

def save_json_file(folder_path, filename, data):
    file_path = os.path.join(folder_path, filename)

    # Load data asli untuk menjaga field yang mungkin hilang
    original_data = load_json_file(folder_path, filename)

    # Pastikan setiap item memiliki semua kunci yang asli
    for i, item in enumerate(data):
        for key in original_data[i]:  # Gunakan data lama sebagai referensi
            if key not in item:
                item[key] = original_data[i][key]  # Gunakan nilai lama jika tidak ada
        
    with open(file_path, "w", encoding="utf-8") as file:
        json.dump(data, file, indent=4, ensure_ascii=False)



def assign_rank(data):
    sorted_data = sorted(data, key=lambda x: x.get("rank_goals", x.get("rank_assists", float('inf'))))
    return sorted_data

app = Flask(__name__)

@app.route('/api/data', methods=['GET'])
def get_data():
    folder_path = "./raw"
    filename = request.args.get("file")
    if not filename:
        return jsonify([])
    
    data = load_json_file(folder_path, filename)
    data = assign_rank(data)

    # Pastikan semua field ada di setiap item
    if data:
        keys = set().union(*(d.keys() for d in data))
        for item in data:
            for key in keys:
                if key not in item:
                    item[key] = ""  # Beri nilai default kosong jika tidak ada
    
    return jsonify(data)


@app.route('/api/save', methods=['POST'])
def save_data():
    if not request.is_json:
        return jsonify({"success": False, "message": "Request must be JSON"}), 400  # Tambahkan validasi JSON

    data = request.get_json()
    folder_path = "./raw"
    filename = data.get("file")
    json_data = data.get("data")

    if not filename or not json_data:
        return jsonify({"success": False, "message": "Invalid data"}), 400
    
    save_json_file(folder_path, filename, json_data)
    return jsonify({"success": True})


@app.route('/')
def index():
    folder_path = "./raw"
    files = get_json_files(folder_path)
    return render_template_string(TEMPLATE, files=files)

TEMPLATE = """
<!DOCTYPE html>
<html lang=\"en\">
<head>
    <meta charset=\"UTF-8\">
    <meta name=\"viewport\" content=\"width=device-width, initial-scale=1.0\">
    <title>JSON CRUD Table</title>
    <script src=\"https://code.jquery.com/jquery-3.6.0.min.js\"></script>
    <style>
        table { width: 100%; border-collapse: collapse; margin-top: 20px; }
        th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
        th { background-color: #f4f4f4; }
        img { width: 100px; height: 100px; border-radius: 100%; }
        .editable { background-color: #fff8dc; cursor: pointer; }
    </style>
    <script>
        $(document).ready(function() {
            let currentFile = '';
            $('#fileSelector').change(function() {
                currentFile = $(this).val();
                if (currentFile) {
                    $.getJSON('/api/data?file=' + currentFile, function(data) {
                        let table = '<table><thead><tr>';
                        let headers = ['Rank', 'Image', 'Name', 'Period', 'Position', 'Appearances', 'Goals', 'Assists', 'Minutes Played', 'Nation', 'Nation Code', 'Height', 'Date Birth', 'Actions'];
                        headers.forEach(header => {
                            table += '<th>' + header + '</th>';
                        });
                        table += '</tr></thead><tbody>';
                        
                        data.forEach((item, index) => {
                            table += '<tr>' +
                                '<td contenteditable="true" class="editable" data-key="rank_goals">' + (item.rank_goals || '') + '</td>' +
                                '<td><img src="' + item.image_url + '" alt="Image"></td>' +
                                '<td contenteditable="true" class="editable" data-key="name">' + item.name + '</td>' +
                                '<td contenteditable="true" class="editable" data-key="period">' + (item.period || '-') + '</td>' +
                                '<td contenteditable="true" class="editable" data-key="position">' + item.position + '</td>' +
                                '<td contenteditable="true" class="editable" data-key="appearances">' + item.appearances + '</td>' +
                                '<td contenteditable="true" class="editable" data-key="goals">' + item.goals + '</td>' +
                                '<td contenteditable="true" class="editable" data-key="assists">' + item.assists + '</td>' +
                                '<td contenteditable="true" class="editable" data-key="minutes_played">' + item.minutes_played + '</td>' +
                                '<td contenteditable="true" class="editable" data-key="nation">' + item.nation + '</td>' +
                                '<td contenteditable="true" class="editable" data-key="nation_code">' + item.nation_code + '</td>' +
                                '<td contenteditable="true" class="editable" data-key="height">' + item.height + '</td>' +
                                '<td contenteditable="true" class="editable" data-key="date_of_birth">' + item.date_of_birth + '</td>' +
                                '<td><button class="delete-btn" data-index="' + index + '">Delete</button></td>' +
                                '</tr>';
                        });
                        
                        table += '</tbody></table>';
                        table += '<button id="saveBtn">Save Changes</button>';
                        $('#dataContainer').html(table);
                    });
                }
            });
            
            $(document).on('click', '.delete-btn', function() {
                $(this).closest('tr').remove();
            });
            
            $(document).on('click', '#saveBtn', function() {
            let newData = [];
            $('table tbody tr').each(function() {
                let row = {};

                // Ambil data dari sel yang bisa diedit
                $(this).find('.editable').each(function() {
                    row[$(this).data('key')] = $(this).text().trim();
                });

                // Ambil data gambar
                let imgSrc = $(this).find('img').attr('src');
                if (imgSrc) row["image_url"] = imgSrc;

                newData.push(row);
            });

            $.ajax({
                url: '/api/save',
                type: 'POST',
                contentType: 'application/json',
                data: JSON.stringify({ file: currentFile, data: newData }),
                success: function(response) {
                    alert('Data saved successfully!');
                },
                error: function() {
                    alert('Failed to save data.');
                }
            });
        });



            });
        });
    </script>
</head>
<body>
    <h2>JSON CRUD Table</h2>
    <label for="fileSelector">Pilih File JSON:</label>
    <select id="fileSelector">
        <option value="">-- Pilih File --</option>
        {% for file in files %}
            <option value="{{ file }}">{{ file }}</option>
        {% endfor %}
    </select>
    <div id="dataContainer"></div>
</body>
</html>
"""

if __name__ == "__main__":
    app.run(debug=True)