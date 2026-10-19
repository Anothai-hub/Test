"""
Streamlit Web App: ออกแบบแผ่นเหล็กรองฐานเสา (Column Base Plate)
สำหรับเสาเหล็กรูปพรรณหน้าตัด H มาตรฐาน รับแรงอัดตามแนวแกนอย่างเดียว

รันด้วย:  streamlit run app.py
"""
import plotly.graph_objects as go
import streamlit as st

import base_plate as bp

st.set_page_config(page_title="Column Base Plate Design", page_icon="🏗️", layout="wide")

st.title("🏗️ ออกแบบแผ่นเหล็กรองฐานเสา (Column Base Plate)")
st.caption(
    "เสาเหล็กรูปพรรณหน้าตัด H มาตรฐาน รับแรงอัดตามแนวแกนอย่างเดียว • "
    "ตามแนวทางมาตรฐานการออกแบบอาคารเหล็กรูปพรรณ มยผ. (อ้างอิง AISC 360 ข้อ J8 และ AISC Design Guide 1) • "
    "รองรับวิธี LRFD และ ASD"
)

# ---------------------------------------------------------------------------
# Sidebar: ข้อมูลนำเข้า
# ---------------------------------------------------------------------------
with st.sidebar:
    st.header("1) วิธีออกแบบ")
    method = st.radio(
        "Design method",
        ["LRFD", "ASD"],
        format_func=lambda x: "LRFD (กำลัง)" if x == "LRFD" else "ASD (หน่วยแรงที่ยอมให้)",
        horizontal=True,
    )

    st.header("2) น้ำหนักบรรทุก")
    PD = st.number_input("น้ำหนักบรรทุกคงที่ D (ตัน)", min_value=0.0, value=40.0, step=1.0)
    PL = st.number_input("น้ำหนักบรรทุกจร L (ตัน)", min_value=0.0, value=25.0, step=1.0)
    if method == "LRFD":
        c1, c2 = st.columns(2)
        fD = c1.number_input("ตัวคูณ D", value=1.4, step=0.1, format="%.2f")
        fL = c2.number_input("ตัวคูณ L", value=1.7, step=0.1, format="%.2f")
        P_ton = max(fD * PD + fL * PL, 1.4 * PD)
        st.info(f"Pu = max({fD:g}D + {fL:g}L, 1.4D) = **{P_ton:,.2f} ตัน**")
    else:
        P_ton = PD + PL
        st.info(f"Pa = D + L = **{P_ton:,.2f} ตัน**")

    st.header("3) หน้าตัดเสา")
    sec_mode = st.radio("แหล่งข้อมูลหน้าตัด", ["ตารางมาตรฐาน มอก. 1227", "กำหนดเอง"], horizontal=True)
    if sec_mode.startswith("ตาราง"):
        sec_name = st.selectbox("หน้าตัด H", list(bp.H_SECTIONS), index=list(bp.H_SECTIONS).index("H300x300x10x15"))
        s = bp.H_SECTIONS[sec_name]
        d_mm, bf_mm, tw_mm, tf_mm = s["d"], s["bf"], s["tw"], s["tf"]
        st.write(f"d = {d_mm:g} mm, bf = {bf_mm:g} mm, tw = {tw_mm:g} mm, tf = {tf_mm:g} mm, w = {s['w']:g} kg/m")
    else:
        sec_name = "Custom"
        c1, c2 = st.columns(2)
        d_mm = c1.number_input("d (mm)", min_value=50.0, value=300.0)
        bf_mm = c2.number_input("bf (mm)", min_value=50.0, value=300.0)
        tw_mm = c1.number_input("tw (mm)", min_value=3.0, value=10.0)
        tf_mm = c2.number_input("tf (mm)", min_value=3.0, value=15.0)

    st.header("4) วัสดุ")
    grade = st.selectbox("เกรดแผ่นเหล็ก", list(bp.STEEL_GRADES))
    Fy = st.number_input("Fy แผ่นเหล็ก (ksc)", min_value=1000.0, value=bp.STEEL_GRADES[grade][0], step=50.0)
    fc = st.number_input("f'c คอนกรีต (ksc) — ทรงกระบอก", min_value=100.0, value=240.0, step=10.0)

    st.header("5) ตอม่อ / ฐานรองรับ")
    c1, c2 = st.columns(2)
    Np_mm = c1.number_input("ความยาวตอม่อ (ขนาน d) mm", min_value=100.0, value=600.0, step=50.0)
    Bp_mm = c2.number_input("ความกว้างตอม่อ (ขนาน bf) mm", min_value=100.0, value=600.0, step=50.0)

    st.header("6) ขนาดแผ่นเหล็ก")
    size_mode = st.radio("การกำหนดขนาด", ["ออกแบบอัตโนมัติ", "กำหนดเอง"], horizontal=True)
    min_proj_mm = st.number_input(
        "ระยะยื่นต่ำสุดจากขอบเสาแต่ละด้าน (mm)", min_value=0.0, value=50.0, step=5.0,
        help="เผื่อพื้นที่สำหรับสลักยึดและการเชื่อม",
    )
    round_mm = st.selectbox("ปัดขนาดแผ่นขึ้นทีละ (mm)", [10, 25, 50], index=0)

    st.header("7) สลักยึด (Anchor Bolts)")
    n_bolt = st.selectbox("จำนวนสลักยึด", [4, 6, 8], index=0, help="อย่างน้อย 4 ตัว เพื่อเสถียรภาพระหว่างการติดตั้ง")
    db_mm = st.selectbox("ขนาดสลักยึด (mm)", [16, 20, 22, 24, 27, 30, 36], index=1)
    edge_mm = st.number_input("ระยะจากศูนย์กลางสลักถึงขอบแผ่น (mm)", min_value=20.0, value=50.0, step=5.0)

