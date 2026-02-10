import uvicorn

uvicorn.run("api.server:app", host="0.0.0.0", port=8100, reload=True)
