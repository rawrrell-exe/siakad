import hmac
import os
from datetime import datetime, timedelta, timezone
import secrets
import ssl
from functools import wraps

import pymysql
from flask import (
    Flask,
    abort,
    flash,
    g,
    redirect,
    render_template,
    request,
    session,
    url_for,
)
from werkzeug.security import check_password_hash, generate_password_hash

app = Flask(__name__)


ON_VERCEL = bool(os.getenv("VERCEL"))
SECRET = os.getenv("SECRET_KEY")
if ON_VERCEL and not SECRET:
    raise RuntimeError("SECRET_KEY belum diatur di Environment Variables Vercel.")
app.secret_key = SECRET or "kunci-lokal-hanya-untuk-pengembangan"
app.config.update(
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="Lax",
    SESSION_COOKIE_SECURE=ON_VERCEL,
)


def buat_ssl():
    """SSL untuk database cloud (mis. Aiven). Aktifkan dengan DB_SSL=true.
    Isi DB_SSL_CA dengan path file CA jika sertifikat ingin diverifikasi."""
    if os.getenv("DB_SSL", "false").lower() != "true":
        return None
    ca = os.getenv("DB_SSL_CA")
    ctx = ssl.create_default_context(cafile=ca) if ca else ssl.create_default_context()
    ctx.check_hostname = False
    if not ca:
        ctx.verify_mode = ssl.CERT_NONE
    return ctx


DB_CONFIG = dict(
    host=os.getenv("DB_HOST", "localhost"),
    port=int(os.getenv("DB_PORT", "3306")),
    user=os.getenv("DB_USER", "root"),
    password=os.getenv("DB_PASS", ""),
    database=os.getenv("DB_NAME", "db_siakadroro"),
    ssl=buat_ssl(),
    connect_timeout=10,
    cursorclass=pymysql.cursors.DictCursor,
    autocommit=True,
)
HARI = ["Senin", "Selasa", "Rabu", "Kamis", "Jumat", "Sabtu"]
PROFIL = {
    "Admin": ("tb_tendik_ftikom", "nama_tendik"),
    "Dosen": ("tb_dosen", "nama_dosen"),
    "Mahasiswa": ("tb_mhs", "nama_mhs"),
}


def conn():
    if "db" not in g:
        g.db = pymysql.connect(**DB_CONFIG)
    return g.db


@app.teardown_appcontext
def tutup_db(_):
    db = g.pop("db", None)
    if db:
        db.close()


def q(sql, args=(), one=False):
    """SELECT -> list of dict (atau satu dict jika one=True)."""
    with conn().cursor() as c:
        c.execute(sql, args)
        rows = c.fetchall()
    return (rows[0] if rows else None) if one else rows


def x(sql, args=()):
    """INSERT/UPDATE/DELETE -> lastrowid."""
    with conn().cursor() as c:
        c.execute(sql, args)
        return c.lastrowid


def nilai_huruf(n):
    """Konversi skala 4.00 ke huruf."""
    return (
        "A"
        if n >= 3.5
        else "B" if n >= 3 else "C" if n >= 2 else "D" if n >= 1 else "E"
    )


def role(*roles):
    def deco(f):
        @wraps(f)
        def wrapper(*a, **k):
            if "uid" not in session:
                return redirect(url_for("login"))
            if session["role"] not in roles:
                abort(403)
            return f(*a, **k)

        return wrapper

    return deco


def profil():
    """Baris profil (tendik/dosen/mhs) milik user yang login."""
    tabel, _ = PROFIL[session["role"]]
    return q(f"SELECT * FROM {tabel} WHERE id_user=%s", (session["uid"],), one=True)


def cek_password(tersimpan, input_pw):
    if tersimpan.startswith(("scrypt:", "pbkdf2:")):
        return check_password_hash(tersimpan, input_pw)
    return tersimpan == input_pw


def csrf_token():
    if "csrf_token" not in session:
        session["csrf_token"] = secrets.token_hex(16)
    return session["csrf_token"]


app.jinja_env.globals["csrf_token"] = csrf_token


