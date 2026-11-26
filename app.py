import streamlit as st
import jwt
import datetime
import time
import hashlib
import json
import pandas as pd

# ==========================================
# 1. PAGE CONFIG & THEME STYLING
# ==========================================
st.set_page_config(
    page_title="Annapurna AI | Intelligent Food Rescue & Culinary Clarity",
    page_icon="🌿",
    layout="wide",
    initial_sidebar_state="expanded"
)

JWT_SECRET = "annapurna_ai_super_secret_key_2026"
JWT_ALGORITHM = "HS256"

# Custom CSS for Organic-Tech Editorial Aesthetic & Booming Clarify Cards
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,600;9..144,700&family=Plus+Jakarta+Sans:wght@400;500;600;700&family=JetBrains+Mono:wght@400;600&display=swap');

    html, body, [class*="css"] {
        font-family: 'Plus Jakarta Sans', sans-serif;
    }
    h1, h2, h3 {
        font-family: 'Fraunces', serif !important;
        color: #1A3A32;
    }
    .stApp {
        background-color: #FAF7F2;
    }
    .clarify-card {
        background: linear-gradient(135deg, #FFFFFF 0%, #F4EFE6 100%);
        border: 1.5px solid #D96B27;
        border-radius: 16px;
        padding: 22px;
        box-shadow: 0 10px 25px rgba(26, 58, 50, 0.08);
        margin-bottom: 18px;
    }
    .jwt-token-box {
        background-color: #142B25;
        color: #E8F5E9;
        font-family: 'JetBrains Mono', monospace;
        font-size: 12px;
        padding: 14px;
        border-radius: 10px;
        word-break: break-all;
        border-left: 4px solid #D96B27;
    }
    .badge-role {
        background-color: #1A3A32;
        color: #FAF7F2;
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 12px;
        font-weight: 600;
        letter-spacing: 0.5px;
    }
    .badge-amber {
        background-color: #D96B27;
        color: #FFFFFF;
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 12px;
        font-weight: 600;
    }
    .metric-box {
        background: #FFFFFF;
        border-radius: 12px;
        padding: 16px;
        border: 1px solid #E5DFD3;
        text-align: center;
    }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 2. JWT AUTHENTICATION ENGINE
# ==========================================
def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

def create_jwt_token(email: str, name: str, role: str, org: str, expiry_minutes: int = 30) -> str:
    now = datetime.datetime.now(datetime.timezone.utc)
    payload = {
        "sub": email,
        "name": name,
        "role": role,
        "org": org,
        "scope": ["clarify:execute", "rescue:read", "rescue:write" if role != "AI Chef / Consumer" else "chef:synthesize"],
        "iat": int(now.timestamp()),
        "exp": int((now + datetime.timedelta(minutes=expiry_minutes)).timestamp()),
        "iss": "annapurna-ai-auth-node"
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

def verify_jwt_token(token: str):
    try:
        decoded = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return decoded, None
    except jwt.ExpiredSignatureError:
        return None, "JWT Token has expired. Please refresh or sign in again."
    except jwt.InvalidTokenError as e:
        return None, f"Invalid JWT Signature: {str(e)}"

# ==========================================
# 3. SESSION STATE INITIALIZATION
# ==========================================
if "users_db" not in st.session_state:
    st.session_state.users_db = {
        "chef@annapurna.ai": {
            "name": "Aarav Sharma",
            "password": hash_password("Annapurna123!"),
            "role": "Donor / Restaurant",
            "org": "Saffron Leaf Kitchens, Bengaluru"
        },
        "ngo@annapurna.ai": {
            "name": "Meera Nair",
            "password": hash_password("Annapurna123!"),
            "role": "NGO / Food Bank",
            "org": "Roti & Hope Foundation"
        }
    }

if "jwt_token" not in st.session_state:
    st.session_state.jwt_token = None

if "surplus_feed" not in st.session_state:
    st.session_state.surplus_feed = [
        {
            "id": "BATCH-901",
            "donor": "Saffron Leaf Kitchens",
            "items": "45x Vegetable Biryani Trays, 30x Dal Tadka",
            "dietary": "100% Vegetarian • Nut-Free",
            "window": "2.5 Hours (Cold-Chain Packed)",
            "radius": "6 km (Indiranagar Hub)",
            "clarity_score": 98,
            "status": "Available"
        },
        {
            "id": "BATCH-902",
            "donor": "Artisan Crust Bakery",
            "items": "60x Sourdough Loaves, 25x Multigrain Focaccia",
            "dietary": "Vegan • Contains Gluten",
            "window": "6.0 Hours (Ambient Sealed)",
            "radius": "12 km (Koramangala)",
            "clarity_score": 96,
            "status": "Available"
        }
    ]

# ==========================================
# 4. AUTHENTICATION GATEWAY (LOGIN / REGISTER)
# ==========================================
def render_auth_screen():
    col1, col2, col3 = st.columns([1, 2.2, 1])
    with col2:
        st.markdown("<h1 style='text-align:center; font-size:2.8rem;'>🌿 Annapurna AI</h1>", unsafe_allow_html=True)
        st.markdown("<p style='text-align:center; color:#4A5D57; font-size:1.1rem;'>Zero-Waste Food Intelligence & JWT-Secured Surplus Redistribution</p>", unsafe_allow_html=True)
        st.divider()

        tab_login, tab_register = st.tabs(["🔐 JWT Sign In", "✨ Create Verified Account"])

        with tab_login:
            with st.form("login_form"):
                email = st.text_input("Email Address", value="chef@annapurna.ai")
                password = st.text_input("Password", type="password", value="Annapurna123!")
                col_a, col_b = st.columns(2)
                submitted = col_a.form_submit_button("Sign In & Issue JWT", use_container_width=True, type="primary")
                demo_ngo = col_b.form_submit_button("⚡ 1-Click NGO Demo JWT", use_container_width=True)

                if submitted:
                    user = st.session_state.users_db.get(email)
                    if user and user["password"] == hash_password(password):
                        token = create_jwt_token(email, user["name"], user["role"], user["org"])
                        st.session_state.jwt_token = token
                        st.rerun()
                    else:
                        st.error("Invalid credentials. Try `chef@annapurna.ai` / `Annapurna123!`.")

                if demo_ngo:
                    ngo_user = st.session_state.users_db["ngo@annapurna.ai"]
                    st.session_state.jwt_token = create_jwt_token(
                        "ngo@annapurna.ai", ngo_user["name"], ngo_user["role"], ngo_user["org"]
                    )
                    st.rerun()

        with tab_register:
            with st.form("register_form"):
                new_name = st.text_input("Full Name", placeholder="e.g., Priya Menon")
                new_email = st.text_input("Work Email", placeholder="priya@greenkitchen.in")
                new_org = st.text_input("Organization / Kitchen Name", placeholder="e.g., GreenHarvest Bistro")
                new_role = st.selectbox("JWT Access Role Claim", [
                    "Donor / Restaurant",
                    "NGO / Food Bank",
                    "AI Chef / Consumer"
                ])
                new_pass = st.text_input("Create Password", type="password")
                reg_submit = st.form_submit_button("Mint Account & Generate HS256 JWT", use_container_width=True, type="primary")

                if reg_submit:
                    if new_email and new_pass and new_name:
                        st.session_state.users_db[new_email] = {
                            "name": new_name,
                            "password": hash_password(new_pass),
                            "role": new_role,
                            "org": new_org or "Independent Node"
                        }
                        st.session_state.jwt_token = create_jwt_token(new_email, new_name, new_role, new_org or "Independent Node")
                        st.success("Account created! Issuing signed JWT...")
                        time.sleep(0.6)
                        st.rerun()
                    else:
                        st.warning("Please fill in Name, Email, and Password.")

# ==========================================
# 5. MAIN APPLICATION (PROTECTED BY JWT)
# ==========================================
if not st.session_state.jwt_token:
    render_auth_screen()
    st.stop()

decoded_jwt, auth_error = verify_jwt_token(st.session_state.jwt_token)
if auth_error:
    st.error(f"🔒 Authentication Interrupted: {auth_error}")
    st.session_state.jwt_token = None
    if st.button("Return to Login"):
        st.rerun()
    st.stop()

# ==========================================
# 6. SIDEBAR: LIVE JWT TOKEN INSPECTOR & ROLE SWITCHER
# ==========================================
with st.sidebar:
    st.markdown("### 🛡️ JWT Security Session")
    st.markdown(f"**{decoded_jwt['name']}**")
    st.caption(f"{decoded_jwt['org']}")
    st.markdown(f"<span class='badge-role'>{decoded_jwt['role']}</span>", unsafe_allow_html=True)

    # Calculate remaining token TTL
    now_ts = int(datetime.datetime.now(datetime.timezone.utc).timestamp())
    ttl_seconds = max(0, decoded_jwt["exp"] - now_ts)
    mins, secs = divmod(ttl_seconds, 60)
    st.info(f"⏱️ Token TTL Remaining: **{mins}m {secs}s**")

    with st.expander("🔍 Live JWT Inspector (HS256)", expanded=True):
        parts = st.session_state.jwt_token.split(".")
        st.markdown("**Encoded Bearer Token:**")
        st.markdown(
            f"<div class='jwt-token-box'>"
            f"<span style='color:#FF8A65'>{parts[0]}</span>."
            f"<span style='color:#81C784'>{parts[1]}</span>."
            f"<span style='color:#64B5F6'>{parts[2]}</span>"
            f"</div>",
            unsafe_allow_html=True
        )
        st.markdown("**Decoded Claims Payload:**")
        st.json(decoded_jwt)

    st.divider()
    st.markdown("**⚡ Dynamic Role Claim Switcher**")
    switched_role = st.selectbox(
        "Re-sign JWT with Role:",
        ["Donor / Restaurant", "NGO / Food Bank", "AI Chef / Consumer"],
        index=["Donor / Restaurant", "NGO / Food Bank", "AI Chef / Consumer"].index(decoded_jwt["role"])
    )
    col_r1, col_r2 = st.columns(2)
    if col_r1.button("🔄 Refresh JWT", use_container_width=True):
        st.session_state.jwt_token = create_jwt_token(
            decoded_jwt["sub"], decoded_jwt["name"], switched_role, decoded_jwt["org"]
        )
        st.rerun()

    if col_r2.button("🚪 Sign Out", use_container_width=True):
        st.session_state.jwt_token = None
        st.rerun()

# ==========================================
# 7. HEADER & IMPACT TELEMETRY
# ==========================================
st.markdown("<h1>🌿 Annapurna AI — Intelligent Food Rescue & Clarity Engine</h1>", unsafe_allow_html=True)
st.caption(f"Authenticated Node: `{decoded_jwt['sub']}` • Scope: `{', '.join(decoded_jwt['scope'])}`")

m1, m2, m3, m4 = st.columns(4)
m1.markdown("<div class='metric-box'><h3>14,820</h3><p>Meals Rescued</p></div>", unsafe_allow_html=True)
m2.markdown("<div class='metric-box'><h3>6.4 Tons</h3><p>CO₂ Emissions Prevented</p></div>", unsafe_allow_html=True)
m3.markdown("<div class='metric-box'><h3>98.4%</h3><p>Clarify™ Match Accuracy</p></div>", unsafe_allow_html=True)
m4.markdown("<div class='metric-box'><h3>18 mins</h3><p>Avg Dispatch Latency</p></div>", unsafe_allow_html=True)

st.write("")

# ==========================================
# 8. NAVIGATION TABS
# ==========================================
tab_clarify, tab_hub, tab_chef = st.tabs([
    "✨ Annapurna Clarify™ Engine (Booming Mode)",
    "🚚 Live Surplus Redistribution Hub",
    "🍲 Zero-Waste AI Chef Synthesizer"
])

# ------------------------------------------
# TAB 1: BOOMING CLARIFICATION ENGINE
# ------------------------------------------
with tab_clarify:
    st.subheader("Turn Ambiguous Kitchen Notes into High-Precision Rescue Payloads")
    st.write("Enter rough leftover or pantry notes below. **Annapurna Clarify™** detects missing safety, allergen, and logistics signals and boosts clarity to **99%**.")

    raw_input = st.text_area(
        "Raw Kitchen / Pantry Note:",
        value="We have around 40 boxes of paneer curry and rice left from a corporate lunch event. Need pickup tonight.",
        height=90
    )

    # Ambiguity Detection Heuristic
    blind_spots = []
    if not any(w in raw_input.lower() for w in ["fridge", "chilled", "hot", "temp", "hour", "time"]):
        blind_spots.append("Missing Thermal & Safe-Consumption Window")
    if not any(w in raw_input.lower() for w in ["nut", "vegan", "jain", "allergen", "gluten", "dairy"]):
        blind_spots.append("Unspecified Allergen & Dietary Tags")
    if not any(w in raw_input.lower() for w in ["km", "radius", "address", "hub", "delivery"]):
        blind_spots.append("Missing Pickup Radius / Cold-Chain Logistics")

    base_score = max(34, 100 - (len(blind_spots) * 21))

    st.markdown("<div class='clarify-card'>", unsafe_allow_html=True)
    st.markdown("#### ⚡ Interactive Clarification Matrix")
    if blind_spots:
        st.warning(f"**{len(blind_spots)} Critical Ambiguities Detected:** " + " • ".join(blind_spots))

    c1, c2, c3 = st.columns(3)
    with c1:
        thermal_state = st.pills(
            "1. Thermal & Shelf State",
            ["Hot-Held (>60°C)", "Blast-Chilled (<4°C)", "Ambient Sealed"],
            default="Blast-Chilled (<4°C)"
        )
        safe_hours = st.slider("Safe Window (Hours)", 1.0, 12.0, 4.0, 0.5)

    with c2:
        dietary_tags = st.multiselect(
            "2. Dietary & Allergen Verification",
            ["100% Vegetarian", "Contains Dairy", "Nut-Free", "Gluten-Free", "Jain Friendly", "Vegan"],
            default=["100% Vegetarian", "Contains Dairy", "Nut-Free"]
        )

    with c3:
        pickup_radius = st.select_slider(
            "3. Dispatch Radius",
            options=["2 km", "5 km", "10 km", "15 km", "25 km"],
            value="10 km"
        )
        packaging = st.pills(
            "Packaging Format",
            ["Foil Trays", "Biodegradable Boxes", "Bulk Cambros"],
            default="Biodegradable Boxes"
        )

    # Calculate Boosted Clarity Score
    boost = 0
    if thermal_state: boost += 22
    if dietary_tags: boost += 22
    if pickup_radius and packaging: boost += 21
    final_clarity = min(99, base_score + boost)

    st.markdown(f"**Clarity Confidence Score: `{base_score}%` ➔ `{final_clarity}%` (+{final_clarity - base_score}% Booming Boost)**")
    st.progress(final_clarity / 100)

    # Synthesized Structured Output
    clarified_summary = {
        "batch_origin": decoded_jwt["org"],
        "authorized_by": decoded_jwt["sub"],
        "role_claim": decoded_jwt["role"],
        "raw_description": raw_input,
        "thermal_protocol": f"{thermal_state} ({safe_hours}h window)",
        "verified_dietary": dietary_tags,
        "logistics": f"{packaging} • Within {pickup_radius}",
        "clarity_confidence": f"{final_clarity}%"
    }

    with st.expander("📄 View Clarified Structured JSON Payload", expanded=False):
        st.json(clarified_summary)

    if st.button("🚀 Broadcast Clarified Batch to Rescue Network", type="primary", use_container_width=True):
        new_batch = {
            "id": f"BATCH-{903 + len(st.session_state.surplus_feed)}",
            "donor": decoded_jwt["org"],
            "items": raw_input[:65] + ("..." if len(raw_input) > 65 else ""),
            "dietary": " • ".join(dietary_tags) if dietary_tags else "Standard",
            "window": f"{safe_hours} Hours ({thermal_state})",
            "radius": f"{pickup_radius} ({packaging})",
            "clarity_score": final_clarity,
            "status": "Available"
        }
        st.session_state.surplus_feed.insert(0, new_batch)
        st.success(f"✅ Batch **{new_batch['id']}** signed with JWT & published at **{final_clarity}% clarity**!")
    st.markdown("</div>", unsafe_allow_html=True)

# ------------------------------------------
# TAB 2: LIVE SURPLUS REDISTRIBUTION HUB
# ------------------------------------------
with tab_hub:
    st.subheader("Live JWT-Verified Surplus Batches")
    for idx, batch in enumerate(st.session_state.surplus_feed):
        with st.container(border=True):
            col_info, col_meta, col_action = st.columns([2.5, 2, 1.2])
            with col_info:
                st.markdown(f"#### {batch['id']} — {batch['donor']}")
                st.write(batch["items"])
                st.caption(f"🥗 {batch['dietary']}")
            with col_meta:
                st.markdown(f"⏱️ **{batch['window']}**")
                st.markdown(f"📍 **{batch['radius']}**")
                st.markdown(f"<span class='badge-amber'>Clarity: {batch['clarity_score']}%</span>", unsafe_allow_html=True)
            with col_action:
                st.write("")
                if batch["status"] == "Available":
                    if st.button(f"Claim Batch", key=f"claim_{batch['id']}", use_container_width=True, type="primary"):
                        st.session_state.surplus_feed[idx]["status"] = f"Claimed by {decoded_jwt['org']}"
                        st.rerun()
                else:
                    st.success(batch["status"])

# ------------------------------------------
# TAB 3: ZERO-WASTE AI CHEF SYNTHESIZER
# ------------------------------------------
with tab_chef:
    st.subheader("Zero-Waste Culinary Synthesis")
    st.write("Transform near-expiry produce and surplus staples into high-nutrition community meals.")
    ingredients = st.text_input(
        "Enter available surplus ingredients:",
        value="Overripe tomatoes, leftover cooked rice, spinach, paneer cubes, ginger"
    )
    cuisine_style = st.selectbox("Target Culinary Profile:", ["North Indian Comfort", "South Indian Tiffin", "Continental One-Pot"])

    if st.button("✨ Generate Clarified Zero-Waste Recipe", type="primary"):
        st.markdown(f"""
        ### 🍲 Roasted Tomato & Spinach Paneer Khichdi Bowl ({cuisine_style})
        - **Zero-Waste Yield:** Converts 100% of softened tomatoes into a rich roasted base; rehydrates day-old rice safely at >75°C.
        - **Prep & Thermal Protocol:** 22 minutes • High-heat tempering to ensure microbial safety.
        - **Nutritional Density:** 24g Protein • Rich in Iron & Lycopene • **0g Kitchen Scrap**.
        """)
