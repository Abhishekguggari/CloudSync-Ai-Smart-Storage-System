import sqlite3
import bcrypt

# REGISTER USER

def register_user(username, email, password):

    conn = sqlite3.connect('database.db')

    cursor = conn.cursor()

    hashed = bcrypt.hashpw(
        password.encode('utf-8'),
        bcrypt.gensalt()
    )

    cursor.execute(
        '''
        INSERT INTO users
        (username, email, password)

        VALUES (?, ?, ?)
        ''',
        (
            username,
            email,
            hashed
        )
    )

    conn.commit()

    conn.close()

# LOGIN USER

def login_user(username, password):

    conn = sqlite3.connect('database.db')

    cursor = conn.cursor()

    cursor.execute(
        '''
        SELECT password
        FROM users
        WHERE username=?
        ''',
        (username,)
    )

    user = cursor.fetchone()

    conn.close()

    if user:

        return bcrypt.checkpw(
            password.encode('utf-8'),
            user[0]
        )

    return False