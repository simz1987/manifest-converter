import streamlit as st
import pandas as pd
from pypdf import PdfReader
import io

st.set_page_config(page_title="Manifest Converter", layout="wide")

st.title("🚛 Manifest Batch Converter")
st.write("Upload multiple PDFs to combine them into one Excel-ready table.")

# Allow multiple files
uploaded_files = st.file_uploader("Upload Manifest PDFs", type="pdf", accept_multiple_files=True)

if uploaded_files:
    all_data = []
    
    for uploaded_file in uploaded_files:
        try:
            reader = PdfReader(uploaded_file)
            
            # Logic to grab the data exactly like your original version
            for page in reader.pages:
                text = page.extract_text()
                lines = text.split('\n')
                
                # Using the original 'Label' scanning logic
                # This assumes your PDF has "Delivered To:" and "Town:" etc.
                current_cust = ""
                current_town = ""
                current_date = ""
                
                for line in lines:
                    if "Delivered To:" in line:
                        current_cust = line.split("Delivered To:")[-1].strip()
                    if "Town:" in line:
                        current_town = line.split("Town:")[-1].strip()
                    if "Date:" in line:
                        current_date = line.split("Date:")[-1].strip()
                    
                    # When a row marker is found (like a Delivery Note or a Carrier ID)
                    # it adds the row to our master list
                    if "CARR_ID" in line or "T_ID" in line:
                        # Split the line based on how your original report was formatted
                        parts = line.split() 
                        all_data.append({
                            "Date": current_date,
                            "Customer": current_cust,
                            "Town": current_town,
                            "CARR_ID": parts[0] if len(parts) > 0 else "",
                            "T_ID": parts[1] if len(parts) > 1 else "",
                            "S_ID": parts[2] if len(parts) > 2 else ""
                        })
        except Exception as e:
            st.error(f"Error processing {uploaded_file.name}: {e}")

    if all_data:
        df = pd.DataFrame(all_data)
        
        # Clean up duplicates
        df = df.drop_duplicates()

        st.success(f"✅ Combined {len(uploaded_files)} files into one list.")
        st.dataframe(df, use_container_width=True)

        # Excel/CSV Download
        csv = df.to_csv(index=False).encode('utf-8')
        st.download_button("📥 Download Master CSV", csv, "Combined_Manifests.csv", "text/csv")