# ---------------------------------------------------------------------------
# แปลงหน่วยเป็น kg, cm
# ---------------------------------------------------------------------------
P = P_ton * 1000.0
d, bf, tw, tf = d_mm / 10, bf_mm / 10, tw_mm / 10, tf_mm / 10
Np, Bp = Np_mm / 10, Bp_mm / 10

if P <= 0:
    st.warning("กรุณาใส่น้ำหนักบรรทุกมากกว่า 0")
    st.stop()

if size_mode == "ออกแบบอัตโนมัติ":
    # สลักยึดวางนอกปีกเสาในแนว N: ระยะยื่น >= ระยะขอบ + db
    N, B = bp.auto_size(method, P, d, bf, fc, Np, Bp, min_proj=min_proj_mm / 10, step=round_mm / 10,
                        min_proj_N=(edge_mm + db_mm) / 10)
else:
    with st.sidebar:
        c1, c2 = st.columns(2)
        N = c1.number_input("N (ขนาน d) mm", min_value=50.0, value=float(d_mm + 2 * max(min_proj_mm, edge_mm + db_mm))) / 10
        B = c2.number_input("B (ขนาน bf) mm", min_value=50.0, value=float(bf_mm + 2 * min_proj_mm)) / 10

# หาความหนาที่ต้องการก่อน แล้วเลือกความหนามาตรฐาน
pre = bp.check(bp.DesignInput(method, P, d, bf, tf, tw, fc, Fy, N, B, Np, Bp, t=1.0))
t_auto = bp.pick_std_thickness(pre.t_req)
with st.sidebar:
    thk_opts = bp.STD_PLATE_THK_MM
    default_idx = thk_opts.index(int(round(t_auto * 10))) if int(round(t_auto * 10)) in thk_opts else len(thk_opts) - 1
    t_mm = st.selectbox("ความหนาแผ่นเหล็กที่ใช้ (mm)", thk_opts, index=default_idx,
                        help=f"ความหนาที่ต้องการ ≈ {pre.t_req * 10:.1f} mm")
t = t_mm / 10

inp = bp.DesignInput(method, P, d, bf, tf, tw, fc, Fy, N, B, Np, Bp, t)
r = bp.check(inp)

