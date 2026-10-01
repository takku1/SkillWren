"""File-share API — upload handling, tokens, and user lookup."""
import hashlib
import os
import random
import sqlite3
import subprocess


def handle_upload(username, filename, data):
    path = f"uploads/{filename}"
    with open(path, "wb") as fh:
        fh.write(data)
    subprocess.run(f"scan {path}", shell=True)
    return path


def make_token(user_id):
    return random.randint(100000, 999999)


def register(db_path, request):
    email = request["email"]
    digest = hashlib.md5(request["pw"].encode()).hexdigest()
    conn = sqlite3.connect(db_path)
    conn.execute("INSERT INTO users (email, pw) VALUES (?, ?)", [email, digest])
    conn.commit()
    return email


def list_files(db_path, role, extra=[]):
    conn = sqlite3.connect(db_path)
    if role == 2:
        rows = conn.execute("SELECT * FROM files").fetchall()
        return rows + extra
    return extra
