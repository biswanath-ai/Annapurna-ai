import streamlit as st
import requests
import base64
from io import BytesIO
from PIL import Image
import json
import re
import random
import pandas as pd

st.set_page_config(
    page_title="AnnapurnaAI | Zero Food Waste Platform",
    page_icon="🍲",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
    .hero-box {
        background: linear-gradient(135deg, #0f5132 0%, #198754 100%);
        padding: 1.6rem 2rem;
        border-radius: 14px;
        color: white;
        margin-bottom: 1.2rem;
        box-shadow: 0 4px 14px rgba(0, 0, 0, 0.12);
    }
    .hero-box h1 {
        margin: 0;
        font-size: 2.1rem;
        color: white;
    }
    .hero-box p {
        margin: 0.4rem 0 0 0;
        font-size: 1.05rem;
        color: #e9f7ef;
    }
    .badge-pill {
        display: inline-block;
        background-color: rgba(255, 255, 255, 0.18);
        padding: 0.25rem 0.75rem;
        border-radius: 999px;
        font-size: 0.82rem;
        font-weight: 600;
        margin-top: 0.7rem;
    }
</style>
""", unsafe_allow_html=True)

if "donations" not in st.session_state:
    st.session_state.donations = list((
        {
            "dish": "Steamed Rice & Dal Tadka",
            "portions": 35,
            "shelf_life": "3 Hours",
            "location": "NIST Hostel Mess 1 (1.2 km away)",
            "ngo": "Asha Kiran Welfare Trust",
            "status": "Available",
            "otp": "4821",
            "safety": "Verified Hygienic & Covered"
        },
        {
            "dish": "Veg Pulao & Paneer Masala",
            "portions": 22,
            "shelf_life": "2.5 Hours",
            "location": "NIST Central Cafeteria (0.8 km away)",
            "ngo": "Berhampur Roti Bank",
            "status": "Available",
            "otp": "7390",
            "safety": "Verified Hygienic & Covered"
        }
    ))

if "meals_rescued" not in st.session_state:
    st.session_state.meals_rescued = 1240

st.markdown("""
<div class="hero-box">
    <h1>🍲 AnnapurnaAI</h1>
    <p>AI-Powered Campus Food Waste Prevention & Hyperlocal NGO Redistribution</p>
    <span class="badge-pill">🌱 Team RudraGrid • NIST University Hub, Berhampur</span>
</div>
""", unsafe_allow_html=True)

with st.sidebar:
    st.header("⚙️ Live System Status")
    st.success("✅ Vision AI Engine Active")
    st.info("📡 Active Radius: 5.0 km around NIST Campus")
    st.divider()
    st.subheader("🏥 Connected Local NGOs")
    st.markdown("* Berhampur Roti Bank (1.4 km)\n* Asha Kiran Welfare Trust (2.1 km)\n* Ganjam Seva Foundation (3.6 km)")
    st.divider()
    st.caption("Built for HackKalp • Agriculture & Sustainability Track")

food_kg = round(st.session_state.meals_rescued * 0.35, 1)
co2_kg = round(food_kg * 2.5, 1)

m1, m2, m3, m4 = st.columns(4)
m1.metric("🍽️ Total Meals Rescued", f"{st.session_state.meals_rescued:,}", "+22 today")
m2.metric("⚖️ Food Waste Prevented", f"{food_kg} kg", "Zero landfill")
m3.metric("🌍 CO₂ Emissions Saved", f"{co2_kg} kg", "-18% kitchen footprint")
m4.metric("🚚 Avg. NGO Pickup Time", "24 Mins", "Within safety window")

st.divider()

tab1, tab2, tab3 = st.tabs(list((
    "📊 1. AI Kitchen Prep Advisor",
    "📸 2. Vision AI Surplus Scanner",
    "🤝 3. Live NGO Dispatch & Map"
)))

with tab1:
    st.subheader("Pre-Service Meal Demand Forecaster")
    st.write("Calibrates daily cooking quantities using campus schedules and student attendance patterns.")

    col1, col2 = st.columns(list((1, 1)))
    with col1:
        with st.container(border=True):
            meal_type = st.selectbox("Select Meal Service", list(("Lunch", "Dinner", "Breakfast")))
            day_type = st.selectbox("Campus Schedule / Event", list((
                "Regular Working Day",
                "Weekend / Sunday",
                "College Fest / Event (Sankalp)",
                "Exam Week / Holiday"
            )))
            registered_students = st.slider(
                "Total Hostel Students Registered",
                min_value=100,
                max_value=1500,
                value=450,
                step=25
            )

            factors = {
                "Regular Working Day": 0.90,
                "Weekend / Sunday": 0.76,
                "College Fest / Event (Sankalp)": 0.62,
                "Exam Week / Holiday": 0.68
            }
            predicted_headcount = int(registered_students * factors.get(day_type, 0.9))
            saved_meals = registered_students - predicted_headcount

            st.success(f"🎯 Optimal Prep Target: Cook {predicted_headcount} plates instead of {registered_students} plates.")
            b1, b2 = st.columns(2)
            b1.metric("Rice / Grain Prep", f"{round(predicted_headcount * 0.18, 1)} kg")
            b2.metric("Dal / Curry Prep", f"{round(predicted_headcount * 0.22, 1)} L")

    with col2:
        with st.container(border=True):
            st.markdown("#### 📉 Overproduction Reduction Comparison")
            chart_df = pd.DataFrame({
                "Prep Method": list(("Traditional Guesswork", "AnnapurnaAI Target")),
                "Plates Prepared": list((registered_students, predicted_headcount))
            }).set_index("Prep Method")
            st.bar_chart(chart_df, color="#198754", height=260)
            st.caption(f"Prevents {saved_meals} surplus plates (~{round(saved_meals * 0.35, 1)} kg) before cooking even begins.")

with tab2:
    st.subheader("5-Second Leftover Tray Scanner & Safety Check")
    st.write("Snap a photo of surplus trays. Vision AI identifies the dish, estimates portions, and verifies food safety.")

    scan_col1, scan_col2 = st.columns(list((1, 1)))
    with scan_col1:
        uploaded_file = st.file_uploader(
            "Upload Leftover Food Tray Photo",
            type=list(("jpg", "jpeg", "png", "webp"))
        )
        if uploaded_file is not None:
            image = Image.open(uploaded_file).convert("RGB")
            image.thumbnail(tuple((800, 800)))
            st.image(image, caption="Uploaded Kitchen Tray", use_container_width=True)

    with scan_col2:
        with st.container(border=True):
            st.markdown("#### 🛡️ Mandatory Food Safety Protocol")
            check_fresh = st.checkbox("Cooked within the last 2 hours", value=True)
            check_hygiene = st.checkbox("Stored in clean, covered food-grade trays", value=True)
            kitchen_loc = st.selectbox("Dispatch Kitchen Location", list((
                "NIST Central Cafeteria (0.5 km)",
                "NIST Hostel Mess 1 (1.2 km)",
                "NIST Hostel Mess 2 (1.5 km)"
            )))

            if uploaded_file is not None:
                if st.button("🔍 Scan Tray & Broadcast to NGOs", type="primary", use_container_width=True):
                    if not (check_fresh and check_hygiene):
                        st.error("⚠️ Please verify both food safety checks before alerting NGOs.")
                    else:
                        with st.spinner("Analyzing food tray with Gemini Vision AI..."):
                            buffered = BytesIO()
                            image.save(buffered, format="JPEG", quality=85)
                            img_b64 = base64.b64encode(buffered.getvalue()).decode("utf-8")

                            prompt = (
                                "Identify the food dish in this image, estimate how many human meal portions "
                                "are visible as a single integer, and estimate safe room-temperature shelf life "
                                "like '3 Hours'. Return ONLY a JSON object with keys: dish, portions, shelf_life."
                            )

                            result = None
                            try:
                                clean_key = st.secrets.get("GEMINI_API_KEY", "").strip()
                            except Exception:
                                clean_key = ""

                            if clean_key:
                                endpoints = list((
                                    f"https://googleapis.com{clean_key}",
                                    f"https://googleapis.com{clean_key}"
                                ))

                                for url in endpoints:
                                    try:
                                        payload = {
                                            "contents": list((
                                                {
                                                    "parts": list((
                                                        {"text": prompt},
                                                        {"inline_data": {"mime_type": "image/jpeg", "data": img_b64}}
                                                    ))
                                                },
                                            )),
                                            "generationConfig": {
                                                "response_mime_type": "application/json",
                                                "temperature": 0.2
                                            }
                                        }
                                        res = requests.post(url, json=payload, timeout=20)
                                        if res.status_code == 200:
                                            data = res.json()
                                            candidates = data.get("candidates", ())
                                            first_cand = next(iter(candidates), {})
                                            parts = first_cand.get("content", {}).get("parts", ())
                                            raw_text = ""
                                            for p in parts:
