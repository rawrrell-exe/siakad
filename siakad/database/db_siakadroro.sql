CREATE DATABASE db_siakadroro;
USE db_siakadroro;

CREATE TABLE tb_user (
    id_user BIGINT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) NOT NULL UNIQUE,
    password VARCHAR(255) NOT NULL,
    role_user ENUM('Admin', 'Dosen', 'Mahasiswa') NOT NULL
);

CREATE TABLE tb_kelas (
    id_kelas BIGINT AUTO_INCREMENT PRIMARY KEY,
    nama_kelas VARCHAR(50) NOT NULL
);

CREATE TABLE tb_matkul (
    kode_mk VARCHAR(30) PRIMARY KEY,
    nama_matkul VARCHAR(255) NOT NULL,
    sks_matakuliah INT
);

CREATE TABLE tb_tendik_ftikom (
    nip_tendik BIGINT AUTO_INCREMENT PRIMARY KEY,
    id_user BIGINT NOT NULL,
    nama_tendik VARCHAR(255) NOT NULL,
    jenis_kelamin_tendik ENUM('Man', 'Woman') NOT NULL,
    email_tendik VARCHAR(255) NOT NULL UNIQUE,
    no_tlp_tendik VARCHAR(30) NOT NULL,
    alamat_tendik TEXT,
    FOREIGN KEY (id_user) REFERENCES tb_user(id_user) ON DELETE CASCADE ON UPDATE CASCADE
);

CREATE TABLE tb_dosen (
    nidn_dosen BIGINT AUTO_INCREMENT PRIMARY KEY,
    id_user BIGINT NOT NULL,
    nama_dosen VARCHAR(255) NOT NULL,
    jenis_kelamin_dosen ENUM('Man', 'Woman') NOT NULL,
    pendidikan_terakhir_dosen VARCHAR(255) NOT NULL,
    email_dosen VARCHAR(255) NOT NULL UNIQUE,
    no_tlp_dosen VARCHAR(30) NOT NULL,
    alamat_dosen TEXT,
    FOREIGN KEY (id_user) REFERENCES tb_user(id_user) ON DELETE CASCADE ON UPDATE CASCADE
);

CREATE TABLE tb_mhs (
    nim_mhs BIGINT  AUTO_INCREMENT PRIMARY KEY,
    id_user BIGINT NOT NULL,
    id_kelas BIGINT,
    nama_mhs VARCHAR(255) NOT NULL,
    jenis_kelamin_mhs ENUM('Man', 'Woman') NOT NULL,
    prodi_mhs VARCHAR(30),
    fakultas_mhs VARCHAR(10),
    angkatan_mhs VARCHAR(10),
    FOREIGN KEY (id_user) REFERENCES tb_user(id_user) ON DELETE CASCADE ON UPDATE CASCADE,
    FOREIGN KEY (id_kelas) REFERENCES tb_kelas(id_kelas) ON DELETE SET NULL ON UPDATE CASCADE
);

CREATE TABLE tb_nilai (
    id_nilai BIGINT AUTO_INCREMENT  PRIMARY KEY,
    nim_mhs BIGINT,
    kode_mk VARCHAR(30),
    nilai_akhir DECIMAL(3,2),
    nilai_huruf VARCHAR(15),
    FOREIGN KEY (nim_mhs) REFERENCES tb_mhs(nim_mhs) ON DELETE SET NULL ON UPDATE CASCADE,
    FOREIGN KEY (kode_mk) REFERENCES tb_matkul(kode_mk) ON DELETE SET NULL ON UPDATE CASCADE
);

CREATE TABLE tb_jadwal_kelas (
    id_jadwal BIGINT AUTO_INCREMENT PRIMARY KEY,
    id_kelas BIGINT,
    kode_mk VARCHAR(30),
    nidn_dosen BIGINT,
    hari ENUM('Senin','Selasa','Rabu','Kamis','Jumat','Sabtu') Not NULL,
    jam VARCHAR(50),
    ruangan VARCHAR(255),
    FOREIGN KEY (id_kelas) REFERENCES tb_kelas(id_kelas) ON DELETE SET NULL ON UPDATE CASCADE,
    FOREIGN KEY (kode_mk) REFERENCES tb_matkul(kode_mk) ON DELETE SET NULL ON UPDATE CASCADE,
    FOREIGN KEY (nidn_dosen) REFERENCES tb_dosen(nidn_dosen) ON DELETE SET NULL ON UPDATE CASCADE
);

