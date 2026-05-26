import sqlite3
from difflib import SequenceMatcher

def similarity(a, b):
    return SequenceMatcher(None, a.lower(), b.lower()).ratio()

def search_files(keyword):
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()

    # Fetch all columns including file_hash to exactly match the database schema structure
    cursor.execute("SELECT id, username, filename, category, duplicate_status, sync_status, file_hash FROM files")
    all_files = cursor.fetchall()
    conn.close()

    results_with_scores = []

    for file in all_files:
        filename = file[2]
        category = file[3] if file[3] else ""
        
        # Calculate similarity for filename and category
        name_score = similarity(keyword, filename)
        cat_score = similarity(keyword, category)
        
        # Also check if keyword is a substring (traditional search logic)
        is_substring = keyword.lower() in filename.lower() or keyword.lower() in category.lower()
        
        # Determine the best match score
        max_score = max(name_score, cat_score)
        
        # Boost score if it's a direct substring match
        if is_substring:
            max_score = max(max_score, 0.8)
        
        # If the match is decent enough (threshold > 0.4), include it
        if max_score > 0.4:
            file_list = list(file)
            # Store the score temporarily at index 7 for sorting
            file_list.append(round(max_score * 100, 1)) 
            results_with_scores.append(file_list)

    # Sort results by the score (index 7) in descending order
    results_with_scores.sort(key=lambda x: x[7], reverse=True)

    # CLEANUP: Remove the temporary score element so it exactly matches your SQL row format
    final_results = [file[:7] for file in results_with_scores]

    return final_results