@app.before_request
def cek_csrf():
    """Semua form POST wajib membawa token yang cocok dengan sesi."""
    if request.method == "POST":
        sah = session.get("csrf_token", "")
        kirim = request.form.get("csrf_token", "")
        if not sah or not hmac.compare_digest(sah, kirim):
            abort(400)


@app.errorhandler(400)
def bad_request(_):
    return "Formulir kedaluwarsa. Muat ulang halaman lalu coba lagi.", 400


@app.context_processor
def inject_menu():
    return dict(nama=session.get("nama"), peran=session.get("role"))


@app.route("/health")
def health():
    """Cek cepat aplikasi + koneksi database."""
    try:
        q("SELECT 1")
        return "ok", 200
    except Exception:
        return "database tidak terjangkau", 503


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        user = q(
            "SELECT * FROM tb_user WHERE username=%s",
            (request.form["username"].strip(),),
            one=True,
        )
        if user and cek_password(user["password"], request.form["password"]):
            if not user["password"].startswith(("scrypt:", "pbkdf2:")):
                x(  # ubah password plain text lama menjadi hash
                    "UPDATE tb_user SET password=%s WHERE id_user=%s",
                    (generate_password_hash(request.form["password"]), user["id_user"]),
                )
            session.clear()
            session.update(uid=user["id_user"], role=user["role_user"])
            p = profil()
            session["nama"] = p[PROFIL[user["role_user"]][1]] if p else user["username"]
            return redirect(url_for("dashboard"))
        flash("Username atau password belum cocok. Coba cek lagi ya.", "error")
    return render_template("login.html", demo=os.getenv("SHOW_DEMO") == "1")


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


@app.route("/")
@role("Admin", "Dosen", "Mahasiswa")
def dashboard():
    stat = None
    if session["role"] == "Admin":
        stat = q(
            """SELECT (SELECT COUNT(*) FROM tb_mhs) mhs, (SELECT COUNT(*) FROM tb_dosen) dosen,
                           (SELECT COUNT(*) FROM tb_matkul) matkul, (SELECT COUNT(*) FROM tb_jadwal_kelas) jadwal""",
            one=True,
        )
    return render_template("dashboard.html", stat=stat)


@app.route("/mahasiswa/jadwal")
@role("Mahasiswa")
def mhs_jadwal():
    rows = q(
        """SELECT j.id_jadwal, k.nama_kelas, mk.nama_matkul, mk.sks_matakuliah, d.nama_dosen,
                       j.hari, j.jam, j.ruangan
                FROM tb_jadwal_kelas j
                JOIN tb_kelas k ON j.id_kelas = k.id_kelas
                JOIN tb_matkul mk ON j.kode_mk = mk.kode_mk
                JOIN tb_dosen d ON j.nidn_dosen = d.nidn_dosen
                WHERE k.id_kelas = %s
                ORDER BY FIELD(j.hari,'Senin','Selasa','Rabu','Kamis','Jumat','Sabtu'), j.jam""",
        (profil()["id_kelas"],),
    )
    return render_template("jadwal.html", rows=rows, judul="Jadwal kuliah", hari=HARI)


@app.route("/mahasiswa/transkrip")
@role("Mahasiswa")
def mhs_transkrip():
    me = profil()
    rows = q(
        """SELECT m.nim_mhs, m.nama_mhs, mk.kode_mk, mk.nama_matkul, mk.sks_matakuliah,
                       n.nilai_akhir, n.nilai_huruf
                FROM tb_nilai n
                JOIN tb_mhs m ON n.nim_mhs = m.nim_mhs
                JOIN tb_matkul mk ON n.kode_mk = mk.kode_mk
                WHERE m.nim_mhs = %s""",
        (me["nim_mhs"],),
    )
    sks = sum(r["sks_matakuliah"] or 0 for r in rows)
    ipk = (
        (sum(float(r["nilai_akhir"]) * (r["sks_matakuliah"] or 0) for r in rows) / sks)
        if sks
        else 0
    )
    return render_template("transkrip.html", rows=rows, me=me, sks=sks, ipk=ipk)


