
import streamlit as st
import pandas as pd
import plotly.express as px


# -------------------------------
# ตั้งค่าหน้า Dashboard
# -------------------------------

st.set_page_config(
    page_title="ระบบ Dashboard คอนโด",
    page_icon="🏢",
    layout="wide"
)

st.title("🏢 ระบบคำนวณและแดชบอร์ดเปรียบเทียบการผ่อนชำระคอนโด")

st.caption(
    "อ่านข้อมูลจาก condo_output.csv "
    "คำนวณยอดชำระรวม และแสดงผลในรูปแบบ Dashboard"
)


# -------------------------------
# ข้อมูลตัวอย่าง
# ใช้เมื่อยังไม่ได้อัปโหลดไฟล์
# -------------------------------

data = {
    "ชื่อลูกค้า": [
        "นายสมชาย ใจดี",
        "นางสาวสายฝน สดใส",
        "นายอาทิตย์ สุขใจ",
        "นางสาวพิมพ์ชนก แสนสวย",
        "นายธนกร มั่นคง"
    ],

    "เงินต้น (บาท)": [
        1000000,
        2000000,
        3000000,
        4000000,
        5000000
    ],

    "ระยะเวลา (ปี)": [
        5, 10, 15, 20, 25
    ],

    "ค่างวด/เดือน (บาท)": [
        19000,
        22300,
        25600,
        29000,
        33000
    ]
}

df = pd.DataFrame(data)


# -------------------------------
# อัปโหลดไฟล์ CSV
# -------------------------------

st.subheader("📂 นำเข้าข้อมูล")

uploaded_file = st.file_uploader(
    "เลือกไฟล์ condo_output.csv",
    type=["csv"]
)

if uploaded_file is not None:

    df = pd.read_csv(uploaded_file)

    st.success("อ่านไฟล์ CSV เรียบร้อยแล้ว")


# -------------------------------
# ตรวจสอบคอลัมน์
# -------------------------------

required_columns = [
    "ชื่อลูกค้า",
    "เงินต้น (บาท)",
    "ระยะเวลา (ปี)",
    "ค่างวด/เดือน (บาท)"
]

if all(col in df.columns for col in required_columns):

    # แปลงข้อมูลตัวเลข
    df["เงินต้น (บาท)"] = pd.to_numeric(
        df["เงินต้น (บาท)"], errors="coerce"
    )

    df["ระยะเวลา (ปี)"] = pd.to_numeric(
        df["ระยะเวลา (ปี)"], errors="coerce"
    )

    df["ค่างวด/เดือน (บาท)"] = pd.to_numeric(
        df["ค่างวด/เดือน (บาท)"], errors="coerce"
    )

    # ลบแถวที่ข้อมูลไม่ครบ
    df = df.dropna(subset=required_columns)

    # คำนวณยอดชำระรวม
    df["ยอดชำระรวม (บาท)"] = (
        df["ค่างวด/เดือน (บาท)"]
        * df["ระยะเวลา (ปี)"]
        * 12
    )

    # คำนวณดอกเบี้ยรวม
    df["ดอกเบี้ยรวม (บาท)"] = (
        df["ยอดชำระรวม (บาท)"]
        - df["เงินต้น (บาท)"]
    )

    # -------------------------------
    # สรุปข้อมูลด้านบน
    # -------------------------------

    st.divider()

    st.subheader("📌 สรุปข้อมูลภาพรวมการผ่อนคอนโด")

    col1, col2, col3, col4 = st.columns(4)

    total_customer = len(df)

    total_principal = df["เงินต้น (บาท)"].sum()

    total_payment = df["ยอดชำระรวม (บาท)"].sum()

    total_interest = df["ดอกเบี้ยรวม (บาท)"].sum()

    col1.metric(
        "จำนวนลูกค้าทั้งหมด",
        f"{total_customer:,} คน"
    )

    col2.metric(
        "เงินต้นรวม",
        f"฿{total_principal:,.2f}"
    )

    col3.metric(
        "ยอดชำระรวม",
        f"฿{total_payment:,.2f}"
    )

    col4.metric(
        "ดอกเบี้ยรวม",
        f"฿{total_interest:,.2f}"
    )

    # -------------------------------
    # กราฟ
    # -------------------------------

    st.divider()

    st.subheader("📊 กราฟวิเคราะห์และเปรียบเทียบข้อมูล")

    left, right = st.columns(2)

    # กราฟแท่งเปรียบเทียบยอดเงิน
    with left:

        st.markdown("#### เปรียบเทียบเงินต้นและยอดชำระรวม")

        chart_data = df.melt(
            id_vars=["ชื่อลูกค้า"],
            value_vars=[
                "เงินต้น (บาท)",
                "ยอดชำระรวม (บาท)"
            ],
            var_name="ประเภท",
            value_name="จำนวนเงิน"
        )

        fig1 = px.bar(
            chart_data,
            x="ชื่อลูกค้า",
            y="จำนวนเงิน",
            color="ประเภท",
            barmode="group",
            text_auto=".2s"
        )

        fig1.update_layout(
            xaxis_title="ลูกค้า",
            yaxis_title="จำนวนเงิน (บาท)",
            legend_title="ประเภท"
        )

        st.plotly_chart(
            fig1,
            use_container_width=True
        )

    # กราฟกระจาย
    with right:

        st.markdown(
            "#### ความสัมพันธ์ระหว่างระยะเวลาผ่อนกับยอดชำระ"
        )

        fig2 = px.scatter(
            df,
            x="ระยะเวลา (ปี)",
            y="ยอดชำระรวม (บาท)",
            size="เงินต้น (บาท)",
            color="ชื่อลูกค้า",
            hover_data=[
                "ค่างวด/เดือน (บาท)",
                "ดอกเบี้ยรวม (บาท)"
            ],
            text="ชื่อลูกค้า"
        )

        fig2.update_layout(
            xaxis_title="ระยะเวลาผ่อน (ปี)",
            yaxis_title="ยอดชำระรวม (บาท)"
        )

        st.plotly_chart(
            fig2,
            use_container_width=True
        )

    # -------------------------------
    # ตารางข้อมูล
    # -------------------------------

    st.divider()

    st.subheader("📋 ตารางเปรียบเทียบข้อมูลลูกค้า")

    st.dataframe(
        df.style.format({
            "เงินต้น (บาท)": "{:,.2f}",
            "ค่างวด/เดือน (บาท)": "{:,.2f}",
            "ยอดชำระรวม (บาท)": "{:,.2f}",
            "ดอกเบี้ยรวม (บาท)": "{:,.2f}"
        }),
        use_container_width=True,
        hide_index=True
    )

    # -------------------------------
    # ดาวน์โหลดไฟล์ CSV
    # -------------------------------

    csv = df.to_csv(
        index=False,
        encoding="utf-8-sig"
    )

    st.download_button(
        label="📥 ดาวน์โหลดข้อมูล condo_output.csv",
        data=csv,
        file_name="condo_output.csv",
        mime="text/csv"
    )

else:

    st.error(
        "ชื่อคอลัมน์ในไฟล์ CSV ไม่ตรงกับที่โปรแกรมกำหนด"
    )

    st.write("คอลัมน์ที่ต้องมี ได้แก่")

    st.write(required_columns)