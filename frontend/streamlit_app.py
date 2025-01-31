import streamlit as st
import requests

# FastAPI Backend URL
BASE_URL = "http://127.0.0.1:8000"

st.title("Assignment 1 - Team 6")

# Create a dropdown menu to choose the service
service = st.selectbox("Choose the service to use:", ["Select a service", "Open Source", "Enterprise"])

if service in ["Open Source","Enterprise"]:
    tab1, tab2 = st.tabs(["Process PDF", "Scrape Website"])

    with tab1:
        st.header("Process PDF")
        st.write(f"You are using the {service} service for PDF processing.")
        st.subheader("Process a PDF")

        # File uploader
        uploaded_file = st.file_uploader("Choose a PDF file", type="pdf")

        if uploaded_file:  # Ensure file is provided
            st.write("Processing your PDF...")
    
            # Prepare the file for API request
            files = {"file": uploaded_file.getvalue()}

            status_code = 0
            if service =="Open Source":
                response = requests.post(f"{BASE_URL}/process-pdf/", files=files)
                status_code = response.status_code
            else:
                response = requests.post(f"{BASE_URL}/process-pdf/eneterprise", files=files)
                status_code = response.status_code
    
    
            if status_code == 200:
                data = response.json()
                st.success("PDF processed successfully!")
                st.code(f"Markdown File Path: {data['markdown_s3_url']}", language="bash")
                if "image_s3_urls" in data:
                    st.code(f"Images Directory: {data['image_s3_urls']}", language="bash")
            else:
                st.error(f"Failed to process PDF! Error: {response.text}")
    
    with tab2:
        st.header("Scrape Web")
        urls = st.text_area("Enter URLs (one per line)")


        if st.button("Scrape"):
            url_list = urls.strip().split("\n")
            if url_list:
                st.write("Scraping URLs...")
                status_code = 0
                if service == "Open Source":
                    response = requests.post(f"{BASE_URL}/scrape-web/", json = {"urls":url_list})
                    status_code = response.status_code
                else:
                    response = requests.post(f"{BASE_URL}/scrape-web/enterprise", json = {"urls":url_list})
                    status_code = response.status_code

                if status_code==200:
                    results = response.json()["markdown_results"]

                    for url,result in results.items():
                        st.subheader(url)
                        st.success("Markdown file generated!")
                        st.code(f"File path: {result['markdown_s3_url']}",language="bash")
                        
                else:
                    st.error("Failed to scrape URLs!")
            else:
                st.warning("Please enter at least one URL.")

elif service == "Select a service":
    st.info("Please select a service to continue.")