DOSEN_JADWAL_SQL = """SELECT j.id_jadwal, d.nama_dosen, mk.kode_mk, mk.nama_matkul, k.id_kelas, k.nama_kelas,
                             j.hari, j.jam, j.ruangan
                      FROM tb_jadwal_kelas j
                      JOIN tb_dosen d ON j.nidn_dosen = d.nidn_dosen
                      JOIN tb_matkul mk ON j.kode_mk = mk.kode_mk
                      JOIN tb_kelas k ON j.id_kelas = k.id_kelas
                      WHERE d.nidn_dosen = %s
                      ORDER BY FIELD(j.hari,'Senin','Selasa','Rabu','Kamis','Jumat','Sabtu'), j.jam"""


@app.route("/dosen/jadwal")
@role("Dosen")
def dsn_jadwal():
    rows = q(DOSEN_JADWAL_SQL, (profil()["nidn_dosen"],))
    return render_template("jadwal.html", rows=rows, judul="Jadwal mengajar", hari=HARI)


@app.route("/dosen/nilai")
@role("Dosen")
def dsn_nilai():
    rows = q(DOSEN_JADWAL_SQL, (profil()["nidn_dosen"],))
    return render_template("nilai_pilih.html", rows=rows)


@app.route("/dosen/nilai/<kode_mk>/<int:id_kelas>", methods=["GET", "POST"])
@role("Dosen")
def dsn_nilai_input(kode_mk, id_kelas):
    me = profil()
    ampu = q(
        """SELECT mk.nama_matkul, k.nama_kelas FROM tb_jadwal_kelas j
                JOIN tb_matkul mk ON j.kode_mk = mk.kode_mk JOIN tb_kelas k ON j.id_kelas = k.id_kelas
                WHERE j.nidn_dosen=%s AND j.kode_mk=%s AND j.id_kelas=%s""",
        (me["nidn_dosen"], kode_mk, id_kelas),
        one=True,
    )
    if not ampu:
        abort(403)

    if request.method == "POST":
        siswa_kelas = {
            str(r["nim_mhs"])
            for r in q("SELECT nim_mhs FROM tb_mhs WHERE id_kelas=%s", (id_kelas,))
        }
        simpan = 0
        for nim in request.form.getlist("nim"):
            if nim not in siswa_kelas:
                continue
            raw = request.form.get(f"nilai_{nim}", "").strip().replace(",", ".")
            if not raw:
                continue
            try:
                n = round(float(raw), 2)
                assert 0 <= n <= 4
            except (ValueError, AssertionError):
                flash(f"Nilai untuk NIM {nim} harus angka 0 - 4.", "error")
                return redirect(request.url)
            ada = q(
                "SELECT id_nilai FROM tb_nilai WHERE nim_mhs=%s AND kode_mk=%s",
                (nim, kode_mk),
                one=True,
            )
            if ada:
                x(
                    "UPDATE tb_nilai SET nilai_akhir=%s, nilai_huruf=%s WHERE id_nilai=%s",
                    (n, nilai_huruf(n), ada["id_nilai"]),
                )
            else:
                x(
                    "INSERT INTO tb_nilai (nim_mhs, kode_mk, nilai_akhir, nilai_huruf) VALUES (%s,%s,%s,%s)",
                    (nim, kode_mk, n, nilai_huruf(n)),
                )
            simpan += 1
        flash(f"{simpan} nilai berhasil disimpan.", "ok")
        return redirect(request.url)

    order = (
        "n.nilai_akhir DESC" if request.args.get("urut") == "nilai" else "m.nama_mhs"
    )
    siswa = q(
        f"""SELECT m.nim_mhs, m.nama_mhs, n.nilai_akhir, n.nilai_huruf
                  FROM tb_mhs m LEFT JOIN tb_nilai n ON n.nim_mhs = m.nim_mhs AND n.kode_mk = %s
                  WHERE m.id_kelas = %s ORDER BY {order}""",
        (kode_mk, id_kelas),
    )
    return render_template(
        "nilai_input.html", siswa=siswa, ampu=ampu, urut=request.args.get("urut")
    )


