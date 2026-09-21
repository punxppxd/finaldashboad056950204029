
import io
import base64
from urllib.parse import quote

import pandas as pd
import plotly.express as px
import streamlit as st
import requests


# =========================================================
# ตั้งค่าหน้าเว็บ
# =========================================================
st.set_page_config(
    page_title="แดชบอร์ดเปรียบเทียบการผ่อนชำระคอนโด",
    page_icon="🏢",
    layout="wide",
    initial_sidebar_state="expanded",
)


# =========================================================
# CSS ปรับแต่งหน้าตา
# =========================================================
st.markdown(
    """
    <style>
        .main {
            background-color: #ffffff;
        }

        .block-container {
            max-width: 1200px;
            padding-top: 2rem;
            padding-bottom: 2rem;
        }

        h1, h2, h3 {
            color: #172554;
        }

        .dashboard-title {
            color: #172554;
            font-size: 2rem;
            font-weight: 700;
            margin-bottom: 0.25rem;
        }

        .dashboard-subtitle {
            color: #64748b;
            font-size: 0.9rem;
            margin-bottom: 1.5rem;
        }

        [data-testid="stMetric"] {
            background-color: #f8fafc;
            border: 1px solid #e2e8f0;
            padding: 15px;
            border-radius: 10px;
        }

        [data-testid="stMetricLabel"] {
            color: #475569;
        }

        [data-testid="stMetricValue"] {
            color: #1e3a8a;
            font-size: 1.6rem;
        }

        .section-title {
            color: #172554;
            font-size: 1.3rem;
            font-weight: 700;
            border-bottom: 2px solid #dbeafe;
            padding-bottom: 8px;
            margin-top: 20px;
            margin-bottom: 15px;
        }
    </style>
    """,
    unsafe_allow_html=True,
)


# =========================================================
# ค่าพื้นฐาน
# =========================================================
DEFAULT_INTEREST_RATE = 3.25

DEFAULT_DATA = pd.DataFrame(
    {
        "ชื่อลูกค้า": [
            "นายสมชาย ใจดี",
            "นางสาวสุภาวดี มีสุข",
            "นายวิทนา รุ่งเรือง",
            "นางสาวพิมพ์ชนก แสงทอง",
            "นายธนกร มั่นคง",
        ],
        "จำนวนเงินต้น": [
            1_000_000,
            2_000_000,
            3_000_000,
            4_000_000,
            5_000_000,
        ],
        "จำนวนปีที่ผ่อน": [5, 10, 15, 20, 25],
    }
)


# =========================================================
# ฟังก์ชันช่วยเหลือ
# =========================================================
def format_money(value):
    """จัดรูปแบบตัวเลขเป็นเงินบาท"""
    if pd.isna(value):
        return "฿0.00"

    return f"฿{value:,.2f}"


def find_column(df, possible_names):
    """ค้นหาชื่อคอลัมน์ที่ตรงกับชื่อที่กำหนด"""
    for column in df.columns:
        clean_column = str(column).strip().lower()

        for name in possible_names:
            if name.lower() in clean_column:
                return column

    return None