# ตรวจระยะสลักยึด
hole_mm = db_mm + (6 if db_mm < 24 else 8)  # รูเผื่อสำหรับสลักยึดฝังในคอนกรีต (ค่าประมาณ)
edge_min_mm = 1.5 * db_mm
bolt_x_mm = N * 10 / 2 - edge_mm
bolt_y_mm = B * 10 / 2 - edge_mm
r.checks["ระยะขอบสลักยึด ≥ 1.5 db"] = edge_mm >= edge_min_mm
clear_ok = bolt_x_mm - d_mm / 2 >= db_mm or bolt_y_mm - bf_mm / 2 >= db_mm
r.checks["สลักยึดไม่ชนหน้าตัดเสา"] = clear_ok

# ---------------------------------------------------------------------------
# แสดงผล
# ---------------------------------------------------------------------------
status = "✅ ผ่านทุกข้อ" if r.ok else "❌ ไม่ผ่าน — กรุณาปรับข้อมูล"
st.subheader(f"ผลการออกแบบ: {status}")

c1, c2, c3, c4 = st.columns(4)
c1.metric("ขนาดแผ่นเหล็ก N × B", f"{N * 10:.0f} × {B * 10:.0f} mm")
c2.metric("ความหนา t ที่ใช้", f"{t_mm} mm", f"ต้องการ {r.t_req * 10:.1f} mm", delta_color="off")
c3.metric("อัตราส่วนแบกทาน", f"{r.bearing_ratio:.3f}", "OK" if r.bearing_ratio <= 1 else "NG",
          delta_color="normal" if r.bearing_ratio <= 1 else "inverse")
c4.metric("อัตราส่วนความหนา", f"{r.thk_ratio:.3f}", "OK" if r.thk_ratio <= 1 else "NG",
          delta_color="normal" if r.thk_ratio <= 1 else "inverse")

if r.ok:
    st.success(
        f"**สรุป:** ใช้แผ่นเหล็ก {grade} ขนาด **PL {N * 10:.0f} × {B * 10:.0f} × {t_mm} mm** "
        f"สลักยึด **{n_bolt}-Ø{db_mm} mm** (รูเจาะ Ø{hole_mm} mm) "
        f"เชื่อมพอกรอบหน้าตัดเสาขนาดไม่น้อยกว่า **{r.weld_min_mm:.0f} mm**"
    )
else:
    st.error("มีรายการที่ไม่ผ่าน ดูรายละเอียดด้านล่าง")

tab_calc, tab_draw, tab_check = st.tabs(["📐 รายการคำนวณ", "🖼️ แบบร่าง", "✔️ สรุปการตรวจสอบ"])

LE, GE = r"\le", r"\ge"
Preq = "P_u" if method == "LRFD" else "P_a"

