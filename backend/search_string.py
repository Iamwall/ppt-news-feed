import os

search_term = "demo response"
root_dir = "c:\\PPT NEWS FEED"

print(f"Searching for '{search_term}' in {root_dir}...")

for root, dirs, files in os.walk(root_dir):
    if "node_modules" in dirs:
        dirs.remove("node_modules")
    if ".git" in dirs:
        dirs.remove(".git")
    if "__pycache__" in dirs:
        dirs.remove("__pycache__")
        
    for file in files:
        try:
            path = os.path.join(root, file)
            with open(path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
                if search_term.lower() in content.lower():
                    print(f"FOUND in {path}")
        except Exception as e:
            pass # ignore errors

print("Search complete.")
