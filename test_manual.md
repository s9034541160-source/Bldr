# Bldr Empire v2 Manual E2E Testing Guide

## Prerequisites
1. Ensure all services are running using `run_system.sh` or `one_click_start.bat`
2. LM Studio with required models loaded:
   - DeepSeek/Qwen3-Coder (for coordinator)
   - Qwen2.5-VL (for vision analysis)
   - Mistral (for general tasks)
3. Test data prepared:
   - Sample photo (site.jpg for VL analysis)
   - Sample audio (meeting.mp3 for transcription if Whisper is used)
   - Sample estimate (smeta.csv with GESN rates)
   - Sample project LSR in Neo4j

## Scenario 1: Frontend Query

### Steps:
1. Open browser and navigate to http://localhost:3000
2. Go to the Query tab
3. Enter query: "Проверь фото на СП31 + смета ГЭСН Екатеринбург"
4. Upload a sample photo (site.jpg)
5. Select a project LSR from the dropdown
6. Click Submit

### Expected Results:
1. **Parse Stage**:
   - Intent detected: "qc+finance"
   - Entities extracted: {"norm": "СП31", "rate": "ГЭСН"}
   - Confidence score > 0.8

2. **Plan Stage**:
   - JSON plan generated with roles: [qc_compliance, analyst, chief_engineer]
   - Tasks assigned with appropriate tools
   - Estimated execution time < 30s

3. **Execute Stage**:
   - Role agents invoked with proper inputs
   - Tools executed successfully:
     * vl_analyze for photo analysis
     * calc_estimate for GESN calculation
     * gen_docx for report generation
   - All responses contain [Source: ...] citations

4. **Aggregate Stage**:
   - Final synthesis in Russian
   - ZIP file generated with:
     * photo_analysis.pdf
     * budget.csv
   - No hallucinations in output

5. **Storage**:
   - Check Neo4j: `MATCH (q:QueryResult) RETURN q`
   - Verify plan, responses, files, and sources are stored

## Scenario 2: TG Bot

### Steps:
1. Open Telegram
2. Find and message the Bldr bot
3. Send: "Анализ фото site.jpg на SanPiN + timeline проект LSR"
4. Attach the sample photo

### Expected Results:
1. **Response**:
   - Initial message: "План: complexity med..."
   - ZIP attachment with analysis.docx and timeline.gantt

2. **Processing**:
   - Parse → Plan → Roles invoke
   - chief VL photo agent with [Source: SanPiN]
   - project_manager timeline agent
   - Aggregate response

3. **Storage**:
   - Check Neo4j: `MATCH (q:QueryResult {source: 'tg'}) RETURN q`
   - Verify all data stored correctly

## Scenario 3: AI-Shell

### Steps:
1. Open terminal
2. Run: `curl -X POST http://localhost:8000/submit_query -H "Content-Type: application/json" -d '{"query": "Бюджет GESN 8-6-1.1 Москва + письмо заказчику", "source": "shell"}'`

### Expected Results:
1. **Response**:
   - JSON plan with roles and tasks
   - Agent responses with [Source: ...] citations
   - Final synthesis in Russian
   - File download links

2. **Output**:
   - Print JSON plan/responses/final
   - Files available for download

## Error Testing

### LM Studio Down:
1. Stop LM Studio
2. Run any query
3. Expected: "LM error: Connection refused, fallback simple RAG" + basic response

### Low RuBERT Confidence:
1. Use ambiguous query
2. Expected: "Parse error: Confidence 0.6, fallback regex"

### Tool Fail:
1. Remove GESN file
2. Run estimate calculation
3. Expected: "Calc error: No data, cite [Source: Empty]"

## Metrics to Verify:
- Time: plan <30s, full execution <5min
- Tokens used <4096
- 100% of facts have [Source: ...] citations
- No hallucinations (manual verification)

## Verification Commands:

### Check Neo4j:
```cypher
MATCH (q:QueryResult) 
RETURN q.id, q.timestamp, q.source 
ORDER BY q.timestamp DESC 
LIMIT 5
```

### Check Files:
```bash
ls -la exports/
cat exports/budget.csv
```

### Check Logs:
```bash
tail -f logs/system.log
```