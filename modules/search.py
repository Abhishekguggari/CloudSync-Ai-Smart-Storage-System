import sqlite3
from difflib import SequenceMatcher

def similarity(a, b):
    return SequenceMatcher(None, a.lower(), b.lower()).ratio()

def search_files(keyword):
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()

    # Fetch all files to perform fuzzy matching in Python
    cursor.execute("SELECT * FROM files")
    all_files = cursor.fetchall()
    conn.close()

    results_with_scores = []

    for file in all_files:
        filename = file[2]
        category = file[3]
        
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
            # We'll append the score to the file tuple so we can sort by it
            # Original file tuple: (id, username, filename, category, duplicate_status, sync_status)
            file_list = list(file)
            file_list.append(round(max_score * 100, 1)) # Add score as percentage
            results_with_scores.append(file_list)

    # Sort results by the score (which is now at index 6) in descending order
    results_with_scores.sort(key=lambda x: x[6], reverse=True)

    return results_with_scores