with tab_calc:
    st.markdown("### ขั้นที่ 1 — แรงอัดที่ต้องการ")
    if method == "LRFD":
        st.latex(rf"P_u = \max({fD:g}D + {fL:g}L,\ 1.4D) = {P_ton:,.2f}\ \text{{ton}} = {P:,.0f}\ \text{{kg}}")
    else:
        st.latex(rf"P_a = D + L = {P_ton:,.2f}\ \text{{ton}} = {P:,.0f}\ \text{{kg}}")

    st.markdown("### ขั้นที่ 2 — กำลังแบกทานของคอนกรีต (Bearing on Concrete)")
    st.latex(rf"A_1 = N \times B = {N:.1f} \times {B:.1f} = {r.A1:,.1f}\ \text{{cm}}^2")
    st.latex(rf"A_2 = {r.A2:,.1f}\ \text{{cm}}^2 \quad(\text{{พื้นที่ฐานรองรับที่คล้ายและศูนย์กลางร่วมกับ }}A_1)")
    st.latex(rf"\sqrt{{A_2/A_1}} = {r.sqrt_ratio:.3f} \le 2")
    st.latex(
        rf"P_p = 0.85 f'_c A_1 \sqrt{{A_2/A_1}} \le 1.7 f'_c A_1"
        rf" \Rightarrow P_p = {r.Pp:,.0f}\ \text{{kg}}"
    )
    if method == "LRFD":
        st.latex(rf"\phi_c P_p = 0.65 \times {r.Pp:,.0f} = {r.P_avail_bearing:,.0f}\ \text{{kg}}")
    else:
        st.latex(rf"P_p / \Omega_c = {r.Pp:,.0f} / 2.31 = {r.P_avail_bearing:,.0f}\ \text{{kg}}")
    st.latex(
        rf"\frac{{{Preq}}}{{\text{{กำลังที่ใช้ได้}}}} = \frac{{{P:,.0f}}}{{{r.P_avail_bearing:,.0f}}}"
        rf" = {r.bearing_ratio:.3f}\ {LE if r.bearing_ratio <= 1 else '>'}\ 1.0"
        rf"\ \Rightarrow\ \text{{{'OK' if r.bearing_ratio <= 1 else 'NG'}}}"
    )
    st.caption(f"หน่วยแรงแบกทานเฉลี่ย fp = {r.fp:.1f} ksc ; ที่ใช้ได้ = {r.fp_avail:.1f} ksc ({'φc = 0.65' if method == 'LRFD' else 'Ωc = 2.31'})")

    st.markdown("### ขั้นที่ 3 — ระยะยื่นวิกฤตของแผ่นเหล็ก (Cantilever)")
    st.latex(rf"m = \frac{{N - 0.95d}}{{2}} = \frac{{{N:.1f} - 0.95({d:.1f})}}{{2}} = {r.m:.2f}\ \text{{cm}}")
    st.latex(rf"n = \frac{{B - 0.80b_f}}{{2}} = \frac{{{B:.1f} - 0.80({bf:.1f})}}{{2}} = {r.n:.2f}\ \text{{cm}}")
    st.latex(
        rf"X = \frac{{4 d b_f}}{{(d+b_f)^2}} \cdot \frac{{{Preq}}}{{\text{{กำลังแบกทานที่ใช้ได้}}}} = {r.X:.3f}"
    )
    st.latex(rf"\lambda = \frac{{2\sqrt{{X}}}}{{1+\sqrt{{1-X}}}} \le 1 \Rightarrow \lambda = {r.lam:.3f}")
    st.latex(rf"\lambda n' = \lambda \frac{{\sqrt{{d b_f}}}}{{4}} = {r.lam_n:.2f}\ \text{{cm}}")
    st.latex(rf"l = \max(m,\ n,\ \lambda n') = {r.l:.2f}\ \text{{cm}}")

    st.markdown("### ขั้นที่ 4 — ความหนาแผ่นเหล็กที่ต้องการ")
    if method == "LRFD":
        st.latex(
            rf"t_{{req}} = l\sqrt{{\frac{{2P_u}}{{0.9 F_y B N}}}} = {r.l:.2f}\sqrt{{\frac{{2({P:,.0f})}}"
            rf"{{0.9({Fy:,.0f})({B:.1f})({N:.1f})}}}} = {r.t_req:.2f}\ \text{{cm}}"
        )
    else:
        st.latex(
            rf"t_{{req}} = l\sqrt{{\frac{{2 P_a \Omega}}{{F_y B N}}}} = {r.l:.2f}\sqrt{{\frac{{2({P:,.0f})(1.67)}}"
            rf"{{({Fy:,.0f})({B:.1f})({N:.1f})}}}} = {r.t_req:.2f}\ \text{{cm}}"
        )
    st.latex(
        rf"t_{{use}} = {t_mm}\ \text{{mm}}\ {GE if t >= r.t_req else '<'}\ t_{{req}} = {r.t_req * 10:.1f}\ \text{{mm}}"
        rf"\ \Rightarrow\ \text{{{'OK' if t >= r.t_req else 'NG'}}}"
    )

    st.markdown("### ขั้นที่ 5 — รอยเชื่อมและสลักยึด")
    st.markdown(
        f"- เสารับแรงอัดอย่างเดียว ถ่ายแรงด้วยการสัมผัสแบกทาน (ปลายเสาตัดเรียบ) "
        f"รอยเชื่อมทำหน้าที่ยึดตำแหน่ง → ใช้รอยเชื่อมพอกขนาดต่ำสุดตามความหนาชิ้นที่บางกว่า "
        f"(min(tf, t) = {min(tf_mm, t_mm):g} mm) → **{r.weld_min_mm:.0f} mm**\n"
        f"- สลักยึด {n_bolt}-Ø{db_mm} mm ไม่รับแรงจากการคำนวณ (ไม่มีแรงดึง/แรงเฉือน) "
        f"ใช้อย่างน้อย 4 ตัวเพื่อเสถียรภาพระหว่างติดตั้ง\n"
        f"- ระยะขอบ = {edge_mm:g} mm {'≥' if edge_mm >= edge_min_mm else '<'} 1.5db = {edge_min_mm:g} mm\n"
        f"- แนะนำให้มีช่องเกราท์ (Non-shrink grout) หนา 25–50 mm ใต้แผ่นเหล็ก"
    )

