import sqlite3

def get_analytics(username):

    conn = sqlite3.connect(
        'database.db'
    )

    cursor = conn.cursor()

    # TOTAL FILES

    cursor.execute(
        '''
        SELECT COUNT(*)
        FROM files
        WHERE username=?
        ''',
        (username,)
    )

    total = cursor.fetchone()[0]

    # SYNCED FILES

    cursor.execute(
        '''
        SELECT COUNT(*)
        FROM files
        WHERE username=?
        AND sync_status=?
        ''',
        (
            username,
            "Synced"
        )
    )

    synced = cursor.fetchone()[0]

    # DUPLICATES

    cursor.execute(
        '''
        SELECT COUNT(*)
        FROM files
        WHERE username=?
        AND duplicate_status LIKE ?
        ''',
        (
            username,
            "%Duplicate%"
        )
    )

    duplicates = cursor.fetchone()[0]

    conn.close()

    return total, synced, duplicates