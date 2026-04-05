import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))


def search_word_in_path(search_path, target_word):
    """
    Searches for a specific word ONLY in the immediate directory provided.
    Does not enter subfolders.
    """
    results = []

    if not os.path.exists(search_path):
        return "The provided path does not exist."

    # Use os.listdir to stay in the current folder only
    for file_name in os.listdir(search_path):
        file_path = os.path.join(search_path, file_name)

        # Ensure we are only looking at files, not folders
        if os.path.isfile(file_path):
            print(f"Searching in: {file_name}...")  # Tracks current progress

            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    for line_num, line in enumerate(f, 1):
                        if target_word.lower() in line.lower():
                            results.append({
                                "file": file_path,
                                "line": line_num,
                                "content": line.strip()
                            })
            except (UnicodeDecodeError, PermissionError):
                continue

    return results


# Example Usage:
found_items = search_word_in_path(BASE_DIR, "my_holding_instruments")

print("\n--- Search Results ---")
print(found_items)