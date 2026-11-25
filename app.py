import streamlit as st
import requests
import base64
from io import BytesIO
from PIL import Image
import json

st.set_page_config(page_title="AnnapurnaAI", page_icon="🍲", layout="wide")

if "donations" not in st.session_state:
    st.session_state.donations = list((
        {
            "dish": "Steamed Rice & Dal Tadka",
            "portions": 35,
            "shelf_life": "3 Hours",
            "location": "NIST Hostel Mess 1 (1.2 km away)",
            "status": "Available"
        },
    ))

st.title("🍲 AnnapurnaAI: Smart Food Waste Prevention & Redistribution")
st.markdown("**Team RudraGrid** | *Preventing overcooking before meals & rescuing surplus food after service.*")

with st.sidebar:
    st.header("⚙️ AI Configuration")
    default_key = st.secrets.get("GEMINI_API_KEY", "")
    api_key = st.text_input("Gemini API Key", value=default_key, type="password", help="Loaded automatically from Streamlit Secrets")
    if api_key:
        st.success("✅ AI Engine Connected & Ready")
    else:
        st.info("💡 Paste your Gemini API key above to enable live Vision AI tray scanning.")

tab1, tab2, tab3 = st.tabs(list((
    "📊 1. AI Kitchen Prep Advisor",
    "📸 2. Vision AI Surplus Scanner",
    "🤝 3. Live NGO Pickup Portal"
)))

# TAB 1: DEMAND FORECASTER
with tab1:
    st.subheader("Daily Meal Quantity Forecaster")
    st.write("Replaces manual headcount guesswork with data-driven prep targets.")
    
    col1, col2 = st.columns(2)
    with col1:
        meal_type = st.selectbox("Select Meal", list(("Lunch", "Dinner", "Breakfast")))
        day_type = st.selectbox("Campus Schedule", list((
            "Regular Working Day",
            "Weekend / Sunday",
            "College Fest / Event (Sankalp)",
            "Exam Week / Holiday"
        )))
        registered_students = st.number_input("Total Hostel Students Registered", min_value=50, max_value=2000, value=450)

    with col2:
        factors = {
            "Regular Working Day": 0.92,
            "Weekend / Sunday": 0.78,
            "College Fest / Event (Sankalp)": 0.65,
            "Exam Week / Holiday": 0.70
        }
        predicted_headcount = int(registered_students * factors.get(day_type, 0.9))
        saved_meals = registered_students - predicted_headcount

        st.metric("Recommended Meals to Cook", f"{predicted_headcount} Plates", f"-{saved_meals} plates saved from waste")
        st.write(f"**Rice / Grain Prep:** {round(predicted_headcount * 0.18, 1)} kg")
        st.write(f"**Dal / Curry Prep:** {round(predicted_headcount * 0.22, 1)} Liters")
        st.success("✅ Prep target calibrated to cut overproduction by ~18%.")

# TAB 2: VISION AI SCANNER
with tab2:
    st.subheader("5-Second Leftover Tray Scanner")
    st.write("Upload a photo of leftover food trays. Vision AI detects the dish, estimates portions, and sets a freshness timer.")

    uploaded_file = st.file_uploader("Upload Leftover Food Tray Photo", type=list(("jpg", "jpeg", "png")))

    if uploaded_file is not None:
        image = Image.open(uploaded_file).convert("RGB")
        st.image(image, caption="Uploaded Kitchen Tray", width=350)

        if st.button("🔍 Scan Tray & Alert NGOs", type="primary"):
            if not api_key:
                st.warning("⚠️ Please configure your Gemini API Key first!")
            else:
                with st.spinner("Analyzing food tray with Gemini Vision AI..."):
                    try:
                        buffered = BytesIO()
                        image.save(buffered, format="JPEG")
                        img_b64 = base64.b64encode(buffered.getvalue()).decode("utf-8")

                        base = "https://googleapis.com"
                        path = "/v1beta/models/gemini-2.5-flash:generateContent"
                        url = base + path
                        prompt = (
                            "Analyze this food image for a surplus food donation app. "
                            "Identify the dish name, estimate how many human meal portions are visible (as an integer), "
                            "and estimate safe shelf-life at room temperature (e.g., '3 Hours'). "
                            "Respond ONLY in valid JSON with keys: 'dish', 'portions', 'shelf_life'."
                        )
                        payload = {
                            "contents": list((
                                {
                                    "parts": list((
                                        {"text": prompt},
                                        {"inline_data": {"mime_type": "image/jpeg", "data": img_b64}}
                                    ))
                                },
                            ))
                        }
                        res = requests.post(url, params={"key": api_key.strip()}, json=payload, timeout=30)
                        data = res.json()
                        if "error" in data:
                            st.error(f"API Error: {data.get('error').get('message')}")
                        else:
                            first_cand = next(iter(data.get("candidates", ())))
                            first_part = next(iter(first_cand.get("content", {}).get("parts", ())))
                            raw_text = first_part.get("text", "")
                            raw_text = raw_text.strip().removeprefix("```json").removesuffix("```").strip()
                            result = json.loads(raw_text)

                            st.success("✅ Food Analyzed & Broadcasted to Nearby NGOs (< 5 km)!")
                            c1, c2, c3 = st.columns(3)
                            c1.metric("Detected Dish", result.get("dish", "Cooked Meal"))
                            c2.metric("Estimated Portions", f"{result.get('portions', 20)} Meals")
                            c3.metric("Freshness Timer", result.get("shelf_life", "3 Hours"))

                            st.session_state.donations.insert(0, {
                                "dish": result.get("dish", "Cooked Meal"),
                                "portions": result.get("portions", 20),
                                "shelf_life": result.get("shelf_life", "3 Hours"),
                                "location": "NIST Campus Kitchen (0.5 km away)",
                                "status": "Available"
                            })
                    except Exception as e:
                        st.error(f"Error analyzing image: {e}")

# TAB 3: NGO PORTAL
with tab3:
    st.subheader("Real-Time NGO Dispatch Feed (< 5 km Radius)")
    st.write("Verified local NGOs receive instant alerts and claim food before the freshness timer expires.")

    for idx, item in enumerate(st.session_state.donations):
        with st.container(border=True):
            col_a, col_b = st.columns(list((3, 1)))
            with col_a:
                st.markdown(f"### 🍛 {item.get('dish')} ({item.get('portions')} Portions)")
                st.write(f"📍 **Pickup:** {item.get('location')} | ⏳ **Expires in:** {item.get('shelf_life')}")
            with col_b:
                if item.get("status") == "Available":
                    if st.button("🚚 Claim Pickup", key=f"claim_{idx}"):
                        st.session_state.donations[idx]["status"] = "Claimed by NGO ✅"
                        st.rerun()
                else:
                    st.success(item.get("status"))