def opt_kelas():
    return q("SELECT id_kelas AS v, nama_kelas AS t FROM tb_kelas ORDER BY nama_kelas")


def opt_matkul():
    return q(
        "SELECT kode_mk AS v, CONCAT(kode_mk,' - ',nama_matkul) AS t FROM tb_matkul ORDER BY kode_mk"
    )


def opt_dosen():
    return q(
        "SELECT nidn_dosen AS v, nama_dosen AS t FROM tb_dosen ORDER BY nama_dosen"
    )


JK = lambda: [dict(v="Man", t="Laki-laki"), dict(v="Woman", t="Perempuan")]
HARI_OPT = lambda: [dict(v=h, t=h) for h in HARI]


ENT = {
    "mahasiswa": dict(
        title="Data mahasiswa",
        table="tb_mhs",
        pk="nim_mhs",
        role="Mahasiswa",
        cols=[
            ("nim_mhs", "NIM"),
            ("nama_mhs", "Nama"),
            ("jenis_kelamin_mhs", "JK"),
            ("nama_kelas", "Kelas"),
            ("prodi_mhs", "Prodi"),
            ("angkatan_mhs", "Angkatan"),
        ],
        list_sql="""SELECT m.*, k.nama_kelas FROM tb_mhs m LEFT JOIN tb_kelas k ON m.id_kelas=k.id_kelas ORDER BY m.nama_mhs""",
        search_sql="""SELECT m.*, k.nama_kelas FROM tb_mhs m LEFT JOIN tb_kelas k ON m.id_kelas=k.id_kelas
                      WHERE m.nama_mhs LIKE %s OR m.nim_mhs LIKE %s ORDER BY m.nama_mhs ASC""",
        fields=[
            dict(name="nim_mhs", label="NIM", type="number", create_only=True),
            dict(
                name="username", label="Username login", type="text", create_only=True
            ),
            dict(name="password", label="Password", type="password", create_only=True),
            dict(name="nama_mhs", label="Nama lengkap", type="text"),
            dict(
                name="jenis_kelamin_mhs",
                label="Jenis kelamin",
                type="select",
                options=JK,
            ),
            dict(
                name="id_kelas",
                label="Kelas",
                type="select",
                options=opt_kelas,
                optional=True,
            ),
            dict(name="prodi_mhs", label="Prodi", type="text", optional=True),
            dict(name="fakultas_mhs", label="Fakultas", type="text", optional=True),
            dict(name="angkatan_mhs", label="Angkatan", type="text", optional=True),
        ],
    ),
    "dosen": dict(
        title="Data dosen",
        table="tb_dosen",
        pk="nidn_dosen",
        role="Dosen",
        cols=[
            ("nidn_dosen", "NIDN"),
            ("nama_dosen", "Nama"),
            ("pendidikan_terakhir_dosen", "Pendidikan"),
            ("email_dosen", "Email"),
            ("no_tlp_dosen", "Telepon"),
        ],
        list_sql="SELECT * FROM tb_dosen ORDER BY nama_dosen",
        search_sql="SELECT * FROM tb_dosen WHERE nama_dosen LIKE %s OR nidn_dosen LIKE %s ORDER BY nama_dosen",
        fields=[
            dict(name="nidn_dosen", label="NIDN", type="number", create_only=True),
            dict(
                name="username", label="Username login", type="text", create_only=True
            ),
            dict(name="password", label="Password", type="password", create_only=True),
            dict(name="nama_dosen", label="Nama lengkap + gelar", type="text"),
            dict(
                name="jenis_kelamin_dosen",
                label="Jenis kelamin",
                type="select",
                options=JK,
            ),
            dict(
                name="pendidikan_terakhir_dosen",
                label="Pendidikan terakhir",
                type="text",
            ),
            dict(name="email_dosen", label="Email", type="email"),
            dict(name="no_tlp_dosen", label="No. telepon", type="text"),
            dict(name="alamat_dosen", label="Alamat", type="textarea", optional=True),
        ],
    ),
    "jadwal": dict(
        title="Jadwal perkuliahan",
        table="tb_jadwal_kelas",
        pk="id_jadwal",
        role=None,
        cols=[
            ("nama_kelas", "Kelas"),
            ("nama_matkul", "Mata kuliah"),
            ("nama_dosen", "Dosen"),
            ("hari", "Hari"),
            ("jam", "Jam"),
            ("ruangan", "Ruang"),
        ],
        list_sql="""SELECT j.*, k.nama_kelas, mk.nama_matkul, d.nama_dosen FROM tb_jadwal_kelas j
                    LEFT JOIN tb_kelas k ON j.id_kelas=k.id_kelas
                    LEFT JOIN tb_matkul mk ON j.kode_mk=mk.kode_mk
                    LEFT JOIN tb_dosen d ON j.nidn_dosen=d.nidn_dosen
                    ORDER BY j.id_kelas, FIELD(j.hari,'Senin','Selasa','Rabu','Kamis','Jumat','Sabtu'), j.jam""",
        search_sql=None,
        fields=[
            dict(name="id_kelas", label="Kelas", type="select", options=opt_kelas),
            dict(
                name="kode_mk", label="Mata kuliah", type="select", options=opt_matkul
            ),
            dict(
                name="nidn_dosen",
                label="Dosen pengampu",
                type="select",
                options=opt_dosen,
            ),
            dict(name="hari", label="Hari", type="select", options=HARI_OPT),
            dict(name="jam", label="Jam (mis. 08.00-09.40)", type="text"),
            dict(name="ruangan", label="Ruangan", type="text"),
        ],
    ),
}


