import streamlit as st
import xmlrpc.client
import pandas as pd

# =============== APP CONFIG ===============
st.set_page_config(
    page_title="Odoo Price & Branch Tool (API Key)",
    layout="wide"
)

st.title("Odoo Price & Branch Tool (API Key)")
st.caption("Models se price update, sirf jab price different ho, API key ke through.")


# =============== ODOO HELPER FUNCTIONS ===============
def get_odoo_models(url, db, username, api_key):
    """
    Odoo XML-RPC (API key as password) se connect karega.
    """
    base = url.rstrip("/")
    common = xmlrpc.client.ServerProxy(f"{base}/xmlrpc/2/common")
    uid = common.authenticate(db, username, api_key, {})
    if not uid:
        raise Exception("Auth failed: DB / email / API key check karo.")
    models = xmlrpc.client.ServerProxy(f"{base}/xmlrpc/2/object")
    return uid, models


def get_branches(models, db, uid, api_key, branch_model):
    """
    Branch master list read karega (name field ke saath).
    """
    branch_ids = models.execute_kw(
        db, uid, api_key,
        branch_model, "search",
        [[]]
    )
    if not branch_ids:
        return []
    branches = models.execute_kw(
        db, uid, api_key,
        branch_model, "read",
        [branch_ids, ["name"]]
    )
    return branches


# =============== SIDEBAR: ODOO CONNECTION ===============
st.sidebar.header("Odoo Connection (API key)")

odoo_url = st.sidebar.text_input("Odoo URL", "https://odooprosys-la-rouche.odoo.com")
db = st.sidebar.text_input("Database")
username = st.sidebar.text_input("Login Email")
api_key = st.sidebar.text_input("API Key", type="password")

st.sidebar.markdown("---")
st.sidebar.header("Technical Settings")

product_model = st.sidebar.text_input("Product model", "product.product")
branch_model = st.sidebar.text_input("Branch model", "x_branch")  # ex: x_branch / res.branch
branch_field = st.sidebar.text_input("Branch field on product", "x_branch_id")
price_field = st.sidebar.text_input("Price field", "list_price")

connect_btn = st.sidebar.button("Connect to Odoo (API key)")

if "odoo_connected" not in st.session_state:
    st.session_state.odoo_connected = False
    st.session_state.uid = None
    st.session_state.models = None
    st.session_state.branches = []


if connect_btn:
    if not (odoo_url and db and username and api_key):
        st.sidebar.error("Saare connection fields fill karo.")
    else:
        try:
            uid, models = get_odoo_models(odoo_url, db, username, api_key)
            branches = get_branches(models, db, uid, api_key, branch_model)

            st.session_state.odoo_connected = True
            st.session_state.uid = uid
            st.session_state.models = models
            st.session_state.branches = branches

            st.sidebar.success(f"Connected (uid: {uid})")
        except Exception as e:
            st.session_state.odoo_connected = False
            st.sidebar.error(f"Connect error: {e}")


# =============== MAIN UI ===============
if not st.session_state.odoo_connected:
    st.info("Pehle left sidebar se Odoo (API key) se connect karo.")
