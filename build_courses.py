# -*- coding: utf-8 -*-
"""
코스 라이브러리 빌드 스크립트.

courses_src/ 폴더의 GPX 파일들을 읽어서:
  1) 포인트를 단순화(다운샘플)하고
  2) 거리 / 획득 고도 / 소요시간을 계산하고
  3) 거리·고도 기준으로 난이도(초급/중급/고급)를 자동 분류한 뒤
  4) 코스별 경량 JSON(courses/<id>.json)과 목록(courses/index.json)을 생성합니다.

사용법:
  python build_courses.py
  (courses_src/meta.json 으로 파일별 name/region 을 덮어쓸 수 있음)
"""
import xml.etree.ElementTree as ET
import json
import os
import glob
import math
import re

SRC_DIR = "courses_src"
OUT_DIR = "courses"
MAX_POINTS = 800  # 코스 1개당 최대 포인트(개요용 단순화)


def parse_gpx(path):
    tree = ET.parse(path)
    root = tree.getroot()
    trkpts = root.findall('.//{http://www.topografix.com/GPX/1/1}trkpt')
    if not trkpts:
        trkpts = root.findall('.//trkpt')
    points = []
    for pt in trkpts:
        lat = float(pt.attrib['lat'])
        lon = float(pt.attrib['lon'])
        ele_el = pt.find('{http://www.topografix.com/GPX/1/1}ele')
        if ele_el is None:
            ele_el = pt.find('ele')
        ele = float(ele_el.text) if ele_el is not None else 0.0
        time_el = pt.find('{http://www.topografix.com/GPX/1/1}time')
        if time_el is None:
            time_el = pt.find('time')
        time_str = time_el.text if time_el is not None else ""
        points.append({'lat': lat, 'lon': lon, 'ele': ele, 'time': time_str})
    return points


def haversine(lat1, lon1, lat2, lon2):
    R = 6371.0
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat / 2) ** 2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2) ** 2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def compute_stats(points):
    total_dist = 0.0
    gain = 0.0
    for i in range(1, len(points)):
        p, c = points[i - 1], points[i]
        total_dist += haversine(p['lat'], p['lon'], c['lat'], c['lon'])
        d = c['ele'] - p['ele']
        if d > 0:
            gain += d
    return total_dist, gain


def classify(distance, gain):
    # 거리(km) + 획득 고도(m) 기준 (조정 가능)
    if distance <= 30 and gain <= 300:
        return "초급"
    if distance <= 70 and gain <= 1000:
        return "중급"
    return "고급"


def simplify(points, max_points):
    if len(points) <= max_points:
        return points
    step = len(points) / max_points
    out = [points[int(i * step)] for i in range(max_points)]
    out[0] = points[0]
    out[-1] = points[-1]
    return out


def slugify(stem, idx):
    s = re.sub(r'[^a-z0-9]+', '-', stem.lower()).strip('-')
    return s if s else f"course-{idx}"


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    meta = {}
    meta_path = os.path.join(SRC_DIR, "meta.json")
    if os.path.exists(meta_path):
        with open(meta_path, encoding='utf-8') as f:
            meta = json.load(f)

    index = []
    gpx_files = sorted(glob.glob(os.path.join(SRC_DIR, "*.gpx")))
    for idx, path in enumerate(gpx_files, 1):
        fname = os.path.basename(path)
        stem = os.path.splitext(fname)[0]
        info = meta.get(fname, {})

        points = parse_gpx(path)
        if not points:
            print(f"skip (no points): {fname}")
            continue
        distance, gain = compute_stats(points)
        diff = classify(distance, gain)
        simp = simplify(points, MAX_POINTS)

        cid = slugify(stem, idx)
        out_file = os.path.join(OUT_DIR, f"{cid}.json")
        with open(out_file, 'w', encoding='utf-8') as f:
            json.dump(simp, f, ensure_ascii=False, separators=(',', ':'))

        index.append({
            "id": cid,
            "name": info.get("name", stem),
            "region": info.get("region", ""),
            "distance": round(distance, 1),
            "elevationGain": round(gain),
            "difficulty": diff,
            "points": f"{OUT_DIR}/{cid}.json",
            "numPoints": len(simp),
        })
        print(f"OK {cid}: {info.get('name', stem)} | {round(distance,1)}km | {round(gain)}m | {diff} | {len(points)}->{len(simp)}pts")

    order = {"초급": 0, "중급": 1, "고급": 2}
    index.sort(key=lambda c: (order.get(c["difficulty"], 9), c["distance"]))
    with open(os.path.join(OUT_DIR, "index.json"), 'w', encoding='utf-8') as f:
        json.dump({"courses": index}, f, ensure_ascii=False, indent=2)
    print(f"\nwrote {OUT_DIR}/index.json ({len(index)} courses)")


if __name__ == '__main__':
    main()
