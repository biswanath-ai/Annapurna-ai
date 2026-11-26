import datetime as dt
import hashlib
import math
import random

import pandas as pd
import streamlit as st


st.set_page_config(page_title="AnnapurnaAI", page_icon="🍲", layout="wide")

MEAL_COST = 45
KG_PER_MEAL = 0.35
MAX_SAFE_HOLDING_HOURS = 4


def init_state():
    defaults = {
        "donations": [],
        "rescued": 0,
        "planned_plates": 405,
        "community_deliveries": [],
        "shortage_log": [],
        "audit_log": [],
        "ngos": [
            {"name": "Berhampur Roti Bank", "distance": 0.8, "capacity": 45, "need": 95, "available": True, "phone": "Verified partner"},
            {"name": "Asha Kiran Trust", "distance": 1.4, "capacity": 30, "need": 88, "available": True, "phone": "Verified partner"},
            {"name": "Ganjam Seva Foundation", "distance": 2.1, "capacity": 55, "need": 82, "available": True, "phone": "Verified partner"},
            {"name": "Saksham Community Kitchen", "distance": 3.3, "capacity": 25, "need": 91, "available": True, "phone": "Verified partner"},
            {"name": "Udaan Youth Collective", "distance": 4.6, "capacity": 20, "need": 76, "available": True, "phone": "Verified partner"},
        ],
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def log(event):
    st.session_state.audit_log.insert(0, {"time": dt.datetime.now().strftime("%d %b %H:%M"), "event": event})


def freshness_hours(cooked_at):
    return max(0.0, (dt.datetime.now() - dt.datetime.combine(dt.date.today(), cooked_at)).total_seconds() / 3600)


def food_is_safe(cooked_at, covered, temp_checked, allergen_label):
    age = freshness_hours(cooked_at)
    reasons = []
    if age > MAX_SAFE_HOLDING_HOURS:
        reasons.append(f"Food is {age:.1f} hours old, above this app's {MAX_SAFE_HOLDING_HOURS}-hour dispatch limit")
    if not covered:
        reasons.append("Food was not confirmed as clean and covered")
    if not temp_checked:
        reasons.append("Temperature check was not confirmed")
    if not allergen_label.strip():
        reasons.append("Allergen information is required")
    return not reasons, reasons, age


def rank_ngos(radius_km):
    """Rank by current need first, then pickup capacity and proximity."""
    candidates = [n.copy() for n in st.session_state.ngos if n["available"] and n["distance"] <= radius_km and n["capacity"] > 0]
    for ngo in candidates:
        ngo["score"] = round(ngo["need"] * 0.55 + min(ngo["capacity"], 50) * 0.25 + max(0, radius_km - ngo["distance"]) * 4, 1)
    return sorted(candidates, key=lambda n: (-n["score"], n["distance"]))


def allocate_to_ngos(portions, radius_km):
    remaining = portions
    plan = []
    for ngo in rank_ngos(radius_km):
        if remaining == 0:
            break
        assigned = min(remaining, ngo["capacity"])
        plan.append({"ngo": ngo["name"], "portions": assigned, "distance": ngo["distance"], "score": ngo["score"]})
        remaining -= assigned
    return plan, remaining


def add_donation(dish, portions, location, safe_hours, allergens, radius_km):
    allocations, unassigned = allocate_to_ngos(portions, radius_km)
    item = {
        "id": random.randint(10000, 99999), "dish": dish, "portions": portions, "location": location,
        "safe_hours": safe_hours, "allergens": allergens, "radius": radius_km,
        "allocations": allocations, "unassigned": unassigned, "status": "Awaiting NGO confirmation" if allocations else "Community fallback needed",
        "created": dt.datetime.now().strftime("%H:%M"),
    }
    st.session_state.donations.insert(0, item)
    log(f"Created surplus listing #{item['id']} for {portions} portions")
    return item


def predict_demand(students, attendance, event_factor, historic_waste, buffer):
    base = students * attendance * event_factor
    reduction = historic_waste / 100
    return max(1, math.ceil(base * (1 - reduction) * (1 + buffer / 100)))


def render_header():
    st.markdown("""<style>
    .stApp {background: linear-gradient(180deg,#fffaf0,#f0fdf4)}
    .hero {background:linear-gradient(135deg,#ea580c,#f59e0b 48%,#059669);padding:1.35rem 1.6rem;border-radius:16px;color:white;margin-bottom:1rem}
    .hero h1 {margin:0;color:white}.hero p {margin:.35rem 0 0;color:#fffbeb}
    div[data-testid=\"stMetric\"] {background:white;padding:.8rem;border-radius:12px;border-left:5px solid #10b981}
    </style><div class='hero'><h1>🍲 AnnapurnaAI</h1><p>Safe campus meal planning, surplus rescue, and fair community distribution</p></div>""", unsafe_allow_html=True)


def render_planner():
    st.subheader("1. Kitchen Demand & Shortage Advisor")
    left, right = st.columns(2)
    with left:
        students = st.number_input("Registered diners", 50, 5000, 450, 25)
        attendance = st.slider("Expected attendance", 40, 100, 90) / 100
        occasion = st.selectbox("Campus day", ["Regular day", "Weekend", "Exam week", "Festival / event"])
        factors = {"Regular day": 1.0, "Weekend": .84, "Exam week": .78, "Festival / event": 1.16}
        historic_waste = st.slider("Recent avoidable surplus (%)", 0, 30, 10)
        buffer = st.slider("Service buffer for unexpected diners (%)", 0, 20, 6)
        planned = predict_demand(students, attendance, factors[occasion], historic_waste, buffer)
        st.session_state.planned_plates = planned
        st.success(f"Recommended preparation: **{planned} plates**")
        st.caption("Recommendation combines expected attendance, event effects, recent surplus, and a controlled service buffer.")
    with right:
        rice = round(planned * .18, 1)
        curry = round(planned * .22, 1)
        st.metric("Rice to prepare", f"{rice} kg")
        st.metric("Dal/curry to prepare", f"{curry} L")
        st.metric("Estimated maximum avoidable surplus", f"{max(0, students - planned)} plates")
        st.info("Keep a small reserve of fast-cook items (rice, dal, eggs/vegetable option) rather than preparing all buffer portions in advance.")

    st.divider()
    st.markdown("#### 🚨 If more people arrive than food prepared")
    actual = st.number_input("Actual diners currently present", 0, 5000, planned, 1)
    served = st.number_input("Meals already served", 0, 5000, min(planned, actual), 1)
    remaining_food = max(0, planned - served)
    waiting = max(0, actual - served)
    if st.button("Run shortage response", type="primary"):
        if waiting <= remaining_food:
            st.success(f"Enough prepared food remains for the {waiting} diners waiting. Continue normal service.")
        else:
            shortage = waiting - remaining_food
            fair_share = max(1, remaining_food // waiting) if waiting else 0
            st.error(f"Potential shortage: **{shortage} meals** after existing prepared food is served.")
            st.markdown(f"1. Announce the situation and use a token/queue system.  \\n+2. Serve the {remaining_food} remaining meals fairly (temporary target: {fair_share} meal-equivalent per waiting diner).  \\n+3. Start the pre-approved fast-cook reserve for **{shortage} meals**; notify the kitchen manager and nearby campus kitchens.  \\n+4. Record unmet demand—tomorrow's prediction gets a higher buffer.")
            st.session_state.shortage_log.insert(0, {"time": dt.datetime.now().strftime("%H:%M"), "shortage": shortage, "actual": actual, "planned": planned})
            log(f"Shortage response activated: {shortage} extra meals requested")


def render_safety_and_listing():
    st.subheader("2. Safe Surplus Listing & Matching")
    st.caption("Food is listed only after the kitchen confirms its condition. Follow your institution's food-safety policy and local rules.")
    with st.form("surplus_form", clear_on_submit=True):
        c1, c2 = st.columns(2)
        with c1:
            dish = st.text_input("Food item", placeholder="e.g., Veg pulao and dal")
            portions = st.number_input("Available portions", 1, 1000, 25)
            location = st.selectbox("Pickup location", ["NIST Central Cafeteria", "NIST Hostel Mess 1", "Campus event venue"])
            cooked_at = st.time_input("Cooking completed at", value=(dt.datetime.now() - dt.timedelta(hours=1)).time().replace(second=0, microsecond=0))
        with c2:
            covered = st.checkbox("Food is in clean, covered containers")
            temp_checked = st.checkbox("Kitchen staff checked the food temperature")
            allergens = st.text_input("Allergen information", placeholder="e.g., dairy, nuts; or 'none known'")
            radius = st.slider("Dispatch radius (km)", 1, 15, 5)
        submit = st.form_submit_button("Verify safety and create listing", type="primary", use_container_width=True)
    if submit:
        if not dish.strip():
            st.error("Please name the food item.")
            return
        safe, reasons, age = food_is_safe(cooked_at, covered, temp_checked, allergens)
        if not safe:
            st.error("Listing paused: " + "; ".join(reasons))
            return
        safe_hours = round(MAX_SAFE_HOLDING_HOURS - age, 1)
        item = add_donation(dish.strip(), portions, location, safe_hours, allergens.strip(), radius)
        st.success(f"Verified listing created. It has about {safe_hours} safe hours remaining in this app's workflow.")
        if item["allocations"]:
            st.markdown("**Recommended allocation (need + capacity + distance):**")
            st.dataframe(pd.DataFrame(item["allocations"]), use_container_width=True, hide_index=True)
        if item["unassigned"]:
            st.warning(f"{item['unassigned']} portions remain unassigned. Use the community fallback plan below after NGO confirmation.")
        elif not item["allocations"]:
            st.warning("No available NGO is in the selected radius. Create a supervised community distribution plan below.")


def render_dispatch():
    st.subheader("3. NGO Dispatch, Fair Allocation & Community Fallback")
    radius = st.slider("View partner NGOs within (km)", 1, 15, 5, key="dispatch_radius")
    ranked = rank_ngos(radius)
    if ranked:
        st.markdown("**Who receives food when five NGOs are available?** The app prioritises verified NGOs with the highest current need, enough pickup capacity, and a shorter pickup distance. It splits a large listing across them instead of sending everything to one organisation.")
        view = pd.DataFrame(ranked)[["name", "distance", "capacity", "need", "score", "phone"]]
        view.columns = ["NGO", "Distance (km)", "Free capacity", "Need score", "Match score", "Status"]
        st.dataframe(view, use_container_width=True, hide_index=True)
    else:
        st.warning("No available verified NGO is currently within this radius.")

    st.markdown("#### Active food listings")
    if not st.session_state.donations:
        st.info("No surplus food has been listed yet.")
    for item in st.session_state.donations:
        with st.container(border=True):
            a, b = st.columns([3, 1])
            a.markdown(f"**#{item['id']} · {item['dish']}** — {item['portions']} portions")
            a.caption(f"{item['location']} · {item['safe_hours']} safe hours left · Allergens: {item['allergens']} · {item['status']}")
            if item["allocations"]:
                a.write("Allocation: " + " · ".join(f"{x['ngo']}: {x['portions']}" for x in item["allocations"]))
            if item["status"] == "Awaiting NGO confirmation":
                if b.button("Confirm handover", key=f"confirm_{item['id']}"):
                    item["status"] = "NGO pickup confirmed"
                    st.session_state.rescued += item["portions"] - item["unassigned"]
                    log(f"NGO handover confirmed for listing #{item['id']}")
                    st.rerun()
            else:
                b.success(item["status"])

    st.divider()
    st.markdown("#### 🏘️ No NGO available? Supervised community fallback")
    st.caption("Do not go door-to-door alone. Use verified volunteers, a public pickup point, consent, a queue, and a named supervisor. Never distribute food that failed safety checks.")
    with st.form("community_form"):
        source = st.selectbox("Food listing for fallback", [f"#{d['id']} — {d['dish']} ({d['unassigned'] or d['portions']} portions)" for d in st.session_state.donations] or ["No active listing"])
        zones = st.multiselect("Neighbourhood/pickup zones", ["Campus gate pickup point", "Ward 1 community centre", "Ward 2 community centre", "Night shelter partner"], default=["Campus gate pickup point"])
        volunteers = st.number_input("Verified adult volunteers", 0, 20, 2)
        supervisor = st.text_input("Named supervisor / authorised partner")
        create_route = st.form_submit_button("Create supervised distribution plan")
    if create_route:
        if source == "No active listing" or not zones or volunteers < 2 or not supervisor.strip():
            st.error("Choose a listing and zone, assign at least two verified adult volunteers, and name an authorised supervisor.")
        else:
            st.session_state.community_deliveries.insert(0, {"listing": source, "zones": ", ".join(zones), "volunteers": volunteers, "supervisor": supervisor, "status": "Ready for supervisor approval"})
            log("Created supervised community fallback plan")
            st.success("Community plan created. Supervisor must approve it before distribution.")
    if st.session_state.community_deliveries:
        st.dataframe(pd.DataFrame(st.session_state.community_deliveries), use_container_width=True, hide_index=True)


def render_dashboard():
    kg = st.session_state.rescued * KG_PER_MEAL
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Meals safely handed over", st.session_state.rescued)
    c2.metric("Waste prevented", f"{kg:.1f} kg")
    c3.metric("Estimated CO₂ avoided", f"{kg * 2.5:.1f} kg")
    c4.metric("Open surplus listings", sum(x["status"] != "NGO pickup confirmed" for x in st.session_state.donations))
    if st.session_state.audit_log:
        with st.expander("Audit trail"):
            st.dataframe(pd.DataFrame(st.session_state.audit_log), use_container_width=True, hide_index=True)


init_state()
render_header()
render_dashboard()
tabs = st.tabs(["📊 Demand & shortage", "🛡️ Safe surplus", "🤝 Dispatch & fallback"])
with tabs[0]:
    render_planner()
with tabs[1]:
    render_safety_and_listing()
with tabs[2]:
    render_dispatch()

