import xml.etree.ElementTree as ET
import json
import os
import sys


def parse_gpx(file_path):
    tree = ET.parse(file_path)
    root = tree.getroot()

    # trkpt 태그 찾기 (네임스페이스 포함)
    trkpts = root.findall('.//{http://www.topografix.com/GPX/1/1}trkpt')
    if not trkpts:
        trkpts = root.findall('.//trkpt')

    points = []
    for pt in trkpts:
        lat = float(pt.attrib['lat'])
        lon = float(pt.attrib['lon'])

        # 고도 추출
        ele_el = pt.find('{http://www.topografix.com/GPX/1/1}ele')
        if ele_el is None:
            ele_el = pt.find('ele')
        ele = float(ele_el.text) if ele_el is not None else 0.0

        # 시간 추출
        time_el = pt.find('{http://www.topografix.com/GPX/1/1}time')
        if time_el is None:
            time_el = pt.find('time')
        time_str = time_el.text if time_el is not None else ""

        points.append({
            'lat': lat,
            'lon': lon,
            'ele': ele,
            'time': time_str
        })

    return points


if __name__ == '__main__':
    # 사용법: python parse_gpx.py [입력.gpx] [출력.js]
    # 인자를 생략하면 이 스크립트와 같은 폴더의 기본 파일을 사용합니다.
    base_dir = os.path.dirname(os.path.abspath(__file__))
    gpx_path = sys.argv[1] if len(sys.argv) > 1 else os.path.join(base_dir, "sample.gpx")
    out_path = sys.argv[2] if len(sys.argv) > 2 else os.path.join(base_dir, "points.js")

    points = parse_gpx(gpx_path)
    print(f"Parsed {len(points)} points from {gpx_path}")

    # 로컬 CORS 에러 우회를 위해 JS 변수 형태(points.js)로 저장
    with open(out_path, 'w', encoding='utf-8') as f:
        f.write("const defaultGpxPoints = ")
        json.dump(points, f, ensure_ascii=False)
        f.write(";")
    print(f"Saved to {out_path}")
