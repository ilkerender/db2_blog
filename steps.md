### 0 - Setup relevant tables: 
```
db2 -tvf 0_db2_setup.sql
..
DB20000I  The SQL command completed successfully.
```

### 1 - process document
```
python3 1_process_document.py defne_chocolates.pdf
Processing defne_chocolates.pdf...
2025-11-26 08:26:18,375 - INFO - detected formats: [<InputFormat.PDF: 'pdf'>]
2025-11-26 08:26:18,399 - INFO - Going to convert document batch...
2025-11-26 08:26:18,400 - INFO - Initializing pipeline for StandardPdfPipeline with options hash 44ae89a68fc272bc7889292e9b5a1bad
2025-11-26 08:26:18,415 - INFO - Loading plugin 'docling_defaults'
2025-11-26 08:26:18,417 - INFO - Registered picture descriptions: ['vlm', 'api']
2025-11-26 08:26:18,430 - INFO - Loading plugin 'docling_defaults'
2025-11-26 08:26:18,434 - INFO - Registered ocr engines: ['auto', 'easyocr', 'ocrmac', 'rapidocr', 'tesserocr', 'tesseract']
2025-11-26 08:26:18,435 - INFO - rapidocr cannot be used because onnxruntime is not installed.
2025-11-26 08:26:18,435 - INFO - easyocr cannot be used because it is not installed.
2025-11-26 08:26:19,029 - INFO - Accelerator device: 'cpu'
[INFO] 2025-11-26 08:26:19,085 [RapidOCR] base.py:22: Using engine_name: torch
[INFO] 2025-11-26 08:26:19,090 [RapidOCR] download_file.py:68: Initiating download: https://www.modelscope.cn/models/RapidAI/RapidOCR/resolve/v3.4.0/torch/PP-OCRv4/det/ch_PP-OCRv4_det_infer.pth
.....
2025-11-26 08:26:30,104 - INFO - Auto OCR model selected rapidocr with torch.
2025-11-26 08:26:30,110 - INFO - Accelerator device: 'cpu'
2025-11-26 08:26:43,422 - INFO - Accelerator device: 'cpu'
2025-11-26 08:26:44,381 - INFO - Processing document defne_chocolates.pdf
2025-11-26 08:27:02,975 - INFO - Finished converting document defne_chocolates.pdf in 44.61 sec.
Saved 46 chunks to defne_chocolates.jsonl
```

### 2 - Ingest Chunked policy docs
```
python3 2_ingest_chunks.py defne_chocolates.jsonl
Connected to MYVECTDB. Ingesting defne_chocolates.jsonl...
Inserted 46 rows. Embeddings are currently NULL.
```

### 3 - Update embeddings
```
db2 -tvf 3_generate_embeddings.sql
UPDATE TEST.DEFNE_POLICY SET EMBEDDING = TO_EMBEDDING(CONTENT USING SLATE125M) WHERE EMBEDDING IS NULL
DB20000I  The SQL command completed successfully.

UPDATE TEST.CUSTOMER_EMAILS SET EMBEDDING = TO_EMBEDDING(SUBJECT_LINE || '. ' || EMAIL_BODY USING SLATE125M) WHERE EMBEDDING IS NULL
DB20000I  The SQL command completed successfully.
```

### 4 - Update env settings & run the app 
```
python3 app.py
Dash is running on http://0.0.0.0:8050/

 * Serving Flask app 'app'
 * Debug mode: on
```



