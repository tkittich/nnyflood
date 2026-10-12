#!/usr/bin/env bash
# ดึงข้อมูลภายนอกที่เกี่ยวกับรีวิว Sonnet (12 ต.ค. 69): ผิวดิน/น้ำถาวร/ประชากร/ถนน — GET สาธารณะ ไม่ต้อง auth · resume ได้ (-C -)
set -u
cd "$(dirname "$0")/raw"
get() { # url file
  if [ -s "$2" ] && [ -f "$2.done" ]; then echo "skip $2"; return; fi
  curl -sSL -C - --retry 5 --retry-delay 5 -o "$2" "$1" && touch "$2.done" && echo "ok $2" || echo "FAIL $2"
}
WC=https://esa-worldcover.s3.eu-central-1.amazonaws.com/v200/2021/map
for t in N12E096 N12E099 N12E102 N15E096 N15E099 N18E096 N18E099; do
  get "$WC/ESA_WorldCover_10m_2021_v200_${t}_Map.tif" "ESA_WorldCover_10m_2021_v200_${t}_Map.tif"
done
GSW=https://storage.googleapis.com/global-surface-water/downloads2021/occurrence
for t in 90E_20N 100E_20N; do
  get "$GSW/occurrence_${t}v1_4_2021.tif" "occurrence_${t}v1_4_2021.tif"
done
get https://data.worldpop.org/GIS/Population/Global_2000_2020_1km/2020/THA/tha_ppp_2020_1km_Aggregated.tif tha_ppp_2020_1km_Aggregated.tif
get https://download.geofabrik.de/asia/thailand-latest.osm.pbf thailand-latest.osm.pbf
echo ALLDONE
