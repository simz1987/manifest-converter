import streamlit as st
import pandas as pd
from pypdf import PdfReader
import re
from datetime import datetime

st.set_page_config(page_title="APC Manifest Batcher", layout="wide")

st.title("🚛 APC Weekly Manifest Batcher")
st.write("Upload multiple PDFs to generate a combined weekly summary.")

uploaded_files = st.file_uploader("Upload APC Manifest PDFs", type="pdf", accept_multiple_files=True)

if uploaded_files:
    master_list = []
    
    # Month mapping for the "05-Mar" format
    months = {
        "01": "Jan", "02": "Feb", "03": "Mar", "04": "Apr", "05": "May", "06": "Jun",
        "07": "Jul", "08": "Aug", "09": "Sep", "10": "Oct", "11": "Nov", "12": "Dec"
    }
    
    for uploaded_file in uploaded_files:
        try:
            reader = PdfReader(uploaded_file)
            full_text = ""
            for page in reader.pages:
                full_text += page.extract_text() + "\n"
            
            lines = [l.strip() for l in full_text.split('\n') if l.strip()]
            
            # --- 1. GET THE COLLECTION DATE (05-Mar Format) ---
            file_date = ""
            for i, line in enumerate(lines):
                if "Collection Date:" in line and i+1 < len(lines):
                    date_match = re.search(r'(\d{2})/(\d{2})', lines[i+1])
                    if date_match:
                        day = date_match.group(1)
                        month_num = date_match.group(2)
                        file_date = f"{day}-{months.get(month_num, month_num)}"
                    break

            # --- 2. EXTRACT EACH DELIVERY BLOCK ---
            for i, line in enumerate(lines):
                # Trigger on 7-digit consignment number starting with 000
                if re.fullmatch(r'000\d{4}', line):
                    # Strip leading zeros for the display (0004827 -> 4827)
                    cons_num = str(int(line))
                    dest = lines[i+1] if i+1 < len(lines) else ""
                    
                    service, weight, qty, postcode = "", "", "", ""
                    
                    for j in range(i+1, i+15):
                        if j >= len(lines): break
                        l = lines[j]
                        
                        # Service Code (SL: XXXX) + " parcel"
                        if "SL:" in l:
                            s_match = re.search(r'SL:\s*(\d+)', l)
                            if s_match: service = f"{s_match.group(1)} parcel"
                        
                        # Weight
                        if "Weight:" in l:
                            w_match = re.search(r'Weight:\s*([\d\.]+)', l)
                            if w_match: weight = w_match.group(1)
                        
                        # Postcode
                        pc_match = re.search(r'[A-Z]{1,2}[0-9][A-Z0-9]? [0-9][A-Z]{2}', l.upper())
                        if pc_match: postcode = pc_match.group()
                        
                        # Parcel Qty
                        if l in ["1", "2", "3", "4", "5"] and ("Phone:" in lines[j-1] or "QTY" in lines[j-5]):
                            qty = l

                    master_list.append({
                        "Collection Date": file_date,
                        "Consignment Number": cons_num,
                        "Service": service,
                        "Delivery Destination": dest,
                        "Parcels": qty,
                        "Weight": weight,
                        "Postcode": postcode
                    })
                    
        except Exception as e:
            st.error(f"Error reading {uploaded_file.name}: {e}")

    if master_list:
        df = pd.DataFrame(master_list)
        df = df.drop_duplicates(subset=["Consignment Number"])

        st.success(f"✅ Extracted {len(df)} deliveries.")
        
        # Display the table
        st.dataframe(df, use_container_width=True, hide_index=True)

        # Download
        csv = df.to_csv(index=False).encode('utf-8')
        st.download_button("📥 Download Weekly Summary CSV", csv, "Weekly_APC_Summary.csv", "text/csv")