def get_ent(nama):
    return ENT.get(nama) or abort(404)


@app.route("/admin/<ent>")
@role("Admin")
def adm_list(ent):
    e, cari = get_ent(ent), request.args.get("cari", "").strip()
    if cari and e["search_sql"]:
        rows = q(e["search_sql"], (f"%{cari}%", f"%{cari}%"))
    else:
        rows = q(e["list_sql"])
    return render_template("list.html", e=e, ent=ent, rows=rows, cari=cari)


def simpan(e, v, row):
    """Simpan dalam satu transaksi (user + profil harus berhasil bersamaan)."""
    db = conn()
    try:
        db.begin()
        if row:
            sets = ", ".join(f"{k}=%s" for k in v)
            x(
                f"UPDATE {e['table']} SET {sets} WHERE {e['pk']}=%s",
                [*v.values(), row[e["pk"]]],
            )
        else:
            if e["role"]:
                if not v.get("username") or not v.get("password"):
                    raise pymysql.err.IntegrityError(
                        0, "username & password wajib diisi"
                    )
                v["id_user"] = x(
                    "INSERT INTO tb_user (username, password, role_user) VALUES (%s,%s,%s)",
                    (
                        v.pop("username"),
                        generate_password_hash(v.pop("password")),
                        e["role"],
                    ),
                )
            cols, ph = ", ".join(v), ", ".join(["%s"] * len(v))
            x(f"INSERT INTO {e['table']} ({cols}) VALUES ({ph})", list(v.values()))
        db.commit()
    except Exception:
        db.rollback()
        raise


@app.route("/admin/<ent>/tambah", methods=["GET", "POST"])
@app.route("/admin/<ent>/<pk>/edit", methods=["GET", "POST"])
@role("Admin")
def adm_form(ent, pk=None):
    e = get_ent(ent)
    row = (
        q(f"SELECT * FROM {e['table']} WHERE {e['pk']}=%s", (pk,), one=True)
        if pk
        else None
    )
    if pk and not row:
        abort(404)
    fields = [f for f in e["fields"] if not (pk and f.get("create_only"))]
    if request.method == "POST":
        v = {f["name"]: request.form.get(f["name"], "").strip() or None for f in fields}
        try:
            simpan(e, dict(v), row)
            flash("Data berhasil disimpan.", "ok")
            return redirect(url_for("adm_list", ent=ent))
        except pymysql.err.IntegrityError as err:
            flash(
                f"Data belum bisa disimpan: ada isian wajib yang kosong atau sudah dipakai ({err.args[1]}).",
                "error",
            )
            row = {**(row or {}), **v}
    return render_template("form.html", e=e, ent=ent, fields=fields, row=row, pk=pk)


