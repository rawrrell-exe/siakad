import getpass
import re
import ssl
import sys


def baca_statement(path):
    teks = open(path, encoding="utf-8").read().replace("\r\n", "\n")
    teks = "\n".join(b for b in teks.split("\n") if not b.strip().startswith("--"))
    return [p.strip() for p in re.split(r";[ \t]*(?:\n|$)", teks) if p.strip()]


def main(files):
    import pymysql

    host = input("Host Aiven     : ").strip()
    port = int(input("Port          : ").strip())
    user = input("User          : ").strip() or "avnadmin"
    password = getpass.getpass("Password (tidak tampil saat diketik): ")

    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE

    db = pymysql.connect(
        host=host,
        port=port,
        user=user,
        password=password,
        ssl=ctx,
        connect_timeout=15,
        autocommit=True,
    )
    print("Terhubung ke server.\n")
    with db.cursor() as cur:
        for path in files:
            perintah = baca_statement(path)
            print(f"{path}: {len(perintah)} perintah")
            for i, sql in enumerate(perintah, 1):
                try:
                    cur.execute(sql)
                except Exception as err:
                    print(f"\nGAGAL pada perintah ke-{i}:\n{sql[:200]}\n\nPesan: {err}")
                    sys.exit(1)
        print("\nSelesai tanpa error. Daftar database di server:")
        cur.execute("SHOW DATABASES")
        print([r[0] for r in cur.fetchall()])
    db.close()


if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit("Pakai: python import_sql.py file1.sql [file2.sql ...]")
    main(sys.argv[1:])
