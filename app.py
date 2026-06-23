# app.py

import streamlit as st
from datetime import datetime  

from medication import Medication, DrugNotFoundError, APIConnectionError
from recall_checker import RecallChecker
from ai_translator import AITranslator
from search_history import SearchHistory, SearchHistoryError
from text_processor import TextProcessor

class InvalidDrugNameError(Exception):
    pass


# ---------------- PAGE CONFIG ----------------
st.set_page_config(
    page_title="Drug Information App",
    page_icon="💊",
    layout="wide"
)

st.title("💊 Drug Information & Safety Checker")
st.warning("⚠ This app is for educational purposes only. It is not medical advice.")
st.info("ℹ Always consult a doctor before using any medication.")
st.write("Search for a medication to get details, warnings, and simplified explanations.")


# ---------------- INITIALIZE CLASSES ----------------
#history = SearchHistory()
history = SearchHistory(filepath="search_history.json")
translator = AITranslator()
recall_checker = RecallChecker()


# ---------------- USER INPUT ----------------
drug_name = st.text_input("Enter medication name (e.g. ibuprofen, aspirin, tramadol)")

search_btn = st.button("Search")


# ---------------- SEARCH LOGIC ----------------
if search_btn:

    try:
        #check for empty input
        if not drug_name.strip():
            st.error("Please enter a drug name")
            st.stop()

        # Clean input
        cleaned_name = TextProcessor.clean_text(drug_name)

        # Validate input
        if not TextProcessor.validate_name(cleaned_name):
            raise InvalidDrugNameError("Invalid medication name")

        # Fetch drug info
        medication = Medication(cleaned_name)
        with st.spinner("Fetching drug information..."):
            drug_info = medication.fetch_info()


        # ---------------- DISPLAY RESULTS ----------------
        recall = None
        tab1, tab2, tab3 = st.tabs(["📄 Info", "🧠 AI", "⚠ Safety"])

        with tab1:
            st.subheader("📄 Drug Information")

            st.markdown("### Usage")
            st.write(drug_info.get("usage", "Not available"))

            st.markdown("### Warnings")
            st.write(drug_info.get("warnings", "Not available"))

            st.markdown("### Side Effects")
            st.write(drug_info.get("side_effects", "Not available"))

            st.markdown("### Instructions")
            st.write(drug_info.get("instructions", "Not available"))


        # ---------------- AI SIMPLIFICATION ----------------
        with tab2:
            st.subheader("🧠 Simplified Explanation (AI)")

            try:
                with st.spinner("AI is simplifying the information..."):
                    simplified = translator.simplify_text(str(drug_info))
                st.success(simplified)
            except Exception as e:
                simplified = "AI unavailable at the moment."
                st.warning("AI simplification failed. Showing raw info instead.")


        # ---------------- RECALL CHECK ----------------
        with tab3:
            st.subheader("⚠ Safety Check")


            recall = recall_checker.check_recall(cleaned_name)

            if recall:
                st.error("⚠ This medication appears in a recent recall notice!")

                # format date safely
                raw_date = recall.get("recall_date", "")

                try:
                    formatted_date = datetime.strptime(raw_date, "%Y%m%d").strftime("%d %b %Y")
                except:
                    formatted_date = raw_date  # fallback if format fails

                st.markdown(f"""
            ### 📦 Recall Details

            **Status:** {recall.get("status", "N/A")}  
            **Reason:** {recall.get("reason", "N/A")}  
            **Classification:** {recall.get("classification", "N/A")}  
            **Recall Date:** {formatted_date}
            """)
            else:
                st.success("No recent recall notices found.")

        # ✅ SAVE HISTORY (PUT IT HERE)
        history.add_search(
            drug_name=cleaned_name,
            summary=simplified,
            warnings=drug_info.get("warnings", []),
            recall_flag=bool(recall),
            raw_data=drug_info
        )

    except InvalidDrugNameError:
        st.error("❌ Invalid medication name format. Please use standard characters.")

    except DrugNotFoundError as e:
        st.warning(f"🔍 {str(e)}. Please check the spelling and try again.")

    except APIConnectionError as e:
        st.error(f"🌐 {str(e)}")
    
    except SearchHistoryError as e:
        st.error(f"History Logging Error: {str(e)}")

    except Exception:
        st.error("⚠ An unexpected error occurred. Please check your system configuration.")

# ---------------- SIDEBAR HISTORY ----------------
st.sidebar.title("📜 Search History")

try:
    records = history.get_all(newest_first=True)
    if records:
        for item in records[:20]:
            st.sidebar.write(f"💊 {item.get('drug_name', 'Unknown')}")
            
            raw_time = item.get("timestamp", "")
            try:
                formatted_time = datetime.fromisoformat(raw_time).strftime("%d %b %Y, %I:%M %p")
            except:
                formatted_time = raw_time
            st.sidebar.caption(f"🕒 {formatted_time}")

            if item.get("summary"):
                st.sidebar.caption("🧠 AI summary saved")

            if item.get("warnings"):
                st.sidebar.caption("⚠ Warnings available")

            if item.get("recall_flag"):
                st.sidebar.error("🚨 Recall flagged")

            st.sidebar.divider()
    else:
        st.sidebar.write("No history yet.")

except Exception as e:
    st.sidebar.write("Unable to load history.")