INSERT INTO tb_user (username, password, role_user) VALUES
('admin1', 'admin1', 'Admin'),
('admin2', 'admin2', 'Admin'),
('admin3', 'admin3', 'Admin'),
('admin4', 'admin4', 'Admin'),
('admin5', 'admin5', 'Admin'),
('admin6', 'admin6', 'Admin'),
('admin7', 'admin7', 'Admin'),
('admin8', 'admin8', 'Admin'),
('admin9', 'admin9', 'Admin'),
('admin10', 'admin10', 'Admin'),
('aliyah', 'aliyah', 'Dosen'),
('debyo', 'debyo', 'Dosen'),
('pungy', 'pungy', 'Dosen'),
('kamaluddin', 'kamaluddin', 'Dosen'),
('vera', 'vera', 'Dosen'),
('latifatu', 'latifatu', 'Dosen'),
('erwin', 'erwin', 'Dosen'),
('nurwadji', 'nurwadji', 'Dosen'),
('wiranti', 'wiranti', 'Dosen'),
('hana', 'hana', 'Dosen'),
('roro', 'roro35', 'Mahasiswa'),
('rizky', 'rizky18', 'Mahasiswa'),
('rima', 'rima70', 'Mahasiswa'),
('nadya', 'nadya71', 'Mahasiswa'),
('bayu', 'bayu56', 'Mahasiswa'),
('azizah', 'azizah75', 'Mahasiswa'),
('wafika', 'wafika77', 'Mahasiswa'),
('nayla', 'nayla58', 'Mahasiswa'),
('syifa', 'syifa97', 'Mahasiswa'),
('nanda', 'nanda96', 'Mahasiswa');

INSERT INTO tb_kelas (id_kelas, nama_kelas) VALUES
(1101, '1TI01'),
(1102, '1TI02'),
(1201, '1TE01'),
(2101, '2TI01'),
(2102, '2TI02'),
(2201, '2TE01'),
(3101, '3TI01'),
(3102, '3TI02'),
(3201, '3TE01'),
(4101, '4TI01'),
(4102, '4TI02'),
(4201, '4TE01');

INSERT INTO tb_matkul (kode_mk, nama_matkul, sks_matakuliah) VALUES
('04.0103.01', 'Pengantar Sistem Basis Data', 2),
('04.0103.02', 'Organisasi dan Arsitektur Komputer', 3),
('04.0103.03', 'E-commerce', 2),
('04.0103.04', 'Pendidikan Anti Korupsi', 2),
('04.0103.05', 'Bahasa Indonesia', 2),
('04.0103.06', 'Al Izzah Al Islamiyah', 2),
('04.0103.07', 'Pancasila', 2),
('04.0103.08', 'Pengantar Struktur Data', 2),
('04.0103.09', 'Legal, Aspek, dan Bisnis TI', 2),
('04.0103.10', 'Matematika Informatika 2 Matematika Diskrit', 2);

INSERT INTO tb_tendik_ftikom (nip_tendik, id_user, nama_tendik, jenis_kelamin_tendik, email_tendik, no_tlp_tendik, alamat_tendik) VALUES
(20201, 1, 'Aurelia, S.Kom', 'Woman', 'tendik1@ftikom.ac.id', '081200000001', 'Tangerang'),
(20202, 2, 'Handi Al-Ghazali, S.Kom', 'Man', 'tendik2@ftikom.ac.id', '081200000002', 'Tangerang'),
(20203, 3, 'Feiy Saputri, S.Kom', 'Woman', 'tendik3@ftikom.ac.id', '081200000003', 'Tangerang'),
(20204, 4, 'Nana Derly, S.Kom', 'Woman', 'tendik4@ftikom.ac.id', '081200000004', 'Tangerang'),
(20205, 5, 'Evandra Dio, S.Kom', 'Man', 'tendik5@ftikom.ac.id', '081200000005', 'Tangerang'),
(20206, 6, 'Fadil, S.Kom', 'Man', 'tendik6@ftikom.ac.id', '081200000006', 'Tangerang'),
(20207, 7, 'Cindy, S.T', 'Woman', 'tendik7@ftikom.ac.id', '081200000007', 'Tangerang'),
(20208, 8, 'Nazila, S.Kom', 'Woman', 'tendik8@ftikom.ac.id', '081200000008', 'Tangerang'),
(20209, 9, 'Azizah Lubis, S.Kom', 'Woman', 'tendik9@ftikom.ac.id', '081200000009', 'Tangerang'),
(20210, 10, 'Jihan Najla, S.Kom', 'Woman', 'tendik10@ftikom.ac.id', '081200000010', 'Tangerang');

