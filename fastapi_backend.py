from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import List
import os
from backend.pdf_extract import process_pdf
from backend.web_scrape import scrape_and_convert

app = FastAPI()

class URLInput(BaseModel):
    urls: List[str]

# PDF Extract and convert Endpoint  
@app.post("/process-pdf/")
async def process_pdf_endpoint(file: UploadFile = File(...)):

    try:
        # Step 1: Read the uploaded file content
        file_content = await file.read()

        # Step 2: Call the process_pdf function
        result = process_pdf(file_content)

        # Step 3: Return the S3 URLs and other details
        return {
            "message": result["message"],
            "markdown_s3_url": result["markdown_s3_url"],  # S3 URL for Markdown
            "image_s3_urls": result["image_s3_urls"],      # List of S3 URLs for images
            "unique_folder": result["unique_folder"],      # Unique folder name for this processing task
            "status": result["status"]
        }

    except Exception as e:
        # Return a 500 error response in case of an exception
        return JSONResponse(content={"error": str(e)}, status_code=500)
    
# Web Scraping Endpoint    
@app.post("/scrape-web/")
async def scrape_web_endpoint(data: URLInput):
    markdown_results = {}

    try:
        for url in data.urls:
            try:
                # Call the updated scrape_and_convert function
                result = scrape_and_convert(url)

                # Collect result: Markdown and image S3 URLs
                markdown_results[url] = {
                    "markdown_s3_url": result["markdown_s3_url"],
                    "image_s3_urls": result["image_s3_urls"],
                    "unique_folder": result["unique_folder"],
                    "status": result["status"],
                    "message": result["message"]
                }
            except Exception as e:
                markdown_results[url] = {"error": str(e)}

        return {"markdown_results": markdown_results}

    except Exception as e:
        # Handle unexpected errors
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000, debug=True)from fastapi import FastAPI,File,HTTPException,UploadFile
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import List
import os
from backend.web_scrape_enterprise import scrape_and_convert_enterprise
from backend.pdf_extract_enterprise import process_pdf_enterprise
import uvicorn


app = FastAPI()

class URLInput(BaseModel):
    urls: List[str]


# PDF Extract and Convert Endpoint
@app.post("/process-pdf/enterprise")
async def process_pdf_enterprise_endpoint(file: UploadFile = File(...)):
    try:
        # Step 1: Read the uploaded file content
        file_content = await file.read()

        # Step 2: Call the process_pdf function with env credentials
        result = process_pdf_enterprise(file_content)

        # Step 3: Return the S3 URLs and other details
        return {
            "message": result["message"],
            "markdown_s3_url": result["markdown_s3_url"],  # S3 URL for Markdown
            "image_s3_urls": result["image_s3_urls"],      # List of S3 URLs for images
            "unique_folder": result["unique_folder"],      # Unique folder name for this processing task
            "status": result["status"]
        }

    except Exception as e:
        # Return a 500 error response in case of an exception
        return JSONResponse(content={"error": str(e)}, status_code=500)

# Web Scraping Enterprise Endpoint
@app.post("/scrape-web/enterprise")
async def scrape_web_enterprise_endpoint(data:URLInput):
    markdown_results = {}

    try:
        for url in data.urls:
            try:
                # Call the updated scrape_and_convert function
                result = scrape_and_convert_enterprise(url)

                # Collect result: Markdown and image S3 URLs
                markdown_results[url] = {
                    "markdown_s3_url": result["markdown_s3_url"],
                    "image_s3_urls": result["image_s3_urls"],
                    "unique_folder": result["unique_folder"],
                    "status": result["status"],
                    "message": result["message"]
                }
            
            except Exception as e:
                markdown_results[url] = {"error": str(e)}
        return {"markdown_results": markdown_results}
    
    except Exception as e:
        raise HTTPException(status_code=500,detail=f"Internal Server Error: {str(e)}")

if __name__ == "__main__":
    uvicorn.run(app,host="127.0.0.1", port=8000, debug=True)


