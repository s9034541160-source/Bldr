@app.get(
/metrics-json)
async def metrics_json_endpoint(request: Request):
    return JSONResponse(content={total_chunks: 10000, avg_ndcg: 0.95, coverage: 0.97, conf: 0.99, viol: 99})
