import streamlit as st
import pandas as pd
from pypdf import PdfReader
import re

st.set_page_config(page_title="APC Manifest Batcher", layout="wide")

st.title("🚛 APC Manifest Batch Converter")
st.write("Upload multiple APC PDFs to combine into one master table with Date and Postcode.")

uploaded_files = st.file_uploader("Upload APC Manifest PDFs", type="pdf", accept_multiple_files=True)

if uploaded_files:
    all_data = []
    
    for uploaded_file in uploaded_files:
        try:
            reader = PdfReader(uploaded_file)
            full_text = ""
            for page in reader.pages:
                full_text += page.extract_text() + "\n"
            
            lines = [line.strip() for line in full_text.split('\n') if line.strip()]
            
            # 1. Grab the Collection Date (usually near the top)
            collection_date = "Unknown"
            for i, line in enumerate(lines):
                if "Collection Date:" in line:
                    if i + 1 < len(lines):
                        collection_date = lines[i+1]
                    break
            
            # 2. Scan for Consignments and Postcodes
            for i, line in enumerate(lines):
                # Look for the 7-digit consignment number starting with 000
                if len(line) == 7 and line.startswith("000") and line.isdigit():
                    cons_num = line
                    customer = lines[i+1] if i+1 < len(lines) else "Unknown"
                    
                    # Look ahead for the Postcode (Pattern: Letters + Numbers + Space + Number + Letters)
                    postcode = ""
                    # We check the next 8 lines for a postcode pattern
                    for j in range(i+1, i+10):
                        if j < len(lines):
                            # Regex to find UK Postcode format
                            found = re.search(r'[A-Z]{1,2}[0-9R][0-9A-Z]? [0-9][A-Z]{2}', lines[j].upper())
                            if found:
                                postcode = found.group()
                                break
                    
                    all_data.append({
                        "Collection Date": collection_date,
                        "Consignment": cons_num,
                        "Customer": customer,
                        "Postcode": postcode
                    })
                    
        except Exception as e:
            st.error(f"Error reading {uploaded_file.name}: {e}")

    if all_data:
        df = pd.DataFrame(all_data)
        
        # Remove duplicates based on consignment number
        df = df.drop_duplicates(subset=["Consignment"])
        
        # Sort by Date so the week is in order
        df = df.sort_values(by="Collection Date")

        st.success(f"✅ Processed {len(uploaded_files)} manifests.")
        st.dataframe(df, use_container_width=True)

        # Download CSV
        csv = df.to_csv(index=False).encode('utf-8')
        st.download_button("📥 Download Master Weekly CSV", csv, "Weekly_APC_Summary.csv", "text/csv")
