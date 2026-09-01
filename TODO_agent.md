# TODO — ZZZ Damage Calculator (untuk AI agent lanjutan)

Update terbaru: `damage_calc.py` SUDAH JADI dan lolos kalibrasi. Formula
sudah dikonfirmasi cocok ke halaman resmi wiki
(`zenless-zone-zero.fandom.com/wiki/Damage`), bukan cuma "kebetulan cocok"
ke 1 kasus. File ini cuma daftar kerjaan aktif — konteks lengkap ada di
`SKILL_DATA_PROGRESS.md` / `readme3.md` / `wengine.md`.

## 🔴 Prioritas utama — Level Factor generality

**Bug/gap yang ketemu**: konstanta `794` di `compute_def_mult()` itu
**hardcode khusus attacker level 60**. Wiki resmi confirm "Level Factor"
itu scaling per level (pola growth mirip DEF musuh per level), jadi kalau
dipake buat karakter level < 60, DEF Mult-nya bakal SALAH tanpa ada
warning apapun (silent wrong number).

- [ ] Cek `LevelCurveTemplateTb.json` (udah ada di folder upload terakhir)
      — kemungkinan ini tabel Level Factor per level yang dicari
- [ ] Kalau ketemu: extract formula/tabel-nya, ganti `794` hardcode di
      `compute_def_mult()` jadi lookup dinamis berdasar level attacker
- [ ] Kalibrasi ulang ke ground truth (1086/2961, Miyabi level 60) — pastiin
      lookup level 60 dari tabel baru = 794 persis (sanity check)
- [ ] Kalau nemu, cross-check juga bisa dipake buat DEF musuh per level
      (wiki bilang "Enemy DEF di level 1 biasanya 36-60, growth pattern
      sama kayak Level Factor" — mungkin related ke misteri Monster data)

## 🟡 Sudah dicoba, dead end — jangan diulang tanpa clue baru

- [x] ~~Cari data Monster (DEF/RES Tyrfing) di MonsterConfigTemplateTb.json
      + MonsterSubTemplateTb.json~~ — DEAD END (lihat versi TODO
      sebelumnya buat detail). DEF Tyrfing (`572`) tetap hardcode manual
      dengan comment eksplisit di kode.
  - **Clue baru buat dicoba**: kalau Level Factor curve ketemu di
    `LevelCurveTemplateTb.json`, mungkin ada pola/field serupa yang bisa
    dipakai buat crack DEF musuh per level juga (worth re-visit setelah
    item Level Factor di atas selesai)

## 🟢 Selesai & tervalidasi (jangan dikerjain ulang)

- [x] Stat panel karakter (base+gear+set 2pc+W-Engine stat+Core Skill)
- [x] Skill multiplier (formula+naming 91.4%+hidden hit flag)
- [x] W-Engine passive (`wengine_passive_mapped.json`) — fabrication lama
      sudah fixed, 73 effect re-verified, 0 mismatch nyata
- [x] Set 4pc (`drive_disc_mapped.json`) — 30/30 suit, teks mentah
      disertakan
- [x] Mindscape M1/M2/M4/M6 (`mindscape_mapped.json`) — 58 karakter,
      evidence-based
- [x] **`damage_calc.py` — SELESAI dan LOLOS kalibrasi**:
  - Loader 3 file mapped, generic (terima weapon_id/set_name/avatar_id
    sebagai parameter, bukan hardcode)
  - Toggle list auto-generate dari 3 sumber, auto-enable unconditional,
    auto-evaluate threshold (mis. Anomaly Mastery >= 115)
  - `compute_final_damage()` — formula CONFIRMED match wiki resmi
    (DEF Mult identik 100%, RES Mult sudah punya slot res_ignore_pcts +
    res_shred_pct meski belum di-exercise di kalibrasi)
  - Tes generalisasi ke kombinasi lain (weapon phase 3, set Thorned Rose,
    Anby M3) — SEMUA match ke sumber independen (wiki table Thorned Rose
    persis cocok)
  - Kalibrasi Miyabi vs Tyrfing: selisih 0.03-0.08% (PASS, toleransi 0.5%)

## Open items lain (prioritas rendah, nggak blocking)

- [ ] Fungsi gameplay hidden hits (119 hit di 40 karakter) — kapan mereka
      trigger di combat asli. Lead: `1091035` Miyabi kemungkinan
      "Frostburn - Break" (scaling ke Core Skill level, verified
      750%->1500% linear +130%/level Core Lv1->Lv7), tapi baru 1 dari 119.
- [ ] Residual kalibrasi 0.09% (1085 vs 1086 ground truth) — kemungkinan
      terkait Level Factor hardcode di atas, cek ulang setelah item
      prioritas utama selesai (mungkin auto-fix begitu Level Factor jadi
      presisi penuh, bukan 794 approx)

## Catatan metodologi (jangan dilanggar)

1. Source of truth kalau ada konflik: **JSON mentah**, bukan wiki biligame
2. Selalu cross-check ke **Prydwen** atau **wiki fandom resmi**
   (zenless-zone-zero.fandom.com), bukan biligame
3. Jangan generalize pola dari 1 karakter — validasi ke minimal 2-3
   karakter struktur beda dulu
4. **Verifikasi ulang file "mapped" apapun** yang di-generate agent lain
   sebelum dipercaya — pernah ketemu fabrication (W-Engine CRIT Rate 10%
   dicopy dari weapon lain, ditandain `mapped: true` padahal salah).
   Cross-check ke raw text/JSON dulu.
5. Untuk conditional effects (W-Engine passive, set 4pc, mindscape):
   pakai TOGGLE MANUAL (`enabled: bool`), JANGAN coba deteksi trigger
   otomatis — di luar scope (butuh simulasi combat real-time).
6. **Formula damage sudah dikonfirmasi match wiki resmi** — kalau ada
   penyesuaian formula ke depan, cross-check dulu ke
   `zenless-zone-zero.fandom.com/wiki/Damage` sebelum ubah, jangan
   asumsi dari kalibrasi 1 kasus doang.
