import os
import sqlite3
from difflib import SequenceMatcher
from config import UPLOAD_FOLDER
from modules.encryption import decrypt_file

def similarity(a, b):
    return SequenceMatcher(None, a.lower(), b.lower()).ratio()

def search_files(keyword, username):
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()

    # Fetch all columns including file_hash to exactly match the database schema structure
    cursor.execute("SELECT id, username, filename, category, duplicate_status, sync_status, file_hash FROM files WHERE username=?", (username,))
    user_files = cursor.fetchall()
    conn.close()

    results_with_scores = []
    keyword_lower = keyword.lower()

    for file in user_files:
        filename = file[2]
        category = file[3] if file[3] else ""
        
        # Calculate similarity for filename and category
        name_score = similarity(keyword, filename)
        cat_score = similarity(keyword, category)
        
        # Also check if keyword is a substring (traditional search logic)
        is_substring = keyword_lower in filename.lower() or keyword_lower in category.lower()
        
        # Determine the best match score
        max_score = max(name_score, cat_score)
        
        # Boost score if it's a direct substring match
        if is_substring:
            max_score = max(max_score, 0.8)
            
        # --- AI CONTENT SEARCH & TYPO RESOLUTION ---
        filepath = os.path.join(UPLOAD_FOLDER, filename)
        match_reason = "Typo / Fuzzy Match"
        
        if is_substring or max_score >= 0.8:
            match_reason = "Filename / Category Match"

        # Search inside the actual file contents
        if os.path.exists(filepath):
            try:
                # Safely decrypt the file and decode to text (ignores unreadable binary data like images)
                decrypted_bytes = decrypt_file(filepath)
                content_str = ""
                
                # Extract text depending on document type
                if filename.lower().endswith('.pdf'):
                    try:
                        import PyPDF2
                        import io
                        pdf_reader = PyPDF2.PdfReader(io.BytesIO(decrypted_bytes))
                        for page in pdf_reader.pages:
                            text = page.extract_text()
                            if text:
                                content_str += text.lower() + " "
                    except Exception:
                        # Fallback if PyPDF2 is missing or file is malformed
                        content_str = decrypted_bytes.decode('utf-8', errors='ignore').lower()
                        
                elif filename.lower().endswith('.docx'):
                    try:
                        import zipfile
                        import io
                        import re
                        with zipfile.ZipFile(io.BytesIO(decrypted_bytes)) as docx_zip:
                            xml_content = docx_zip.read('word/document.xml').decode('utf-8')
                            content_str = re.sub(r'<[^>]+>', ' ', xml_content).lower()
                    except Exception:
                        content_str = decrypted_bytes.decode('utf-8', errors='ignore').lower()
                else:
                    content_str = decrypted_bytes.decode('utf-8', errors='ignore').lower()
                
                if keyword_lower in content_str:
                    max_score = max(max_score, 0.9)  # Very high confidence if found in text
                    match_reason = "Content Match (Found inside file)"
            except Exception:
                pass
        
        # If the match is decent enough (threshold > 0.4), include it
        if max_score > 0.4:
            file_list = list(file)
            # Store the score temporarily at index 7 for sorting
            file_list.append(round(max_score * 100, 1)) 
            # Store the AI insight/suggestion at index 8
            file_list.append(match_reason)
            results_with_scores.append(file_list)

    # Sort results by the score (index 7) in descending order
    results_with_scores.sort(key=lambda x: x[7], reverse=True)

    return results_with_scores