from pathlib import Path
import re

search_path = input("""Enter the folder path to search for .txt files:
- Example: C:\\Users\\YourUsername\\Documents
- or just type '.' for the current directory
""")
path = Path(search_path)

while True:
    if not path.exists() or not path.is_dir():
        print("The provided path does not exist or is not a directory.")
        search_path = input("Please enter a valid folder path: ")
        path = Path(search_path)
    else:
        break    

search_pattern = input("Enter the search pattern (e.g., 'example'): ")

for file in path.glob("*.txt"):
    with open(file, "r") as f:
        for line in f:
            cleaned_line = line.strip()
            if re.search(search_pattern, cleaned_line):
                print(f"Found in {file}: {cleaned_line}")