with tab_draw:
    fig = go.Figure()
    Nm, Bm = N * 10, B * 10

    def rect(x0, y0, x1, y1, **kw):
        fig.add_shape(type="rect", x0=x0, y0=y0, x1=x1, y1=y1, **kw)

    # ตอม่อ, แผ่นเหล็ก
    rect(-Np_mm / 2, -Bp_mm / 2, Np_mm / 2, Bp_mm / 2, line=dict(color="gray", dash="dash"),
         fillcolor="rgba(180,180,180,0.15)")
    rect(-Nm / 2, -Bm / 2, Nm / 2, Bm / 2, line=dict(color="#1f4e79", width=2), fillcolor="rgba(31,78,121,0.15)")

    # หน้าตัด H (แกน d ตามแนว x, ปีกตั้งฉากแกน x)
    h = d_mm / 2
    b = bf_mm / 2
    xs = [-h, -h, -h + tf_mm, -h + tf_mm, h - tf_mm, h - tf_mm, h, h, h - tf_mm, h - tf_mm, -h + tf_mm, -h + tf_mm, -h]
    ys = [-b, b, b, tw_mm / 2, tw_mm / 2, b, b, -b, -b, -tw_mm / 2, -tw_mm / 2, -b, -b]
    fig.add_trace(go.Scatter(x=xs, y=ys, fill="toself", fillcolor="rgba(200,60,40,0.6)",
                             line=dict(color="#a02818"), name=sec_name, hoverinfo="name"))

    # พื้นที่วิกฤต 0.95d x 0.8bf
    rect(-0.95 * h, -0.8 * b, 0.95 * h, 0.8 * b, line=dict(color="orange", dash="dot"))

    # สลักยึด
    bx = []
    by = []
    if n_bolt == 4:
        pts = [(sx * bolt_x_mm, sy * bolt_y_mm) for sx in (-1, 1) for sy in (-1, 1)]
    elif n_bolt == 6:
        pts = [(sx * bolt_x_mm, sy * bolt_y_mm) for sx in (-1, 1) for sy in (-1, 0, 1)]
    else:
        pts = [(sx * bolt_x_mm, sy * bolt_y_mm) for sx in (-1, 1) for sy in (-1, -1 / 3, 1 / 3, 1)]
    for x, y in pts:
        fig.add_shape(type="circle", x0=x - hole_mm / 2, y0=y - hole_mm / 2, x1=x + hole_mm / 2, y1=y + hole_mm / 2,
                      line=dict(color="black"), fillcolor="white")
        bx.append(x)
        by.append(y)
    fig.add_trace(go.Scatter(x=bx, y=by, mode="markers", marker=dict(size=4, color="black"),
                             name=f"Anchor Ø{db_mm}"))

    # มิติ
    fig.add_annotation(x=0, y=-Bm / 2, text=f"N = {Nm:.0f}", showarrow=False, yshift=-14)
    fig.add_annotation(x=Nm / 2, y=0, text=f"B = {Bm:.0f}", showarrow=False, xshift=30, textangle=-90)
    fig.add_annotation(x=(Nm / 2 + 0.95 * h) / 2, y=0, text=f"m={r.m * 10:.0f}", showarrow=False, yshift=10)
    fig.add_annotation(x=0, y=(Bm / 2 + 0.8 * b) / 2, text=f"n={r.n * 10:.0f}", showarrow=False)

    lim = max(Np_mm, Bp_mm, Nm, Bm) / 2 * 1.15
    fig.update_xaxes(range=[-lim, lim], scaleanchor="y", scaleratio=1, title="แนว d (mm)", zeroline=False)
    fig.update_yaxes(range=[-lim, lim], title="แนว bf (mm)", zeroline=False)
    fig.update_layout(height=620, title="แปลนแผ่นเหล็กรองฐานเสา (หน่วย mm)", showlegend=True,
                      margin=dict(l=20, r=20, t=50, b=20))
    st.plotly_chart(fig, width="stretch")
    st.caption("เส้นประสีเทา = ตอม่อ • เส้นจุดสีส้ม = พื้นที่ 0.95d × 0.80bf สำหรับคำนวณ m, n")

