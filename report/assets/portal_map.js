/**
 * report/assets/portal_map.js — คอมโพเนนต์แผนที่สืบค้นเชิงโต้ตอบ (Interactive Knowledge Atlas)
 * สำหรับ index.html (รองรับ GitHub Pages 100% แบบ Zero-Backend Static Architecture)
 */

(function () {
  'use strict';

  // พิกัดและข้อมูลของ 3 เสาหลัก
  const DATA = {
    stations: [
      {
        id: "ny1b",
        name: "สถานี Ny.1B (บ้านเขานางบวช)",
        lat: 14.2882,
        lng: 101.2784,
        pillar: "p1",
        river: "แม่น้ำนครนายก",
        type: "โทรมาตรวัดระดับน้ำ",
        bankfull: "666.3 ลบ.ม./วิ (10.60 ม.รทก.)",
        peak: "11.00 ม.รทก. (27 ก.ย. 69)",
        desc: "จุดรับน้ำหลักจากเขื่อนขุนด่านฯ ก่อนเข้าเขตเทศบาลเมืองนครนายก",
        link: "report/น้ำท่วมนครนายก2569_วิชาการ.html#sec-hydraulics"
      },
      {
        id: "ny7",
        name: "สถานี Ny.7 (สะพานเทศบาลนครนายก)",
        lat: 14.2058,
        lng: 101.2131,
        pillar: "p1",
        river: "แม่น้ำนครนายก",
        type: "โทรมาตรวัดระดับน้ำ",
        bankfull: "617.4 ลบ.ม./วิ (8.21 ม.รทก. / ชานพัก 6.86 ม.)",
        peak: "9.23 ม.เกจ / 7.64 ม.รทก. (27 ก.ย. 69)",
        desc: "สถานีควบคุมในเขตเทศบาลเมืองนครนายก น้ำเริ่มเอ่อท่วมที่ 8.45 ม.เกจ",
        link: "report/น้ำท่วมนครนายก2569_ประชาชน.html"
      },
      {
        id: "c2",
        name: "สถานี C.2 (นครสวรรค์)",
        lat: 15.6708,
        lng: 100.1264,
        pillar: "p2",
        river: "แม่น้ำเจ้าพระยา",
        type: "โทรมาตรวัดอัตราไหล",
        bankfull: "3,590 ลบ.ม./วิ (26.20 ม.รทก.)",
        peak: "2,120 ลบ.ม./วิ (ต.ค. 69)",
        desc: "จุดวัดน้ำหลากรวมจาก 4 แควเหนือ (ปิง วัง ยม น่าน) ก่อนลงสู่เขื่อนเจ้าพระยา",
        link: "report/ระลอกปลายกย2569.html"
      },
      {
        id: "c13",
        name: "สถานี C.13 (เขื่อนเจ้าพระยา ชัยนาท)",
        lat: 15.1583,
        lng: 100.1808,
        pillar: "p2",
        river: "แม่น้ำเจ้าพระยา",
        type: "เขื่อนทดน้ำหลัก",
        bankfull: "2,840 ลบ.ม./วิ (ระดับเตือนภัย)",
        peak: "2,199 ลบ.ม./วิ (ระบายสูงสุด ก.ย.–ต.ค. 69)",
        desc: "หัวใจการบริหารน้ำหลากสู่ภาคกลางและจุดเริ่มต้นผันน้ำของคลองเจ้าพระยา 2",
        link: "report/ชุดเทียบมาตรฐาน2554.html"
      },
      {
        id: "c29a",
        name: "สถานี C.29A (บางไทร อยุธยา)",
        lat: 14.2028,
        lng: 100.5056,
        pillar: "p2",
        river: "แม่น้ำเจ้าพระยา",
        type: "จุดบรรจบลุ่มน้ำตอนล่าง",
        bankfull: "3,500 ลบ.ม./วิ (จุดเฝ้าระวัง กทม.)",
        peak: "2,250 ลบ.ม./วิ (2569) vs 3,750 ลบ.ม./วิ (2554)",
        desc: "จุดรวมน้ำหลากจากเจ้าพระยาและแม่น้ำป่าสัก ก่อนเข้าสู่พื้นที่กรุงเทพมหานคร",
        link: "report/ระลอกปลายกย2569.html"
      },
      {
        id: "c12",
        name: "สถานี C.12 (สามเสน กทม.)",
        lat: 13.7847,
        lng: 100.5083,
        pillar: "p2",
        river: "แม่น้ำเจ้าพระยา",
        type: "โทรมาตรวัดระดับน้ำ",
        bankfull: "2.80 ม.รทก. (สันคันกั้นน้ำ กทม.)",
        peak: "2.24 ม.รทก. (ปลาย ก.ย. 69)",
        desc: "สถานีหลักเฝ้าระวังน้ำท่วม กทม. อิทธิพลผสมระหว่างน้ำหลากและน้ำทะเลหนุน",
        link: "report/ระลอกปลายกย2569.html"
      },
      {
        id: "cpy015",
        name: "สถานี CPY015 (สะพานกรุงเทพ ปากแม่น้ำ)",
        lat: 13.7042,
        lng: 100.4931,
        pillar: "p2",
        river: "ปากแม่น้ำเจ้าพระยา",
        type: "สถานีวัดน้ำขึ้น–น้ำลงปากอ่าว",
        bankfull: "2.50 ม.รทก. (น้ำเกิดสูงสุด)",
        peak: "2.40 ม.รทก. (ช่วงน้ำเกิด 26–28 ก.ย. 69)",
        desc: "ขอบเขตทะเลหนุนที่ใช้ในแบบจำลองพยากรณ์ระยะสั้น L3 Coastal (ใช้ได้ที่ระยะไม่เกิน 6 ชม. เท่านั้น)",
        link: "report/ระลอกปลายกย2569.html"
      },
      {
        id: "samlae",
        name: "สถานีสำแล (ปทุมธานี)",
        lat: 14.0042,
        lng: 100.5400,
        pillar: "p2",
        river: "แม่น้ำเจ้าพระยา",
        type: "สถานีวัดลิ่มความเค็มประปา",
        bankfull: "0.25 กรัม/ลิตร (เกณฑ์มาตรฐานประปา)",
        peak: "0.14 กรัม/ลิตร (ช่วงน้ำหลาก 2569 ปกติดี)",
        desc: "จุดสูบน้ำดิบผลิตน้ำประปา กทม. ป้องกันลิ่มความเค็มรุกจากอ่าวไทย",
        link: "report/ระลอกปลายกย2569.html"
      }
    ],

    dams: [
      {
        name: "เขื่อนขุนด่านปราการชล",
        lat: 14.3142,
        lng: 101.3217,
        pillar: "p1",
        cap: "224.0 ล้าน ลบ.ม.",
        peak_storage: "224.34 ล้าน ลบ.ม. (100.1%)",
        release_peak: "31.66 ล้าน ลบ.ม./วัน (366 ลบ.ม./วิ)",
        desc: "เขื่อนคอนกรีตบดอัดแน่นที่ยาวที่สุดในโลก น้ำเต็มเร็วกว่าปกติ 40 วันในปี 2569",
        link: "report/น้ำท่วมนครนายก2569_ประชาชน.html"
      },
      {
        name: "อ่างเก็บน้ำทรายทอง",
        lat: 14.3050,
        lng: 101.3050,
        pillar: "p1",
        cap: "9.8 ล้าน ลบ.ม.",
        peak_storage: "107.7% (ล้นทางระบายน้ำฉุกเฉิน)",
        release_peak: "1.51 ล้าน ลบ.ม. (ปล่อยผ่าน 99.5%)",
        desc: "อ่างขนาดกลาง จ.นครนายก เต็มความจุและหน่วงน้ำไม่ได้ในช่วงฝนวิกฤต",
        link: "report/น้ำท่วมนครนายก2569_วิชาการ.html"
      },
      {
        name: "อ่างเก็บน้ำคลองวังบอน",
        lat: 14.2530,
        lng: 101.3720,
        pillar: "p1",
        cap: "7.7 ล้าน ลบ.ม.",
        peak_storage: "101.6% (ล้นน้ำ)",
        release_peak: "0.71 ล้าน ลบ.ม.",
        desc: "อ่างขนาดกลาง จ.นครนายก เต็ม 101.6% ล้นสู่ที่ราบตอนล่าง",
        link: "report/น้ำท่วมนครนายก2569_วิชาการ.html"
      },
      {
        name: "เขื่อนป่าสักชลสิทธิ์",
        lat: 14.8606,
        lng: 101.0772,
        pillar: "p2",
        cap: "960.0 ล้าน ลบ.ม. (เผื่อวิกฤต 1,064 ลลบ.ม.)",
        peak_storage: "1,032 ล้าน ลบ.ม. (107.5%)",
        release_peak: "450 ลบ.ม./วิ",
        desc: "เส้นฐาน 24 ปีหน่วงน้ำเกิน 100% ถึง 70.8% ของปี ยืนยันบทบาทเขื่อนหน่วงน้ำภาคกลาง",
        link: "report/ชุดเทียบมาตรฐาน2554.html"
      },
      {
        name: "เขื่อนภูมิพล",
        lat: 17.2436,
        lng: 98.9739,
        pillar: "p2",
        cap: "13,462 ล้าน ลบ.ม.",
        peak_storage: "9,291 ล้าน ลบ.ม. (69.0%)",
        release_peak: "0 วันเกินระดับกำกับบน",
        desc: "เขื่อน กฟผ. บริหารน้ำตามเกณฑ์เคร่งครัด ช่วยหน่วงน้ำหลากตอนบนได้ 100%",
        link: "report/ชุดเทียบมาตรฐาน2554.html"
      },
      {
        name: "เขื่อนสิริกิติ์",
        lat: 17.7656,
        lng: 100.5583,
        pillar: "p2",
        cap: "9,510 ล้าน ลบ.ม.",
        peak_storage: "8,210 ล้าน ลบ.ม. (86.3%)",
        release_peak: "0 วันเกินระดับกำกับบน",
        desc: "เขื่อน กฟผ. ริมแม่น้ำน่าน ไม่เคยเกินเกณฑ์กำกับตลอดฤดูฝน 2569",
        link: "report/ชุดเทียบมาตรฐาน2554.html"
      }
    ],

    canal_cp2: {
      route: [
        [15.1650, 100.1850], // เหนือเขื่อนเจ้าพระยา กม.0
        [15.0200, 100.3500],
        [14.8200, 100.6000], // ลพบุรี กม.45
        [14.5800, 100.7500], // ข้ามแม่น้ำป่าสัก ท่าหลวง กม.70
        [14.3500, 100.8800], // สระบุรี-หนองเสือ
        [14.1221, 100.9500], // ข้ามคลองรังสิต / อ.องครักษ์ กม.110
        [13.8500, 100.9200], // ฉะเชิงเทรา-บางน้ำเปรี้ยว
        [13.5500, 100.8600], // สมุทรปราการ บางพลี/คลองด่าน
        [13.4800, 100.8200]  // ปากอ่าวไทย สถานีสูบน้ำออกทะเล
      ],
      structures: [
        {
          name: "ประตูระบายน้ำปากคลองผันน้ำชัยนาท",
          lat: 15.1650,
          lng: 100.1850,
          desc: "ความจุผันน้ำ 600 ลบ.ม./วิ ตัดน้ำหลากก่อนผ่านหน้าเขื่อนเจ้าพระยา",
          link: "report/คลองเจ้าพระยา2_ประชาชน.html"
        },
        {
          name: "ไซฟอนลอดแม่น้ำป่าสัก (ท่าหลวง)",
          lat: 14.5800,
          lng: 100.7500,
          desc: "ท่อลอดคอนกรีตขนาดใหญ่ 5 ช่อง ลอดใต้แม่น้ำป่าสักโดยไม่ตัดการไหลเดิม",
          link: "report/คลองเจ้าพระยา2_วิชาการ.html"
        },
        {
          name: "จุดตัดคลองรังสิตประยูรศักดิ์ (อ.องครักษ์)",
          lat: 14.1221,
          lng: 100.9500,
          desc: "คันคลองลอยสูง 3.2–4.8 ม. ตัดผ่านพื้นที่ผังน้ำ สทนช. และพื้นที่ดินกรดจัด",
          link: "report/คลองเจ้าพระยา2_ประชาชน.html"
        },
        {
          name: "สถานีสูบน้ำและประตูระบายน้ำออกสู่อ่าวไทย",
          lat: 13.4800,
          lng: 100.8200,
          desc: "ประตูระบายน้ำปลายคลองพร้อมเครื่องสูบน้ำขนาดใหญ่ ระบายน้ำลงสู่อ่าวไทย",
          link: "report/คลองเจ้าพระยา2_วิชาการ.html"
        }
      ]
    }
  };

  function initMap() {
    var mapEl = document.getElementById('portal-map');
    if (!mapEl) return;

    // ตรวจสอบว่ามี Leaflet หรือไม่
    if (typeof L === 'undefined') {
      mapEl.innerHTML = '<div style="padding:2rem;text-align:center;color:#666">กำลังโหลดข้อมูลแผนที่ กรุณารอสักครู่...</div>';
      return;
    }

    // สร้างแผนที่ Leaflet พิกัดศูนย์กลางภาคกลาง
    var map = L.map('portal-map', {
      center: [14.40, 100.80],
      zoom: 8,
      scrollWheelZoom: false
    });

    // แผนที่ฐาน OpenStreetMap — ไม่ต้องใช้คีย์ และป้ายชื่อสถานที่เป็นภาษาไทย
    // (เดิมใช้ CARTO Voyager แต่ตั้งแต่ ส.ค. 2569 CARTO บังคับคีย์ — ไร้คีย์จะได้กระเบื้องลายน้ำ "API KEY REQUIRED")
    L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png', {
      attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
      maxZoom: 19
    }).addTo(map);

    // Layer Groups
    var layerPillar1 = L.layerGroup();
    var layerPillar2 = L.layerGroup();
    var layerPillar3 = L.layerGroup();

    // 1. หมุดสถานีโทรมาตร
    DATA.stations.forEach(function (st) {
      var markerColor = st.pillar === 'p1' ? '#0284c7' : '#0d9488';
      var circle = L.circleMarker([st.lat, st.lng], {
        radius: 7,
        fillColor: markerColor,
        color: '#ffffff',
        weight: 2,
        opacity: 1,
        fillOpacity: 0.9
      });

      var popupHtml = '<div style="font-family:sans-serif;font-size:0.85rem;min-width:200px">' +
        '<strong style="color:' + markerColor + ';font-size:0.95rem">' + st.name + '</strong><br>' +
        '<span style="color:#666">' + st.river + ' · ' + st.type + '</span><hr style="margin:4px 0;border:0;border-top:1px solid #ddd">' +
        '<b>ความจุตลิ่ง/วิกฤต:</b> ' + st.bankfull + '<br>' +
        '<b>น้ำสูงสุด 2569:</b> ' + st.peak + '<br>' +
        '<p style="margin:4px 0;font-size:0.8rem;color:#444">' + st.desc + '</p>' +
        '<a href="' + st.link + '" style="color:#0284c7;font-weight:bold;text-decoration:none">อ่านรายงาน &rarr;</a>' +
        '</div>';

      circle.bindPopup(popupHtml);

      if (st.pillar === 'p1') layerPillar1.addLayer(circle);
      else layerPillar2.addLayer(circle);
    });

    // 2. หมุดเขื่อนและอ่างเก็บน้ำ
    DATA.dams.forEach(function (d) {
      var damIcon = L.circleMarker([d.lat, d.lng], {
        radius: 9,
        fillColor: '#d97706',
        color: '#ffffff',
        weight: 2,
        opacity: 1,
        fillOpacity: 0.95
      });

      var popupHtml = '<div style="font-family:sans-serif;font-size:0.85rem;min-width:210px">' +
        '<strong style="color:#b45309;font-size:0.95rem">🏛️ ' + d.name + '</strong><br>' +
        '<span style="color:#666">ความจุอ่าง: ' + d.cap + '</span><hr style="margin:4px 0;border:0;border-top:1px solid #ddd">' +
        '<b>กักเก็บสูงสุด 2569:</b> ' + d.peak_storage + '<br>' +
        '<b>การระบายสูงสุด:</b> ' + d.release_peak + '<br>' +
        '<p style="margin:4px 0;font-size:0.8rem;color:#444">' + d.desc + '</p>' +
        '<a href="' + d.link + '" style="color:#d97706;font-weight:bold;text-decoration:none">อ่านรายงาน &rarr;</a>' +
        '</div>';

      damIcon.bindPopup(popupHtml);

      if (d.pillar === 'p1') layerPillar1.addLayer(damIcon);
      else layerPillar2.addLayer(damIcon);
    });

    // 3. แนวคลองเจ้าพระยา 2 (เสาที่ 3)
    var canalPolyline = L.polyline(DATA.canal_cp2.route, {
      color: '#e11d48',
      weight: 4,
      opacity: 0.85,
      dashArray: '8, 6'
    });
    layerPillar3.addLayer(canalPolyline);

    DATA.canal_cp2.structures.forEach(function (st) {
      var marker = L.circleMarker([st.lat, st.lng], {
        radius: 8,
        fillColor: '#be123c',
        color: '#ffffff',
        weight: 2,
        opacity: 1,
        fillOpacity: 0.9
      });

      var popupHtml = '<div style="font-family:sans-serif;font-size:0.85rem;min-width:200px">' +
        '<strong style="color:#be123c;font-size:0.95rem">⚙️ ' + st.name + '</strong><hr style="margin:4px 0;border:0;border-top:1px solid #ddd">' +
        '<p style="margin:4px 0;font-size:0.8rem;color:#444">' + st.desc + '</p>' +
        '<a href="' + st.link + '" style="color:#be123c;font-weight:bold;text-decoration:none">อ่านรายงาน &rarr;</a>' +
        '</div>';

      marker.bindPopup(popupHtml);
      layerPillar3.addLayer(marker);
    });

    // แสดงผลทุกเลเยอร์เป็นค่าเริ่มต้น
    layerPillar1.addTo(map);
    layerPillar2.addTo(map);
    layerPillar3.addTo(map);

    // ปุ่มตัวกรองเสาหลัก (Filter Buttons)
    var filterBtns = document.querySelectorAll('.atlas-btn');
    filterBtns.forEach(function (btn) {
      btn.addEventListener('click', function () {
        filterBtns.forEach(function (b) { b.classList.remove('active'); });
        this.classList.add('active');

        var mode = this.getAttribute('data-mode');
        if (mode === 'all') {
          map.addLayer(layerPillar1);
          map.addLayer(layerPillar2);
          map.addLayer(layerPillar3);
          map.flyTo([14.40, 100.80], 8);
        } else if (mode === 'p1') {
          map.addLayer(layerPillar1);
          map.removeLayer(layerPillar2);
          map.removeLayer(layerPillar3);
          map.flyTo([14.25, 101.25], 11);
        } else if (mode === 'p2') {
          map.removeLayer(layerPillar1);
          map.addLayer(layerPillar2);
          map.removeLayer(layerPillar3);
          map.flyTo([15.00, 100.50], 7);
        } else if (mode === 'p3') {
          map.removeLayer(layerPillar1);
          map.removeLayer(layerPillar2);
          map.addLayer(layerPillar3);
          map.flyTo([14.30, 100.70], 9);
        }
      });
    });
  }

  // เรียกทำงานเมื่อโหลดหน้าเสร็จสมบูรณ์
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initMap);
  } else {
    initMap();
  }
})();
