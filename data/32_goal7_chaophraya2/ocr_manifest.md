# OCR ภาษาไทย — ทะเบียนผล (เป้าหมาย 7)

> สร้าง 16 ต.ค. 2569 · เครื่องมือ: `analysis/goal7_ocr.py` (RapidOCR + onnxruntime CPU · venv `E:/theera/ocr_env` นอก repo · ดู docs/ENVIRONMENT.md) · 200 dpi (หน้ากระดานโปสเตอร์ใหญ่เกิน → 80 dpi อัตโนมัติ: `ph2_4_*` 3 หน้า คุณภาพต่ำกว่า)
> ผลบนดิสก์เท่านั้น: `data/32_goal7_chaophraya2/ocr/<label>/{pages.jsonl,text.txt}` (ไม่เข้า git — มีชื่อบุคคลในเอกสารต้นฉบับ) · ข้อเท็จจริงที่ตรวจแล้วอยู่ใน `analysis/goal7/canonical.json → ocr_facts`
> ค้นคำสำคัญ: `analysis/goal7_ocr_scan.py` → `analysis/goal7/ocr_findings.json` · **ผล OCR ใช้ค้นหา ไม่ใช่ข้อความอ้างอิง** (วรรณยุกต์/สระอ่านผิดได้ — ต้องตรวจภาพหน้า)

## เวอร์ชัน

- Name: rapidocr
- Version: 3.10.0
- Name: onnxruntime
- Version: 1.31.0

## โมเดล (SHA-256)

- `ch_ppocr_mobile_v2.0_cls_mobile.onnx` — `e47acedf663230f8863ff1ab0e64dd2d82b838fceb5957146dab185a89d6215c`
- `PP-OCRv6_det_small.onnx` — `090f04abcd9d9a7498bc4ebf677e4cb9bdce1fe4197ddb7e529f1ef44e1ff94f`
- `th_PP-OCRv5_rec_mobile.onnx` — `de541dd83161c241ff426f7ecfd602a0ba77d686cf3ab9a6c255ea82fd08006e`

## เอกสารที่แปลง