with tab_check:
    rows = []
    for k, v in r.checks.items():
        rows.append({"รายการตรวจสอบ": k, "ผล": "✅ ผ่าน" if v else "❌ ไม่ผ่าน"})
    st.table(rows)
    if not r.checks["ฐานรองรับใหญ่กว่าแผ่นเหล็ก"]:
        st.warning("ขนาดแผ่นเหล็กใหญ่กว่าตอม่อ → เพิ่มขนาดตอม่อ หรือเพิ่ม f'c")
    if not r.checks["กำลังแบกทานคอนกรีต"]:
        st.warning("กำลังแบกทานไม่พอ → เพิ่มขนาดแผ่นเหล็ก / ขนาดตอม่อ / f'c")
    if not r.checks["ความหนาแผ่นเหล็ก"]:
        st.warning("แผ่นเหล็กบางเกินไป → เพิ่มความหนา หรือใช้เหล็กกำลังสูงขึ้น")

# ---------------------------------------------------------------------------
# รายงานสำหรับดาวน์โหลด
# ---------------------------------------------------------------------------
report = f"""COLUMN BASE PLATE DESIGN — AXIAL COMPRESSION ONLY
แนวทาง มยผ. (อ้างอิง AISC 360 J8 / AISC Design Guide 1)  วิธี: {method}
---------------------------------------------------------------
หน้าตัดเสา          : {sec_name}  (d={d_mm:g}, bf={bf_mm:g}, tw={tw_mm:g}, tf={tf_mm:g} mm)
น้ำหนักบรรทุก        : D = {PD:g} t, L = {PL:g} t  ->  {Preq} = {P_ton:,.2f} t
วัสดุ               : {grade} Fy = {Fy:,.0f} ksc ; f'c = {fc:,.0f} ksc
ตอม่อ               : {Np_mm:g} x {Bp_mm:g} mm
---------------------------------------------------------------
A1 = {r.A1:,.1f} cm2 ; A2 = {r.A2:,.1f} cm2 ; sqrt(A2/A1) = {r.sqrt_ratio:.3f}
Pp = {r.Pp:,.0f} kg ; กำลังแบกทานที่ใช้ได้ = {r.P_avail_bearing:,.0f} kg
Bearing ratio = {r.bearing_ratio:.3f}
m = {r.m:.2f} cm ; n = {r.n:.2f} cm ; X = {r.X:.3f} ; lambda = {r.lam:.3f} ; lambda*n' = {r.lam_n:.2f} cm
l = {r.l:.2f} cm ; t_req = {r.t_req * 10:.1f} mm ; t_use = {t_mm} mm
---------------------------------------------------------------
ผลลัพธ์: PL {N * 10:.0f} x {B * 10:.0f} x {t_mm} mm ; {n_bolt}-Ø{db_mm} mm anchor ; fillet weld >= {r.weld_min_mm:.0f} mm
สถานะ  : {"ผ่าน" if r.ok else "ไม่ผ่าน"}
""" + "\n".join(f"  - {k}: {'ผ่าน' if v else 'ไม่ผ่าน'}" for k, v in r.checks.items())

st.download_button("⬇️ ดาวน์โหลดรายการคำนวณ (.txt)", report.encode("utf-8"),
                   file_name="base_plate_design.txt", mime="text/plain")

st.divider()
st.caption(
    "หมายเหตุ: โปรแกรมนี้เป็นเครื่องมือช่วยคำนวณเบื้องต้น ผลลัพธ์ต้องได้รับการตรวจสอบและรับรองโดยวิศวกรผู้มีใบอนุญาต "
    "ฉบับและเลขข้อของมาตรฐาน มยผ. ที่ใช้ควรตรวจสอบกับเอกสารฉบับล่าสุดของกรมโยธาธิการและผังเมือง"
)
