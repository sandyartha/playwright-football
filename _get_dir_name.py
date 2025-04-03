import os

# Mendapatkan direktori tempat script ini berada
current_dir = os.getcwd()

# Mendapatkan semua item di direktori
items = os.listdir(current_dir)

# Filter hanya folder/direktori
folders = [item for item in items if os.path.isdir(os.path.join(current_dir, item))]

# Menampilkan daftar folder
print("Daftar folder di direktori saat ini:")
for folder in folders:
    print(f"- {folder}")

# Jika ingin menyimpan ke file txt
with open("daftar_folder.txt", "w") as file:
    file.write("Daftar folder:\n")
    for folder in folders:
        file.write(f"- {folder}\n")

print("\nJumlah folder:", len(folders))