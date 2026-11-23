USE db_siakadroro;

ALTER TABLE tb_nilai ADD UNIQUE KEY uq_nilai_mhs_mk (nim_mhs, kode_mk);

CREATE INDEX idx_jadwal_kelas ON tb_jadwal_kelas (id_kelas);
CREATE INDEX idx_jadwal_dosen ON tb_jadwal_kelas (nidn_dosen);
