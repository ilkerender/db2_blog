-- 1. Generate Embeddings for Policy Documents
-- Db2 calls Watsonx internally for every row where embedding is NULL
UPDATE TEST.DEFNE_POLICY 
SET EMBEDDING = TO_EMBEDDING(CONTENT USING SLATE125M)
WHERE EMBEDDING IS NULL;

-- 2. Generate Embeddings for Emails
-- We combine Subject and Body in the function call for better context
UPDATE TEST.CUSTOMER_EMAILS 
SET EMBEDDING = TO_EMBEDDING(SUBJECT_LINE || '. ' || EMAIL_BODY USING SLATE125M)
WHERE EMBEDDING IS NULL;

-- 3. Verify
SELECT ID, SUBSTR(CONTENT, 1, 30) as TEXT, EMBEDDING 
FROM TEST.DEFNE_POLICY 
FETCH FIRST 2 ROWS ONLY;