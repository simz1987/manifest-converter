import streamlit as st
import pdfplumber
import pandas as pd
import re
import io

# Set up the webpage title and description
st.title("🚚 APC Manifest Converter")
st.write("Upload your PDF driver manifest below to instantly convert it into a formatted Excel file.")

# Create a drag-and-drop file uploader
uploaded_file = st.file_uploader("Choose a PDF file", type="pdf")

if uploaded_file is not None:
    with st.spinner('Processing your manifest...'):
        extracted_data = []
        collection_date = ""
        
        try:
            # Read the uploaded PDF
            with pdfplumber.open(uploaded_file) as pdf:
                full_text = ""
                for page in pdf.pages:
                    text = page.extract_text()
                    if text:
                        full_text += text + "\n"
                
                # Find Collection Date
                date_match = re.search(r"Collection Date:\s*(\d{2}/\d{2}/\d{4})", full_text)
                if date_match:
                    raw_date = pd.to_datetime(date_match.group(1), format="%d/%m/%Y")
                    collection_date = raw_date.strftime("%d-%b")

                # Split text by parcel numbers
                parts = re.split(r'(000\d{4})', full_text)
                
                for i in range(1, len(parts)-1, 2):
                    parcel_number = parts[i][3:] 
                    block = parts[i+1] 
                    
                    weight = ""
                    weight_match = re.search(r"Weight:\s*([\d\.]+)", block)
                    if weight_match: weight = str(int(float(weight_match.group(1))))
                        
                    service = ""
                    service_match = re.search(r"SL:\s*(\d+\s*Parcel)", block)
                    if service_match: service = service_match.group(1)
                        
                    postcode = ""
                    pc_match = re.search(r"([A-Z]{1,2}\d[A-Z\d]?\s+\d[A-Z]{2})", block, re.IGNORECASE)
                    if pc_match: postcode = pc_match.group(1).replace('\n', '').strip()
                        
                    destination = ""
                    dest_match = re.search(r'^\s*([\s\S]*?)(?=Weight:)', block)
                    if dest_match: destination = dest_match.group(1).replace('\n', ' ').strip()

                    extracted_data.append([collection_date, parcel_number, service, destination, "1", weight, postcode])

            if extracted_data:
                columns = ["Collection Date", "Parcel Number", "Service", "Delivery Destination", "Number of Parcels", "Weight Booked", "Postcode"]
                df = pd.DataFrame(extracted_data, columns=columns)
                
                st.success("Manifest processed successfully!")
                
                # Show a preview of the data on the webpage
                st.dataframe(df)
                
                # Convert the data to an Excel file in the background
                output = io.BytesIO()
                with pd.ExcelWriter(output, engine='openpyxl') as writer:
                    df.to_excel(writer, index=False)
                output.seek(0)
                
                # Create the download button
                st.download_button(
                    label="📥 Download Excel File",
                    data=output,
                    file_name="converted_manifest.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
            else:
                st.error("Could not find any valid parcel data in this PDF.")
                
        except Exception as e:
            st.error(f"An error occurred: {e}")