| label | ไฟล์ต้นทาง | หน้าที่ขอ | หน้าที่ได้ | ผิดพลาด | SHA-256 ต้นทาง | SHA-256 pages.jsonl | SHA-256 text.txt |
|---|---|---|---|---|---|---|---|
| letter54_measures | มาตรการที่เป็นหนังสือแนบท้าย.pdf | ทุกหน้า | 54 | 0 | `d8d3736227893ba2d2b8d32748cb1f2a8615f43bde3b8d422e5382d168e1e093` | `776ed9b133acd26012629bf4462a37857e3f376b6e253d1a01ecc8a460044d8f` | `e6f6ac2ba73da3c8f9975aacb6fb4f4b0b387531923b63fcdcb7bf69f62c2dd7` |
| eia2569_app1_imgpages | EIA ทางระบายน้ำหลาก_ภาคผนวก เล่ม 1-1790751406.pdf | 250 | 250 | 0 | `69b2a60b72ff33be0d5acc645bca6d83effcd20b023cc644b67ea58dc2178f5d` | `7260983dc1191a19b7bf59c7e5b28cd3d23d7977890afcb4425408c8bcece165` | `9cdf6de31d6a618e415f38c619a4e9e9d1968a21fd2022c6ebf94842a4e8c8ae` |
| eia2569_app2_imgpages | EIA ทางระบายน้ำหลาก_ภาคผนวก เล่ม 2-1790751446.pdf | 192 | 192 | 0 | `b5ac2e6dfcd0dae445de5d4c4818f37c18c635cb89c0cc09ab6194af59057e0b` | `2ddf5cf1a7fa14679ee56ef2fda413cc353d8a0d019c3e175a835710eaea18b2` | `21b0c50f2a6795cdceece51d1f7be62e7982c518f8c981105ae75175b1b6ba03` |
| eia2569_main1_imgpages | EIA ทางระบายน้ำหลาก_สมบูรณ์ เล่ม 1-1790751309.pdf | 64 | 64 | 0 | `a8c9afc6ed7580f8529ddb47d0ddbc069a0a42c70eee97d73a7761c27c0930bc` | `70dc1addff2487cd8c74ab6478e0cab1f83df20f599e3c0b19969d838478bb6d` | `9c8c600feb20dd1a31bd2dcc160c4183d6a35fd0a33debaf6f87bc392af1eb8c` |
| eia2569_main2_imgpages | EIA ทางระบายน้ำหลาก_สมบูรณ์ เล่ม 2-1790751358.pdf | 2 | 2 | 0 | `400e90e899899fb27bfcf8eb419d2cce66a598764e2f768b2a8163e14b6d14fb` | `e44536a4125d856b90b557a56b1f2ac5418726cdcfae177eb753948c438310c5` | `16b03888227a031ad20eefcd4fc3c6fa90aa143952de150f6399af911a4321c0` |
| ph1_group1_draft | ป่าสักอ่าวไทย_ร่างกลุ่มย่อย1_A4.pdf | ทุกหน้า | 12 | 0 | `733c39a41846e41ee3359c353c07d28fbafd88589790797ae1d11aeb70cd500f` | `0f1ea8553443298996f07973227a618a1a5ab849998b4a967fb68badd0cfa825` | `14de2887ac9c0023dc05b508ed84b43bd7d4ae60bf83251e328ea3e0294c95ad` |
| ph1_group2_doc | ป่าสักอ่าวไทย_เอกสาร กลุ่มย่อย2 _A4 final.pdf | ทุกหน้า | 12 | 0 | `205ce8196ecd590cc63242582170fb7324a4e44d8b102ecb9454c4ac23dcbdc0` | `5e20fe07f082bc693f3830c2d93a134123841b07df0723b2130d2b0f2c42781e` | `188b41d0651873a55051bd451bb1feb9591c6d4b63f480743f461e8154b109a5` |
| ph1_closing | นำเสนอปัจฉิมนิเทศ_29-30_05_66.pdf | ทุกหน้า | 57 | 0 | `781d444f4d6e4f3bab504c50d2c869fe73404675ad5fcf2659d68eed404b238f` | `3b41241e3472885d0153af56cf68134111c63df5fee1933745ffdd34968361ff` | `0c4615d89c38b85f1f19fc1c6e8fdd86daa74e4d01ea20bbc6bc335428661d2e` |
| ph2_1_บอร์ด_ปฐมนิเทศป่าสักอ่าวไทย_ระ | บอร์ด ปฐมนิเทศป่าสักอ่าวไทย ระยะที่ 2.pdf | ทุกหน้า | 7 | 0 | `9d3e435f64bf5a743dbcaa827b644c773e55f723fe86c6f53dad137cb40bcdca` | `69cd215ff43fd81405a72cde316fc9f197e37815287dd87e5d0d857a202cfb42` | `560bcd3151b8c95e17f070e0bf62daf3d8a8c1c33382109a192072f9e2682152` |
| ph2_2_สรปผลการประชุมปฐมนิเทศ_(16-17_ | สรปผลการประชุมปฐมนิเทศ (16-17 02 2566).pdf | ทุกหน้า | 11 | 0 | `9a38153c2f8380c5055b0c0ddbfc9882581edd1d5eaeaff3421e90ce6a059405` | `8eaca9c8f45b278e92368b7aad06767d35057c07dd6342765ac820bd237ce227` | `81d578728e3a31e9773a397967897c9ab2a70e224e9edb7af7a60c22035479b2` |
| ph2_3_เอกสารปฐมนิเทศ_ป่าสัก-อ่าวไทย_ | เอกสารปฐมนิเทศ ป่าสัก-อ่าวไทย ระยะที่ 2.pdf | ทุกหน้า | 11 | 0 | `4e94b295934d8d494b2846fe9bd2951acd1b17e1168a61ebb38bef240628531d` | `6b1c8c5208540770db3a1990e8d59a8f2412ad0eba79a4e060b14a6f2dee2d70` | `73e9f24ad4c8a5be987149a08d55aaf20d16bbbd1289cf5e3791b66ae0566218` |
| ph2_4_บอร์ดกลุ่มย่อย_1_ป่าสัก-อ่าวไท | บอร์ดกลุ่มย่อย 1 ป่าสัก-อ่าวไทย ระยะที่ 2.pdf | ทุกหน้า | 4 | 0 | `3125a982ec2ea2929c0106c98b2357b07139efbb15df170ce9edbd379b74ea6d` | `2faa6da9afa4d43d8191f23519ce83142f00743a344bd03aad7294e6d916a4cb` | `b632f37cb39e2dba5bf87e88898a6e7b34505bbe33b4eff3902ac1eb4b080dcf` |
| ph2_5_เอกสารกลุ่มย่อย_1_ป่าสัก-อ่าวไ | เอกสารกลุ่มย่อย 1 ป่าสัก-อ่าวไทย ระยะที่ 2.pdf | ทุกหน้า | 6 | 0 | `2356d2ace0d2d0e4d2e44740e70623ae16406a93163191cae995d862ac1215b7` | `ea04f497705638ec0ce6cd6f96049d27dab0bba91fc55932bad82548814ee472` | `c7147c70f8106d953b5c6ee1f73d2058939cef14d4149bb858f5b172d271bf8e` |

หมายเหตุ: ไฟล์ต้นทางของเล่ม EIA 2569 แตกจาก `official_eia/256909-65.zip` (แฮชของ zip อยู่ใน `official_eia/hashes.sha256`) · เลือกเฉพาะหน้าที่ไม่มีชั้นข้อความ (<40 ตัวอักษร)
