import streamlit as st

# ================== BASIC APP CONFIG ==================
st.set_page_config(
    page_title="Odoo Product Branch & Price Manager",
    layout="wide"
)

st.title("Odoo Product Branch & Price Manager")
st.caption("Bulk edit branches, prices and fields by model codes (external tool).")

# ================== SIDEBAR: ODOO CONNECTION ==================
st.sidebar.header("Odoo Connection")

odoo_url = st.sidebar.text_input("Odoo URL", "https://odooprosys-la-rouche.odoo.com")
db = st.sidebar.text_input("Database", "")
username = st.sidebar.text_input("Username", "")
password = st.sidebar.text_input("Password", type="password")

connect_btn = st.sidebar.button("Test Connect (not active yet)")

if connect_btn:
    # Abhi sirf dummy message, baad me yahan Odoo XML-RPC logic add karenge
    if not (odoo_url and db and username and password):
        st.sidebar.error("Please fill all connection fields.")
    else:
        st.sidebar.success("(Demo) Connection details received. Odoo logic next step me add hoga.")

st.sidebar.markdown("---")
st.sidebar.header("Global Settings")
product_model = st.sidebar.text_input("Product model", "product.product")
branch_field = st.sidebar.text_input("Branch field", "x_branch_id")
price_field = st.sidebar.text_input("Price field", "list_price")

# ================== MAIN TABS ==================
tabs = st.tabs([
    "1️⃣ Model Filter & Preview",
    "2️⃣ Bulk Update",
    "3️⃣ Logs"
])

# ---------- TAB 1: MODEL FILTER & PREVIEW ----------
with tabs[0]:
    st.subheader("Model Filter & Preview")

    st.markdown("""
    Yahan tum models ka list paste karoge.  
    Next step me hum Odoo se in models ka data laakar table me dikhayenge.
    """)

    model_codes_text = st.text_area(
        "Paste model codes (one per line or comma separated)",
        height=200,
        placeholder="Example:\nWW431\nWW466\nXP6008\n..."
    )

    col_a, col_b = st.columns([1, 2])
    with col_a:
        load_btn = st.button("Load products (preview)")

    with col_b:
        clear_btn = st.button("Clear list")

    if clear_btn:
        st.experimental_rerun()

    if load_btn:
        if not model_codes_text.strip():
            st.error("Please paste at least one model code.")
        else:
            raw_lines = model_codes_text.replace(",", "\n").splitlines()
            model_codes = [l.strip() for l in raw_lines if l.strip()]
            st.success(f"Total model codes entered: {len(model_codes)}")

            st.markdown("#### Sample Preview (Demo)")
            st.info(
                "Abhi demo preview hai. Actual Odoo se data nikalne ka code "
                "next step me add karenge."
            )

            # Sirf demo static table (structure show karne ke liye)
            import pandas as pd
            sample_rows = []
            for code in model_codes[:10]:  # sirf first 10 dikhayenge
                sample_rows.append({
                    "Model": code,
                    "Name": "(will come from Odoo)",
                    "Branch": "(from Odoo)",
                    "Price": "(from Odoo)",
                    "Status": "Pending"
                })

            df = pd.DataFrame(sample_rows)
            st.dataframe(df, use_container_width=True)

            st.markdown("You can go to **Bulk Update** tab to define rules.")

# ---------- TAB 2: BULK UPDATE ----------
with tabs[1]:
    st.subheader("Bulk Update Rules")

    st.markdown("""
    Yahan tum decide karoge ke in loaded products ke saath kya karna hai:  
    - Branch change,  
    - Price increase (value / %),  
    - Exact price set, etc.
    """)

    action_type = st.selectbox(
        "Select action",
        [
            "Change branch",
            "Increase price (value)",
            "Increase price (%)",
            "Set exact price"
        ]
    )

    col1, col2 = st.columns(2)

    with col1:
        if action_type == "Change branch":
            target_branch = st.text_input(
                "Target branch (ID or name - UI only for now)",
                ""
            )
        elif action_type == "Increase price (value)":
            inc_value = st.number_input(
                "Increase by amount",
                min_value=0.0,
                value=0.0,
                step=0.5
            )
        elif action_type == "Increase price (%)":
            inc_percent = st.number_input(
                "Increase by percent",
                min_value=0.0,
                value=0.0,
                step=1.0
            )
        elif action_type == "Set exact price":
            new_price = st.number_input(
                "New price",
                min_value=0.0,
                value=0.0,
                step=0.5
            )

    with col2:
        only_if_diff = st.checkbox(
            "Apply only if price is different from current sale price",
            value=True
        )
        st.caption("Ye tumhara 'sale price match na kare tabhi change karo' rule hai.")

        simulate_only = st.checkbox(
            "Simulation mode (no real update) – Odoo logic baad me add hoga",
            value=True
        )

    st.markdown("#### Preview (Demo)")

    st.info(
        "Yahan actual me old vs new prices ka table aayega. "
        "Filhaal sirf design bana rahe hain."
    )

    col_apply1, col_apply2 = st.columns([1, 3])
    with col_apply1:
        apply_btn = st.button("Apply changes (demo)")
    with col_apply2:
        st.caption("Real Odoo update code next step me add hoga.")

    if apply_btn:
        st.warning(
            "Demo mode: koi real Odoo update nahi ho raha. "
            "Jab Odoo client add karenge tab yeh button actual write karega."
        )

# ---------- TAB 3: LOGS ----------
with tabs[2]:
    st.subheader("Logs")

    st.markdown("""
    Yahan future me:
    - Last actions,
    - Kitne products update hue,
    - Errors (agar koi hua),  
    dikhayenge.
    Filhaal skeleton hai.
    """)

    st.info("No logs yet. Odoo integration ke baad logging add karenge.")