else:
    models_proxy = st.session_state.models
    uid = st.session_state.uid

    st.subheader("Step 1 – Branch, Models aur Target Price do")

    # ---- BRANCH SELECT ----
    branch_options = {b["name"]: b["id"] for b in st.session_state.branches}
    if not branch_options:
        st.error("Koi branch nahi mili. Sidebar me Branch model ka naam sahi karo.")
    else:
        branch_name = st.selectbox("Branch select karo", list(branch_options.keys()))
        branch_id = branch_options[branch_name]

        # ---- MODELS & TARGET PRICE ----
        col1, col2 = st.columns([2, 1])

        with col1:
            model_codes_text = st.text_area(
                "Models list (har line me ek code)",
                height=220,
                placeholder="WW431\nWW466\nXP6008\n..."
            )

        with col2:
            target_price = st.number_input(
                "Target sale price",
                min_value=0.0,
                value=0.0,
                step=0.5,
                help="Jo price tum set karna chahte ho (list_price)."
            )
            st.write("")
            st.write("")
            preview_btn = st.button("Preview products")

        # ---------- PREVIEW ----------
        if preview_btn:
            if not model_codes_text.strip():
                st.error("Models list daalo.")
            elif target_price <= 0:
                st.error("Target price 0 se bada hona chahiye.")
            else:
                raw_lines = model_codes_text.splitlines()
                model_codes = [l.strip() for l in raw_lines if l.strip()]

                st.write(f"Total models entered: **{len(model_codes)}**")

                try:
                    # Products search by default_code
                    domain = [("default_code", "in", model_codes)]
                    product_ids = models_proxy.execute_kw(
                        db, uid, api_key,
                        product_model, "search",
                        [domain]
                    )

                    if not product_ids:
                        st.warning("In models ke liye koi product nahi mila.")
                    else:
                        products = models_proxy.execute_kw(
                            db, uid, api_key,
                            product_model, "read",
                            [product_ids, ["default_code", "name",
                                           price_field, branch_field]]
                        )

                        preview_rows = []
                        will_update_ids = []
                        skip_same_price = 0
                        skip_other_branch = 0

                        for prod in products:
                            code = prod.get("default_code")
                            name = prod.get("name")
                            current_price = prod.get(price_field)
                            prod_branch = prod.get(branch_field)

                            # Branch field handling (many2one)
                            prod_branch_id = None
                            prod_branch_name = ""
                            if isinstance(prod_branch, list) and prod_branch:
                                prod_branch_id = prod_branch[0]
                                prod_branch_name = prod_branch[1]
                            elif isinstance(prod_branch, int):
                                prod_branch_id = prod_branch

                            # Branch check:
                            # - agar product ki branch set hai aur selected branch se alag hai -> skip
                            if prod_branch_id and prod_branch_id != branch_id:
                                status = "SKIP (other branch)"
                                skip_other_branch += 1
                            else:
                                # Price check:
                                # agar current_price already target_price hai -> skip
                                if current_price == target_price:
                                    status = "SKIP (same price)"
                                    skip_same_price += 1
                                else:
                                    status = "UPDATE"
                                    will_update_ids.append(prod["id"])

                            preview_rows.append({
                                "Model": code,
                                "Name": name,
                                "Current Branch": prod_branch_name or "",
                                "Current Price": current_price,
                                "Target Price": target_price,
                                "Status": status
                            })

                        df = pd.DataFrame(preview_rows)
                        st.markdown("### Preview")
                        st.dataframe(df, use_container_width=True)

                        st.info(
                            f"UPDATE: {df['Status'].eq('UPDATE').sum()}  |  "
                            f"SKIP (same price): {skip_same_price}  |  "
                            f"SKIP (other branch): {skip_other_branch}"
                        )

                        # ---------- APPLY ----------
                        if will_update_ids:
                            st.markdown("---")
                            st.subheader("Step 2 – Confirm and apply to Odoo")

                            apply_btn = st.button(
                                f"Apply changes to {len(will_update_ids)} products"
                            )

                            if apply_btn:
                                updated = 0
                                errors = 0
                                for pid in will_update_ids:
                                    values = {
                                        price_field: target_price,
                                        branch_field: branch_id
                                    }
                                    try:
                                        models_proxy.execute_kw(
                                            db, uid, api_key,
                                            product_model, "write",
                                            [[pid], values]
                                        )
                                        updated += 1
                                    except Exception:
                                        errors += 1

                                st.success(f"Successfully updated {updated} products.")
                                if errors:
                                    st.error(f"{errors} products update nahi ho paye (error).")

                except Exception as e:
                    st.error(f"Odoo read/write error: {e}")