def prepare_data(df, interest_rate):
    """
    เตรียมข้อมูลและคำนวณคอลัมน์ต่าง ๆ

    สูตร:
    ดอกเบี้ยรวม = เงินต้น x อัตราดอกเบี้ยต่อปี x จำนวนปี
    ยอดชำระรวม = เงินต้น + ดอกเบี้ยรวม
    ค่างวดต่อเดือน = ยอดชำระรวม / จำนวนเดือน
    """

    df = df.copy()

    name_column = find_column(
        df,
        [
            "ชื่อลูกค้า",
            "ชื่อนักศึกษา",
            "ชื่อ",
            "name",
            "customer",
        ],
    )

    money_column = find_column(
        df,
        [
            "จำนวนเงินต้น",
            "เงินต้น",
            "principal",
            "money",
        ],
    )

    year_column = find_column(
        df,
        [
            "จำนวนปีที่ผ่อน",
            "จำนวนปี",
            "ปีที่ผ่อน",
            "years",
            "year",
        ],
    )

    if name_column is None or money_column is None or year_column is None:
        raise ValueError(
            "ไฟล์ต้องมีคอลัมน์ ชื่อลูกค้า, จำนวนเงินต้น และ จำนวนปีที่ผ่อน"
        )

    df = df.rename(
        columns={
            name_column: "ชื่อลูกค้า",
            money_column: "จำนวนเงินต้น",
            year_column: "จำนวนปีที่ผ่อน",
        }
    )

    df["จำนวนเงินต้น"] = (
        df["จำนวนเงินต้น"]
        .astype(str)
        .str.replace(",", "", regex=False)
        .str.replace("฿", "", regex=False)
        .str.strip()
    )

    df["จำนวนปีที่ผ่อน"] = (
        df["จำนวนปีที่ผ่อน"]
        .astype(str)
        .str.replace(",", "", regex=False)
        .str.strip()
    )

    df["จำนวนเงินต้น"] = pd.to_numeric(
        df["จำนวนเงินต้น"],
        errors="coerce",
    )

    df["จำนวนปีที่ผ่อน"] = pd.to_numeric(
        df["จำนวนปีที่ผ่อน"],
        errors="coerce",
    )

    df = df.dropna(
        subset=[
            "ชื่อลูกค้า",
            "จำนวนเงินต้น",
            "จำนวนปีที่ผ่อน",
        ]
    )

    df = df[
        (df["จำนวนเงินต้น"] > 0)
        & (df["จำนวนปีที่ผ่อน"] > 0)
    ]

    df["จำนวนปีที่ผ่อน"] = df["จำนวนปีที่ผ่อน"].astype(int)

    interest_decimal = interest_rate / 100

    df["ดอกเบี้ยรวม"] = (
        df["จำนวนเงินต้น"]
        * interest_decimal
        * df["จำนวนปีที่ผ่อน"]
    )

    df["ยอดชำระรวม"] = (
        df["จำนวนเงินต้น"]
        + df["ดอกเบี้ยรวม"]
    )

    df["จำนวนเดือน"] = df["จำนวนปีที่ผ่อน"] * 12

    df["ค่างวดต่อเดือน"] = (
        df["ยอดชำระรวม"] / df["จำนวนเดือน"]
    )

    return df


def load_csv_from_github(owner, repo, branch, file_path, token=""):
    """
    อ่าน CSV จาก GitHub Contents API
    """

    encoded_path = quote(file_path.strip("/"), safe="/")

    api_url = (
        f"https://api.github.com/repos/{owner}/{repo}"
        f"/contents/{encoded_path}?ref={branch}"
    )

    headers = {
        "Accept": "application/vnd.github+json"
    }

    if token.strip():
        headers["Authorization"] = f"Bearer {token.strip()}"

    response = requests.get(
        api_url,
        headers=headers,
        timeout=20,
    )

    if response.status_code != 200:
        raise ValueError(
            f"ไม่สามารถอ่านไฟล์จาก GitHub ได้ "
            f"HTTP Status: {response.status_code}"
        )

    result = response.json()

    if result.get("encoding") != "base64":
        raise ValueError("รูปแบบไฟล์จาก GitHub ไม่ใช่ base64")

    content = base64.b64decode(result["content"])

    try:
        return pd.read_csv(
            io.BytesIO(content),
            encoding="utf-8-sig",
        )
    except UnicodeDecodeError:
        return pd.read_csv(
            io.BytesIO(content),
            encoding="tis-620",
        )


def download_csv(df):
    """เตรียมไฟล์ CSV สำหรับดาวน์โหลด"""
    output = df.copy()

    output = output.rename(
        columns={
            "ดอกเบี้ยรวม": "ดอกเบี้ยรวม",
            "ยอดชำระรวม": "ยอดชำระรวม(total)",
            "ค่างวดต่อเดือน": "ค่างวดต่อเดือน",
        }
    )

    return output.to_csv(
        index=False,
        encoding="utf-8-sig",
    ).encode("utf-8-sig")


# =========================================================
# Sidebar
# =========================================================
with st.sidebar:
    st.header("⚙️ ตั้งค่าแดชบอร์ด")

    interest_rate = st.number_input(
        "อัตราดอกเบี้ยต่อปี (%)",
        min_value=0.0,
        max_value=100.0,
        value=DEFAULT_INTEREST_RATE,
        step=0.25,
    )

    st.divider()

    st.subheader("🔗 เชื่อมต่อ GitHub")

    github_owner = st.text_input(
        "GitHub Owner",
        value="",
        placeholder="เช่น nanthicha-c-afk",
    )

    github_repo = st.text_input(
        "Repository",
        value="",
        placeholder="เช่น condo-dashboard",
    )

    github_branch = st.text_input(
        "Branch",
        value="main",
    )

    github_file = st.text_input(
        "Path ของไฟล์ CSV",
        value="condo_output.csv",
    )

    github_token = st.text_input(
        "GitHub Token สำหรับ Repository Private",
        type="password",
        help="ไม่ต้องกรอกหาก Repository เป็น Public",
    )

    connect_github = st.button(
        "โหลดข้อมูลจาก GitHub",
        use_container_width=True,
        type="primary",
    )

    st.divider()

    uploaded_file = st.file_uploader(
        "หรืออัปโหลดไฟล์ CSV",
        type=["csv"],
    )

    use_sample_data = st.checkbox(
        "ใช้ข้อมูลตัวอย่าง",
        value=True,
    )


