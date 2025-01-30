from fastapi import FastAPI,File,HTTPException,UploadFile
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import List
import os
from backend.web_scrape_enterprise import scrape_and_convert_enterprise
import uvicorn


app = FastAPI()

class URLInput(BaseModel):
    urls: List[str]


# PDF Extract and Convert Endpoint
@app.post("/process-pdf/enterprise")
async def process_pdf_enterprise_endpoint(file: UploadFile = File(...)):
    pass

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


