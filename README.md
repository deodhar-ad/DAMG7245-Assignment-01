# PDF and Web Page Markdown Content Extraction Using Open Source and Enterprise Services

## Team Members -
- Aditi Ashutosh Deodhar 002279575
- Lenin Kumar Gorle 002803806
- Poorvika Girish Babu 002801388

## Project Overview

### Problem Statement
Businesses and startups frequently need to process data from unstructured sources like PDFs and web pages, which often contain embedded images, tables, and charts. Extracting and organizing this data properly is a complex task.

### Scope
- Processed output is stored in S3 storage in different folders based on the file extension.
- Metadata tags are used to enhance searchability and access control.

## Methodology
- Compare open-source libraries with enterprise solutions for text and element extraction.
- Develop a methodology to structure extracted data using Markdown.
- Organize the extracted files in AWS S3 with metadata for efficient retrieval.
- Provide an API and frontend interface for seamless interaction with the system.

## Technologies Used

### Backend
- Python
- FastAPI

### Frontend
- Streamlit

### Cloud
- AWS

## Architecture Diagram

![Architecture Diagram for Assignment 1](https://github.com/user-attachments/assets/929236dc-a59d-4c06-9cf6-ddd8281c276c)

## Codelabs Documentation
https://docs.google.com/document/d/1gZOaXw5JYJq11axuy83FqQkATYDIr7m_uveodCyMwh4/edit?usp=sharing

## Hosted Applications links 
- FastAPI on Render - https://fastapi-service-568242136794.us-east1.run.app/docs
- Streamlit on Streamlit Cloud - https://damg7245-assignment-01-ntxhwzwqbxd3rsghktxg6m.streamlit.app/

## Demo -
-  https://shorturl.at/DOsAK

## Prerequisites
- Python 3.9+
- AWS Account
- Adobe Account
- Apify Account

## Set Up the Environment
```
   # clone the environment
     https://github.com/deodhar-ad/DAMG7245-Assignment-01.git
     cd DAMG7245-Assignment-01
   # add all the environmental variables in .env file
```

## Project Structure
```
DAMG7245-Assignment-01/
├─ api/             # Fast API
├─ backend/         # Backend methods for open-source and enterprise
├─ frontend/        # Streamlit 
├─ storage/         # AWS S3 code  
└─ vercel.json      # vercel configurations
 ```  