INSERT INTO tb_dosen (nidn_dosen, id_user, nama_dosen, jenis_kelamin_dosen, pendidikan_terakhir_dosen, email_dosen, no_tlp_dosen, alamat_dosen) VALUES
(20140101, 11, 'Aliyah, S.Kom, M.T.I.', 'Woman', 'S2', 'dosen1@dosen.ac.id', '081300000001', 'Tangerang'),
(20140201, 12, 'Dr. Ir. Debyo Saptono, S.T.', 'Man', 'S3', 'dosen2@dosen.ac.id', '081300000002', 'Tangerang'),
(20140102, 13, 'Pungky Hari Wijaya, S.Kom', 'Man', 'S2', 'dosen3@dosen.ac.id', '081300000003', 'Tangerang'),
(20100001, 14, 'Kamaluddin, S.IP., M.Si.', 'Man', 'S2', 'dosen4@dosen.ac.id', '081300000004', 'Jakarta'),
(20140103, 15, 'Vera Nurlia, S.Pd., M.Pd.', 'Woman', 'S2', 'dosen5@dosen.ac.id', '081300000005', 'Tangerang'),
(20130062, 16, 'Dr. H. Latifatu H., M.A.', 'Woman', 'S3', 'dosen6@dosen.ac.id', '081300000006', 'Serang'),
(20100003, 17, 'Erwin Firmansyah, S.H.', 'Man', 'S3', 'dosen7@dosen.ac.id', '081300000007', 'Tangerang'),
(20100101, 18, 'Nurwadji, S.H., M.M.', 'Man', 'S2', 'dosen8@dosen.ac.id', '081300000008', 'Tangerang'),
(20140104, 19, 'Wiranti Sri U., S.Kom, M.T.I.', 'Woman', 'S2', 'dosen9@dosen.ac.id', '081300000009', 'Tangerang'),
(20140202, 20, 'Helmi Fauziah Y., S.Kom, M.T.', 'Woman', 'S2', 'dosen10@dosen.ac.id', '081300000010', 'Tangerang');

INSERT INTO tb_mhs (nim_mhs, id_user, id_kelas, nama_mhs, jenis_kelamin_mhs, prodi_mhs, fakultas_mhs, angkatan_mhs) VALUES
(2522105035, 21, 2101, 'Roro Aurelia Anggita P. K.', 'Woman', 'TI', 'FTIKom', 2025),
(2522105018, 22, 2101, 'Muhammad Rizki Handi A.', 'Man', 'TI', 'FTIKom', 2025),
(2522105070, 23, 2101, 'Rima Feiy Saputri', 'Woman', 'TI', 'FTIKom', 2025),
(2522105071, 24, 2101, 'Nadya Derly Ardianty', 'Woman', 'TI', 'FTIKom', 2025),
(2522105056, 25, 2101, 'Muhammad Bayu P.', 'Man', 'TI', 'FTIKom', 2025),
(2522105075, 26, 2101, 'Siti Azizah Lubis', 'Woman', 'TI', 'FTIKom', 2025),
(2522105077, 27, 2101, 'Wafiqa Rahma', 'Woman', 'TI', 'FTIKom', 2025),
(2522105058, 28, 2101, 'Nayla Sensabila', 'Woman', 'TI', 'FTIKom', 2025),
(2522105097, 29, 2101, 'Asyifa Ponggabean', 'Woman', 'TI', 'FTIKom', 2025),
(2522105096, 30, 2101, 'Cantikha Nahda Ashila', 'Woman', 'TI', 'FTIKom', 2025);

INSERT INTO tb_nilai (id_nilai, nim_mhs, kode_mk, nilai_akhir, nilai_huruf) VALUES
(1, 2522105035, '04.0103.01', 3.98, 'A'),
(2, 2522105018, '04.0103.01', 3.98, 'A'),
(3, 2522105070, '04.0103.01', 3.92, 'A'),
(4, 2522105071, '04.0103.01', 3.93, 'A'),
(5, 2522105056, '04.0103.01', 3.90, 'A'),
(6, 2522105075, '04.0103.01', 3.99, 'A'),
(7, 2522105077, '04.0103.01', 3.92, 'A'),
(8, 2522105058, '04.0103.01', 3.91, 'A'),
(9, 2522105097, '04.0103.01', 3.95, 'A'),
(10, 2522105096, '04.0103.01', 3.95, 'A');

INSERT INTO tb_jadwal_kelas (id_jadwal, id_kelas, kode_mk, nidn_dosen, hari, jam, ruangan) VALUES
(1, 2101, '04.0103.01', 20140101, 'Senin', '08.00-09.40', 'A205'),
(2, 2101, '04.0103.02', 20140201, 'Senin', '10.00-12.30', 'A205'),
(3, 2101, '04.0103.03', 20140102, 'Senin', '13.00-14.40', 'A205'),
(4, 2101, '04.0103.04', 20100001, 'Selasa', '10.00-11.40', 'A205'),
(5, 2101, '04.0103.05', 20140103, 'Selasa', '13.00-14.40', 'A205'),
(6, 2101, '04.0103.06', 20130062, 'Rabu', '10.00-11.40', 'A205'),
(7, 2101, '04.0103.07', 20100003, 'Rabu', '13.00-14.40', 'A205'),
(8, 2101, '04.0103.08', 20140101, 'Kamis', '08.00-09.40', 'A205'),
(9, 2101, '04.0103.09', 20100101, 'Kamis', '10.00-11.40', 'A205'),
(10, 2101, '04.0103.10', 20140202, 'Kamis', '13.00-14.40', 'A205');