# =========================================================
# โหลดข้อมูล
# =========================================================
if "raw_data" not in st.session_state:
    st.session_state.raw_data = DEFAULT_DATA.copy()

if connect_github:
    if not github_owner or not github_repo or not github_file:
        st.error(
            "กรุณากรอก Owner, Repository และ Path ของไฟล์ให้ครบ"
        )
    else:
        try:
            with st.spinner("กำลังโหลดข้อมูลจาก GitHub..."):
                st.session_state.raw_data = load_csv_from_github(
                    owner=github_owner,
                    repo=github_repo,
                    branch=github_branch,
                    file_path=github_file,
                    token=github_token,
                )

            st.success("โหลดข้อมูลจาก GitHub สำเร็จแล้ว")

        except Exception as error:
            st.error(f"เกิดข้อผิดพลาด: {error}")

elif uploaded_file is not None:
    try:
        st.session_state.raw_data = pd.read_csv(
            uploaded_file,
            encoding="utf-8-sig",
        )

        st.success("โหลดไฟล์ CSV สำเร็จแล้ว")

    except Exception as error:
        st.error(f"ไม่สามารถอ่านไฟล์ CSV ได้: {error}")

elif use_sample_data and "raw_data" not in st.session_state:
    st.session_state.raw_data = DEFAULT_DATA.copy()


# =========================================================
# คำนวณข้อมูล
# =========================================================
try:
    data = prepare_data(
        st.session_state.raw_data,
        interest_rate,
    )

except Exception as error:
    st.error(f"ไม่สามารถเตรียมข้อมูลได้: {error}")
    st.stop()


if data.empty:
    st.warning("ไม่พบข้อมูลที่สามารถนำมาแสดงผลได้")
    st.stop()


# =========================================================
# หัวข้อ Dashboard
# =========================================================
st.markdown(
    '<div class="dashboard-title">🏢 ระบบคำนวณและแดชบอร์ดเปรียบเทียบการผ่อนชำระคอนโด</div>',
    unsafe_allow_html=True,
)

st.markdown(
    f"""
    <div class="dashboard-subtitle">
        แสดงข้อมูลลูกค้าและการคำนวณยอดชำระรวม
        โดยใช้อัตราดอกเบี้ย {interest_rate:.2f}% ต่อปี
        | จำนวนข้อมูล {len(data)} รายการ
    </div>
    """,
    unsafe_allow_html=True,
)


# =========================================================
# Summary Metrics
# =========================================================
total_customers = len(data)
total_principal = data["จำนวนเงินต้น"].sum()
total_payment = data["ยอดชำระรวม"].sum()
total_interest = data["ดอกเบี้ยรวม"].sum()

st.markdown(
    '<div class="section-title">📌 สรุปข้อมูลภาพรวมการผ่อนคอนโด</div>',
    unsafe_allow_html=True,
)

metric_1, metric_2, metric_3, metric_4 = st.columns(4)

with metric_1:
    st.metric(
        "จำนวนลูกค้าทั้งหมด",
        f"{total_customers:,} คน",
    )

with metric_2:
    st.metric(
        "เงินต้นรวมทั้งหมด",
        format_money(total_principal),
    )

with metric_3:
    st.metric(
        "ยอดชำระรวมทั้งหมด",
        format_money(total_payment),
    )

with metric_4:
    st.metric(
        "ดอกเบี้ยรวมทั้งหมด",
        format_money(total_interest),
    )


# =========================================================
# Charts
# =========================================================
st.markdown(
    '<div class="section-title">📈 กราฟวิเคราะห์และเปรียบเทียบข้อมูลสินเชื่อคอนโด</div>',
    unsafe_allow_html=True,
)

chart_col_1, chart_col_2 = st.columns(2)

