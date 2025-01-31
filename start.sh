#!/bin/bash
uvicorn api.fastapi_backend:app --host 0.0.0.0 --port $PORT
