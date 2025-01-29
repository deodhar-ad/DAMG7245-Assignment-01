import streamlit as st
import requests

# FastAPI Backend URL
BASE_URL = "http://127.0.0.1:8000"

st.title("Assignment 1 - Team 6")

# Tabbed interface for PDFs and URLs
tab1, tab2 = st.tabs(["Process PDF", "Scrape Web"])

# Process PDF Tab
with tab1:
    st.header("Upload a PDF")
    uploaded_file = st.file_uploader("Choose a PDF file", type="pdf")
    if uploaded_file:
        st.write("Processing your PDF...")
        files = {"file": uploaded_file.getvalue()}
        response = requests.post(f"{BASE_URL}/process-pdf/", files=files)
        if response.status_code == 200:
            data = response.json()
            st.success("PDF processed successfully!")
            st.code(f"Markdown File Path: {data['markdown_s3_url']}", language="bash")
            if "images_dir" in data:
                st.code(f"Images Directory: {data['image_s3_urls']}", language="bash")
        else:
            # Display error message if API failed
            st.error("Failed to process PDF! Please check your input and try again.")

# Scrape Web Tab
with tab2:
    st.header("Scrape Webpages")
    urls = st.text_area("Enter URLs (one per line)")
    if st.button("Scrape"):
        url_list = urls.strip().split("\n")
        if url_list:
            st.write("Scraping URLs...")
            response = requests.post(f"{BASE_URL}/scrape-web/", json={"urls": url_list})
            if response.status_code == 200:
                results = response.json()["markdown_results"]
                for url, result in results.items():
                    st.subheader(url)
                    st.success("Markdown file generated!")
                    st.code(f"File path: {result['markdown_s3_url']}", language="bash")  # Display the file path
            else:
                st.error("Failed to scrape URLs!")
