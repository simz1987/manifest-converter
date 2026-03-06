import streamlit as st
import pandas as pd
from pypdf import PdfReader
import io
import re

st.set_page_config(page_title="Weekly Manifest Batcher", layout="wide")

# (Optional: Insert your check_password() logic here)

st.title("🚛 Weekly Manifest Batcher")
st.write("Upload all your PDFs for the week. The app will extract every delivery into one master table.")

uploaded_files = st.file_uploader("Upload Manifest PDFs", type="pdf", accept_multiple_files=True)

if uploaded_files:
    master_data = []
    
    with st.spinner(f"Extracting data from {len(uploaded_files)} files..."):
        for uploaded_file in uploaded_files:
            try:
                reader = PdfReader(uploaded_file)
                
                # We process page by page
                for page_num, page in enumerate(reader.pages):
                    text = page.extract_text()
                    lines = text.split('\n')
                    
                    # --- THE UNIVERSAL SCANNER ---
                    # We look for the patterns that usually identify a delivery
                    current_cust = "Unknown"
                    current_town = "Unknown"
                    
                    for line in lines:
                        # Example: Look for 'Customer:' or 'Name:' labels
                        if "Customer:" in line or "Name:" in line:
                            current_cust = line.split(':')[-1].strip()
                        
                        if "Town:" in line or "City:" in line:
                            current_town = line.split(':')[-1].strip()
                        
                        # Once we have a 'set', we add it to our list
                        # Note: You might need to adjust these keywords 
                        # based on exactly what words are on your Manifest PDF
                        if "Delivery Note:" in line:
                            master_data.append({
                                "Date/File": uploaded_file.name.replace('.pdf', ''),
                                "Customer": current_cust,
                                "Town": current_town,
                                "Ref": line.split(':')[-1].strip()
                            })
            except Exception as e:
                st.error(f"Error reading {uploaded_file.name}: {e}")

    if master_data:
        df = pd.DataFrame(master_data)
        
        # Clean up the data
        df = df.drop_duplicates()

        st.success(f"✅ Extracted {len(df)} deliveries from {len(uploaded_files)} files.")
        
        # Display the table
        st.subheader("📅 Weekly Master Schedule")
        st.dataframe(df, use_container_width=True)

        # Download button
        csv = df.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Download Weekly Master CSV",
            data=csv,
            file_name="Weekly_Manifest_Master.csv",
            mime="text/csv",
        )
    else:
        st.warning("Could not find any delivery data in those PDFs. Check that the PDFs are not 'scanned images'.")
