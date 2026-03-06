import streamlit as st
import pandas as pd
from pypdf import PdfReader
import io

st.set_page_config(page_title="Weekly Manifest Batcher", layout="wide")

# (Optional: Insert your check_password() logic here if you want it protected)

st.title("🚛 Weekly Manifest Batcher")
st.write("Drag and drop multiple PDFs here to process a whole week at once.")

# ==========================================
# 🛑 YOUR CARRIER MAPPING 🛑
# ==========================================
CARRIER_MAPPING = {
    "WAITROSE": {"CARR_ID": "WTR001", "T_ID": "TRANSIT_A"},
    "MATRIX": {"CARR_ID": "MTX005", "T_ID": "TRANSIT_B"},
    # ... add your full list here ...
}

# accept_multiple_files=True is the magic switch here
uploaded_files = st.file_uploader("Upload Manifest PDFs", type="pdf", accept_multiple_files=True)

if uploaded_files:
    master_data = []
    
    for uploaded_file in uploaded_files:
        try:
            reader = PdfReader(uploaded_file)
            file_text = ""
            for page in reader.pages:
                file_text += page.extract_text() + "\n"
            
            # --- SCANNER LOGIC ---
            # This part looks for your specific keywords in the PDF text
            # We'll look for "Customer:" and "Town:" as an example
            lines = file_text.split('\n')
            for line in lines:
                # We search the lines for your specific customer names
                for trigger_word in CARRIER_MAPPING.keys():
                    if trigger_word.upper() in line.upper():
                        mapping = CARRIER_MAPPING[trigger_word]
                        master_data.append({
                            "Source File": uploaded_file.name,
                            "Detected Customer": trigger_word,
                            "CARR_ID": mapping["CARR_ID"],
                            "T_ID": mapping["T_ID"]
                        })
                        break # Move to next line once found
        except Exception as e:
            st.error(f"Error reading {uploaded_file.name}: {e}")

    if master_data:
        df = pd.DataFrame(master_data)
        
        # Remove exact duplicates (e.g., if the same customer is on 3 pages of 1 PDF)
        df = df.drop_duplicates(subset=["Detected Customer", "CARR_ID", "T_ID"])

        st.success(f"✅ Processed {len(uploaded_files)} files and found {len(df)} unique deliveries.")
        
        # Display the results
        st.subheader("📋 Weekly Carrier Master List")
        st.dataframe(df, use_container_width=True)

        # ✨ THE DOWNLOAD BUTTON
        csv = df.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Download Master Weekly CSV",
            data=csv,
            file_name="Weekly_Manifest_Summary.csv",
            mime="text/csv",
        )
    else:
        st.warning("Processed the files but couldn't find any matching customers from your mapping list.")