@app.post("/admin/<ent>/<pk>/hapus")
@role("Admin")
def adm_hapus(ent, pk):
    e = get_ent(ent)
    row = q(f"SELECT * FROM {e['table']} WHERE {e['pk']}=%s", (pk,), one=True) or abort(
        404
    )
    if e["role"]:
        x("DELETE FROM tb_user WHERE id_user=%s", (row["id_user"],))
    else:
        x(f"DELETE FROM {e['table']} WHERE {e['pk']}=%s", (pk,))
    flash("Data sudah dihapus.", "ok")
    return redirect(url_for("adm_list", ent=ent))


def data_laporan(kode):
    """Data untuk 4 laporan. Dipakai halaman laporan dan halaman cetak."""
    return dict(
        kode=kode,
        matkul=opt_matkul(),
        rekap=q(
            """SELECT jenis_kelamin_mhs AS jenis_kelamin, COUNT(*) AS total_mahasiswa
                   FROM tb_mhs GROUP BY jenis_kelamin_mhs"""
        ),
        rata=q(
            """SELECT m.nim_mhs, m.nama_mhs, COUNT(n.kode_mk) AS jumlah_matkul_diambil,
                         ROUND(AVG(n.nilai_akhir), 2) AS rata_rata_nilai_akhir
                  FROM tb_mhs m LEFT JOIN tb_nilai n ON m.nim_mhs = n.nim_mhs
                  GROUP BY m.nim_mhs, m.nama_mhs"""
        ),
        beban=q(
            """SELECT d.nidn_dosen, d.nama_dosen, COUNT(j.kode_mk) AS total_matkul_diampu
                   FROM tb_dosen d LEFT JOIN tb_jadwal_kelas j ON d.nidn_dosen = j.nidn_dosen
                   GROUP BY d.nidn_dosen, d.nama_dosen"""
        ),
        ranking=q(
            """SELECT m.nim_mhs, m.nama_mhs, n.nilai_akhir, n.nilai_huruf
                     FROM tb_nilai n JOIN tb_mhs m ON n.nim_mhs = m.nim_mhs
                     WHERE n.kode_mk = %s ORDER BY n.nilai_akhir DESC""",
            (kode,),
        ),
    )


@app.route("/admin/laporan")
@role("Admin")
def adm_laporan():
    kode = request.args.get("kode_mk") or "04.0103.01"
    return render_template("laporan.html", **data_laporan(kode))


BULAN = ["Januari", "Februari", "Maret", "April", "Mei", "Juni", "Juli",
         "Agustus", "September", "Oktober", "November", "Desember"]
BAGIAN_CETAK = ("semua", "rekap", "rata", "beban", "ranking")


@app.route("/admin/laporan/cetak")
@role("Admin")
def adm_laporan_cetak():
    """Halaman laporan versi cetak (A4). ?bagian=semua|rekap|rata|beban|ranking"""
    kode = request.args.get("kode_mk") or "04.0103.01"
    bagian = request.args.get("bagian", "semua")
    if bagian not in BAGIAN_CETAK:
        bagian = "semua"
    data = data_laporan(kode)
    nama_mk = next((m["t"] for m in data["matkul"] if m["v"] == kode), kode)
    wib = datetime.now(timezone(timedelta(hours=7)))  # waktu server -> WIB
    tanggal = f"{wib.day} {BULAN[wib.month - 1]} {wib.year}, {wib:%H.%M} WIB"
    return render_template(
        "cetak_laporan.html", bagian=bagian, nama_mk=nama_mk, tanggal=tanggal, **data
    )


@app.errorhandler(403)
def forbidden(_):
    return render_template("login.html", forbidden=True), 403


if __name__ == "__main__":
    app.run(debug=os.getenv("FLASK_DEBUG") == "1")  # lokal: set FLASK_DEBUG=1
