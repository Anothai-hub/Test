"""
คำนวณออกแบบแผ่นเหล็กรองฐานเสา (Column Base Plate) สำหรับเสาเหล็กรูปพรรณหน้าตัด H
รับแรงอัดตามแนวแกนอย่างเดียว (Concentric Axial Compression)

หลักการคำนวณตามแนวทางมาตรฐานการออกแบบอาคารเหล็กรูปพรรณของกรมโยธาธิการและผังเมือง (มยผ.)
ซึ่งอ้างอิง AISC 360 (J8 Bearing on Concrete) และ AISC Design Guide 1
รองรับทั้งวิธีหน่วยแรงที่ยอมให้ (ASD) และวิธีตัวคูณความต้านทานและน้ำหนักบรรทุก (LRFD)

หน่วยภายใน: kg, cm, ksc (kg/cm²)
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field

# ---------------------------------------------------------------------------
# ฐานข้อมูลหน้าตัด H ตาม มอก. 1227 (หน่วย mm, kg/m)
# ---------------------------------------------------------------------------
H_SECTIONS: dict[str, dict[str, float]] = {
    # Wide flange (bf = d)
    "H100x100x6x8": dict(d=100, bf=100, tw=6, tf=8, w=17.2),
    "H125x125x6.5x9": dict(d=125, bf=125, tw=6.5, tf=9, w=23.8),
    "H150x150x7x10": dict(d=150, bf=150, tw=7, tf=10, w=31.5),
    "H175x175x7.5x11": dict(d=175, bf=175, tw=7.5, tf=11, w=40.4),
    "H200x200x8x12": dict(d=200, bf=200, tw=8, tf=12, w=49.9),
    "H250x250x9x14": dict(d=250, bf=250, tw=9, tf=14, w=72.4),
    "H300x300x10x15": dict(d=300, bf=300, tw=10, tf=15, w=94.0),
    "H350x350x12x19": dict(d=350, bf=350, tw=12, tf=19, w=137.0),
    "H400x400x13x21": dict(d=400, bf=400, tw=13, tf=21, w=172.0),
    # Middle flange
    "H148x100x6x9": dict(d=148, bf=100, tw=6, tf=9, w=21.1),
    "H194x150x6x9": dict(d=194, bf=150, tw=6, tf=9, w=30.6),
    "H244x175x7x11": dict(d=244, bf=175, tw=7, tf=11, w=44.1),
    "H294x200x8x12": dict(d=294, bf=200, tw=8, tf=12, w=56.8),
    "H340x250x9x14": dict(d=340, bf=250, tw=9, tf=14, w=79.7),
    "H390x300x10x16": dict(d=390, bf=300, tw=10, tf=16, w=107.0),
    "H440x300x11x18": dict(d=440, bf=300, tw=11, tf=18, w=124.0),
    "H488x300x11x18": dict(d=488, bf=300, tw=11, tf=18, w=128.0),
    "H588x300x12x20": dict(d=588, bf=300, tw=12, tf=20, w=151.0),
    # Narrow flange
    "H150x75x5x7": dict(d=150, bf=75, tw=5, tf=7, w=14.0),
    "H200x100x5.5x8": dict(d=200, bf=100, tw=5.5, tf=8, w=21.3),
    "H250x125x6x9": dict(d=250, bf=125, tw=6, tf=9, w=29.6),
    "H300x150x6.5x9": dict(d=300, bf=150, tw=6.5, tf=9, w=36.7),
    "H350x175x7x11": dict(d=350, bf=175, tw=7, tf=11, w=49.6),
    "H400x200x8x13": dict(d=400, bf=200, tw=8, tf=13, w=66.0),
    "H450x200x9x14": dict(d=450, bf=200, tw=9, tf=14, w=76.0),
    "H500x200x10x16": dict(d=500, bf=200, tw=10, tf=16, w=89.6),
    "H600x200x11x17": dict(d=600, bf=200, tw=11, tf=17, w=106.0),
}

# เกรดเหล็กแผ่น (Fy, Fu หน่วย ksc)
STEEL_GRADES: dict[str, tuple[float, float]] = {
    "SS400 (มอก. 1479)": (2450.0, 4100.0),
    "SM400": (2450.0, 4100.0),
    "SM490": (3250.0, 5000.0),
    "ASTM A36": (2500.0, 4080.0),
}

# ความหนาแผ่นเหล็กมาตรฐานในท้องตลาด (mm)
STD_PLATE_THK_MM = [9, 10, 12, 16, 19, 20, 22, 25, 28, 32, 36, 40, 45, 50, 55, 60, 65, 70, 75, 80, 90, 100]

# ตัวคูณ/ตัวประกอบความปลอดภัย
PHI_C, OMEGA_C = 0.65, 2.31  # Bearing on concrete
PHI_B, OMEGA_B = 0.90, 1.67  # Plate yielding (flexure)


@dataclass
class DesignInput:
    method: str  # "LRFD" หรือ "ASD"
    P: float  # แรงอัดที่ต้องการ (kg) — Pu สำหรับ LRFD, Pa สำหรับ ASD
    d: float  # ความลึกหน้าตัดเสา (cm)
    bf: float  # ความกว้างปีกเสา (cm)
    tf: float  # ความหนาปีกเสา (cm)
    tw: float  # ความหนาเอวเสา (cm)
    fc: float  # f'c คอนกรีต (ksc)
    Fy: float  # Fy แผ่นเหล็ก (ksc)
    N: float  # ความยาวแผ่นเหล็ก (ขนาน d) (cm)
    B: float  # ความกว้างแผ่นเหล็ก (ขนาน bf) (cm)
    Np: float  # ความยาวตอม่อ/ฐานรองรับ (cm)
    Bp: float  # ความกว้างตอม่อ/ฐานรองรับ (cm)
    t: float  # ความหนาแผ่นเหล็กที่เลือก (cm)


@dataclass
class DesignResult:
    A1: float
    A2: float
    sqrt_ratio: float
    Pp: float
    P_avail_bearing: float
    bearing_ratio: float
    fp: float  # หน่วยแรงแบกทานที่เกิดขึ้น (ksc)
    fp_avail: float  # หน่วยแรงแบกทานที่ยอมให้ (ksc)
    m: float
    n: float
    X: float
    lam: float
    lam_n: float
    l: float
    t_req: float
    thk_ratio: float
    weld_min_mm: float
    checks: dict[str, bool] = field(default_factory=dict)

    @property
    def ok(self) -> bool:
        return all(self.checks.values())


def sqrt_a2_a1(N: float, B: float, Np: float, Bp: float) -> tuple[float, float]:
    """คืนค่า (A2, sqrt(A2/A1)) โดย A2 คือพื้นที่ใหญ่สุดของฐานรองรับที่คล้ายและมีศูนย์กลางร่วมกับ A1
    และจำกัด sqrt(A2/A1) <= 2"""
    A1 = N * B
    k = max(1.0, min(Np / N, Bp / B))
    A2 = A1 * k**2
    return A2, min(k, 2.0)


def bearing_capacity(method: str, fc: float, A1: float, ratio: float) -> tuple[float, float]:
    """กำลังแบกทานของคอนกรีต: คืนค่า (Pp nominal, กำลังที่ใช้ได้ phi*Pp หรือ Pp/Omega)"""
    Pp = min(0.85 * fc * A1 * ratio, 1.7 * fc * A1)
    avail = PHI_C * Pp if method == "LRFD" else Pp / OMEGA_C
    return Pp, avail


def min_fillet_weld_mm(t_thin_mm: float) -> float:
    """ขนาดรอยเชื่อมพอกต่ำสุด ตามความหนาชิ้นส่วนที่บางกว่า (AISC Table J2.4)"""
    if t_thin_mm <= 6:
        return 3.0
    if t_thin_mm <= 13:
        return 5.0
    if t_thin_mm <= 19:
        return 6.0
    return 8.0


def check(inp: DesignInput) -> DesignResult:
    A1 = inp.N * inp.B
    A2, ratio = sqrt_a2_a1(inp.N, inp.B, inp.Np, inp.Bp)
    Pp, P_avail = bearing_capacity(inp.method, inp.fc, A1, ratio)
    bearing_ratio = inp.P / P_avail

    fp = inp.P / A1
    fp_avail = P_avail / A1

    # ระยะยื่นวิกฤตของแผ่นเหล็ก
    m = (inp.N - 0.95 * inp.d) / 2.0
    n = (inp.B - 0.80 * inp.bf) / 2.0

    # ระยะยื่นเทียบเท่าบริเวณระหว่างปีกเสา (Thornton)
    X = min((4.0 * inp.d * inp.bf / (inp.d + inp.bf) ** 2) * bearing_ratio, 1.0)
    lam = min(2.0 * math.sqrt(X) / (1.0 + math.sqrt(1.0 - X)), 1.0) if X < 1.0 else 1.0
    lam_n = lam * math.sqrt(inp.d * inp.bf) / 4.0
    l = max(m, n, lam_n)

    if inp.method == "LRFD":
        t_req = l * math.sqrt(2.0 * inp.P / (PHI_B * inp.Fy * inp.B * inp.N))
    else:
        t_req = l * math.sqrt(2.0 * inp.P * OMEGA_B / (inp.Fy * inp.B * inp.N))

    weld = min_fillet_weld_mm(min(inp.tf, inp.t) * 10.0)

    checks = {
        "ขนาดแผ่นเหล็กครอบหน้าตัดเสา": inp.N >= inp.d and inp.B >= inp.bf,
        "ฐานรองรับใหญ่กว่าแผ่นเหล็ก": inp.Np >= inp.N and inp.Bp >= inp.B,
        "กำลังแบกทานคอนกรีต": bearing_ratio <= 1.0,
        "ความหนาแผ่นเหล็ก": inp.t >= t_req,
    }
    return DesignResult(
        A1=A1, A2=A2, sqrt_ratio=ratio, Pp=Pp, P_avail_bearing=P_avail,
        bearing_ratio=bearing_ratio, fp=fp, fp_avail=fp_avail,
        m=m, n=n, X=X, lam=lam, lam_n=lam_n, l=l, t_req=t_req,
        thk_ratio=t_req / inp.t if inp.t > 0 else float("inf"),
        weld_min_mm=weld, checks=checks,
    )


def _ceil_to(x: float, step: float) -> float:
    return math.ceil(x / step - 1e-9) * step


def auto_size(method: str, P: float, d: float, bf: float, fc: float,
              Np: float, Bp: float, min_proj: float = 5.0, step: float = 1.0,
              min_proj_N: float | None = None) -> tuple[float, float]:
    """หาขนาด N x B ที่เหมาะสม (ประหยัด) ตามแนวทาง Design Guide 1
    min_proj   : ระยะยื่นต่ำสุดจากขอบเสาแต่ละด้าน (cm) เพื่อวางสลักยึด/เชื่อม
    min_proj_N : ระยะยื่นต่ำสุดในแนว N (cm) ถ้าต่างจาก min_proj เช่น เผื่อสลักยึดวางนอกปีกเสา
    step       : ปัดขึ้นทีละ (cm)"""
    N_min = d + 2.0 * (min_proj if min_proj_N is None else max(min_proj, min_proj_N))
    B_min = bf + 2.0 * min_proj
    phi_factor = PHI_C if method == "LRFD" else 1.0 / OMEGA_C

    # เริ่มจากพื้นที่ที่ต้องการเมื่อไม่คิดผลของ A2 (อนุรักษ์) แล้ววนลดลง
    A1_req = P / (phi_factor * 0.85 * fc)
    delta = (0.95 * d - 0.80 * bf) / 2.0
    N = max(_ceil_to(math.sqrt(A1_req) + delta, step), N_min)
    B = max(_ceil_to(A1_req / N, step), B_min)

    # ลดขนาดลงทีละขั้นถ้ายังผ่านเมื่อพิจารณา sqrt(A2/A1)
    for _ in range(500):
        candidates = []
        for dN, dB in ((step, 0.0), (0.0, step), (step, step)):
            Nn, Bn = N - dN, B - dB
            if Nn < N_min or Bn < B_min or Nn > Np or Bn > Bp:
                continue
            _, r = sqrt_a2_a1(Nn, Bn, Np, Bp)
            _, avail = bearing_capacity(method, fc, Nn * Bn, r)
            if avail >= P:
                candidates.append((Nn * Bn, Nn, Bn))
        if not candidates:
            break
        _, N, B = min(candidates)
    return N, B


def pick_std_thickness(t_req_cm: float) -> float:
    """เลือกความหนาแผ่นเหล็กมาตรฐาน (cm) ที่ไม่น้อยกว่าที่ต้องการ"""
    for t in STD_PLATE_THK_MM:
        if t / 10.0 >= t_req_cm:
            return t / 10.0
    return _ceil_to(t_req_cm, 0.5)
