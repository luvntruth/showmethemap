import xml.etree.ElementTree as ET
import json
import os

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
    gpx_path = r"C:\Users\luvnt\Desktop\멧빵뿡.gpx"
    points = parse_gpx(gpx_path)
    print(f"Parsed {len(points)} points.")
    
    # 결과를 points.js 파일로 저장 (CORS 우회용)
    out_path = r"C:\Users\luvnt\.gemini\antigravity-ide\scratch\gpx-viewer\points.js"
    with open(out_path, 'w', encoding='utf-8') as f:
        f.write("const defaultGpxPoints = ")
        json.dump(points, f, ensure_ascii=False)
        f.write(";")
    print(f"Saved to {out_path}")
