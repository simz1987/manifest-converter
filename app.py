import streamlit as st
import pandas as pd
from pypdf import PdfReader
import io

st.set_page_config(page_title="APC Manifest Batcher", layout="wide")

st.title("🚛 APC Manifest Batch Converter")
st.write("Upload your weekly APC Driver Manifests here to combine them into one table.")

# This allows you to select multiple PDFs at once
uploaded_files = st.file_uploader("Upload APC Manifest PDFs", type="pdf", accept_multiple_files=True)

if uploaded_files:
    all_data = []
    
    for uploaded_file in uploaded_files:
        try:
            reader = PdfReader(uploaded_file)
            
            for page in reader.pages:
                text = page.extract_text()
                # We split by lines, but also look for specific APC patterns
                lines = text.split('\n')
                
                for i, line in enumerate(lines):
                    # APC Consignments are 7 digits starting with 000
                    if "000" in line and any(char.isdigit() for char in line):
                        parts = line.split()
                        
                        # Find the actual 7-digit number in the parts
                        cons_num = next((p for p in parts if len(p) == 7 and p.startswith("000")), None)
                        
                        if cons_num:
                            # Usually the Name is either in the same line or the line right after
                            # Based on your PDF, it's often the line immediately following the number
                            customer_name = "Unknown"
                            if i + 1 < len(lines):
                                customer_name = lines[i+1].strip()
                            
                            # Grab the next few lines for address/postcode
                            address_block = []
                            for j in range(i+2, i+6):
                                if j < len(lines):
                                    # Stop if we hit the next consignment or "Weight:"
                                    if "000" in lines[j] or "Weight:" in lines[j]:
                                        break
                                    address_block.append(lines[j].strip())
                            
                            full_address = ", ".join(address_block)
                            
                            all_data.append({
                                "Consignment": cons_num,
                                "Customer": customer_name,
                                "Address/Postcode": full_address
                            })
        except Exception as e:
            st.error(f"Error reading {uploaded_file.name}: {e}")

    if all_data:
        df = pd.DataFrame(all_data)
        
        # Clean up: Remove any row that is just "Special Instructions" or "Weight"
        df = df[~df['Customer'].str.contains("Special Instructions|Weight", na=False)]
        df = df.drop_duplicates(subset=["Consignment"])

        st.success(f"✅ Combined {len(uploaded_files)} manifests into one master list.")
        st.dataframe(df, use_container_width=True)

        # Download button
        csv = df.to_csv(index=False).encode('utf-8')
        st.download_button("📥 Download Weekly Master CSV", csv, "Weekly_APC_Manifest.csv", "text/csv")
    else:
        st.warning("Could not find any consignments. Please ensure the PDF is a standard APC Driver Manifest.")