with chart_col_1:
    chart_data = data[
        [
            "ชื่อลูกค้า",
            "จำนวนเงินต้น",
            "ดอกเบี้ยรวม",
        ]
    ].copy()

    chart_data = chart_data.melt(
        id_vars=["ชื่อลูกค้า"],
        value_vars=[
            "จำนวนเงินต้น",
            "ดอกเบี้ยรวม",
        ],
        var_name="ประเภทเงิน",
        value_name="จำนวนเงิน",
    )

    fig_bar = px.bar(
        chart_data,
        x="ชื่อลูกค้า",
        y="จำนวนเงิน",
        color="ประเภทเงิน",
        barmode="stack",
        text_auto=".2s",
        title="สัดส่วนเงินต้นและดอกเบี้ยรวม",
        color_discrete_map={
            "จำนวนเงินต้น": "#315b91",
            "ดอกเบี้ยรวม": "#d84f51",
        },
    )

    fig_bar.update_layout(
        xaxis_title="ลูกค้า",
        yaxis_title="จำนวนเงิน (บาท)",
        legend_title="ประเภท",
        height=450,
        margin=dict(l=10, r=10, t=60, b=80),
    )

    fig_bar.update_xaxes(
        tickangle=-25,
    )

    st.plotly_chart(
        fig_bar,
        use_container_width=True,
    )


with chart_col_2:
    fig_scatter = px.scatter(
        data,
        x="จำนวนปีที่ผ่อน",
        y="ค่างวดต่อเดือน",
        size="จำนวนเงินต้น",
        color="ชื่อลูกค้า",
        text="ชื่อลูกค้า",
        title="ความสัมพันธ์ระหว่างระยะเวลาผ่อนกับค่างวดต่อเดือน",
        labels={
            "จำนวนปีที่ผ่อน": "ระยะเวลาผ่อน (ปี)",
            "ค่างวดต่อเดือน": "ค่างวดต่อเดือน (บาท)",
            "ชื่อลูกค้า": "ลูกค้า",
        },
        color_discrete_sequence=[
            "#55b9a8",
            "#f39c9d",
            "#ef6a6a",
            "#8fc5ef",
            "#70c0a8",
        ],
    )

    fig_scatter.update_traces(
        textposition="top center",
        marker=dict(
            line=dict(
                width=1,
                color="white",
            )
        ),
    )

    fig_scatter.update_layout(
        height=450,
        margin=dict(l=10, r=10, t=60, b=50),
    )

    st.plotly_chart(
        fig_scatter,
        use_container_width=True,
    )


# =========================================================
# ตารางข้อมูล
# =========================================================
st.markdown(
    '<div class="section-title">📋 ตารางเปรียบเทียบข้อมูลลูกค้า</div>',
    unsafe_allow_html=True,
)

display_data = data[
    [
        "ชื่อลูกค้า",
        "จำนวนเงินต้น",
        "จำนวนปีที่ผ่อน",
        "ค่างวดต่อเดือน",
        "ยอดชำระรวม",
        "ดอกเบี้ยรวม",
    ]
].copy()

display_data = display_data.rename(
    columns={
        "ชื่อลูกค้า": "ชื่อลูกค้า",
        "จำนวนเงินต้น": "เงินต้น (บาท)",
        "จำนวนปีที่ผ่อน": "จำนวนปีที่ผ่อน",
        "ค่างวดต่อเดือน": "ค่างวด/เดือน (บาท)",
        "ยอดชำระรวม": "ยอดชำระรวม (บาท)",
        "ดอกเบี้ยรวม": "ดอกเบี้ยรวม (บาท)",
    }
)

st.dataframe(
    display_data.style.format(
        {
            "เงินต้น (บาท)": "{:,.2f}",
            "ค่างวด/เดือน (บาท)": "{:,.2f}",
            "ยอดชำระรวม (บาท)": "{:,.2f}",
            "ดอกเบี้ยรวม (บาท)": "{:,.2f}",
        }
    ),
    use_container_width=True,
    hide_index=True,
)


# =========================================================
# ดาวน์โหลดไฟล์ผลลัพธ์
# =========================================================
st.markdown(
    '<div class="section-title">⬇️ ดาวน์โหลดข้อมูล</div>',
    unsafe_allow_html=True,
)

st.download_button(
    label="ดาวน์โหลดผลลัพธ์เป็น CSV",
    data=download_csv(data),
    file_name="condo_dashboard_output.csv",
    mime="text/csv",
    type="primary",
)
