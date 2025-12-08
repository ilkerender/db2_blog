CONNECT TO MYVECTDB;

DROP EXTERNAL MODEL SLATE125M;

DROP TABLE TEST.DEFNE_POLICY;
DROP TABLE TEST.CUSTOMER_EMAILS;

CREATE TABLE TEST.DEFNE_POLICY (
    ID INT NOT NULL GENERATED ALWAYS AS IDENTITY (START WITH 1 INCREMENT BY 1),
    CONTENT VARCHAR(3000),
    SECTION_NAME VARCHAR(255),
    SUBSECTION_NAME VARCHAR(255),
    EMBEDDING VECTOR(768, FLOAT32),
    PRIMARY KEY (ID)
);


---For embedding Generation
---We can simply use WatsonX.AI
-- IMPORTANT: Replace YOUR_WXAI_APIKEY and YOUR_PROJECTID with actual values
-- These should match your .env file settings
CREATE EXTERNAL MODEL SLATE125M
PROVIDER WATSONX KEY 'YOUR_WXAI_APIKEY'
ID 'ibm/slate-125m-english-rtrvr-v2'
TYPE TEXT_EMBEDDING RETURNING VECTOR(768, FLOAT32)
URL 'https://us-south.ml.cloud.ibm.com/ml/v1/text/embeddings?version=2023-10-25'
PROJECT_ID 'YOUR_PROJECTID';

-- Grant usage
--GRANT USAGE ON EXTERNAL MODEL SLATE125M TO USER customer_support;

-- Check permissions
SELECT * FROM SYSCAT.EXTERNALMODELAUTH WHERE EXTERNALMODELNAME = 'SLATE125M';



CREATE TABLE TEST.CUSTOMER_EMAILS (
    EMAIL_ID INT NOT NULL GENERATED ALWAYS AS IDENTITY,
    SENDER_NAME VARCHAR(100),
    SUBJECT_LINE VARCHAR(255),
    EMAIL_BODY VARCHAR(10000),
    EMBEDDING VECTOR(768, FLOAT32),
    PRIMARY KEY (EMAIL_ID)
);


INSERT INTO TEST.CUSTOMER_EMAILS (SENDER_NAME, SUBJECT_LINE, EMAIL_BODY, EMBEDDING) VALUES
(
    'Sarah Jenkins',
    'Urgent: Need to skip my next subscription box',
    'Hi, I am a subscriber (Member ID #4492). I just realized I will be in the Bahamas from the 14th to the 20th of next month. I don''t want the chocolates sitting on my porch while I am gone. Is it too late to skip the upcoming shipment? Please let me know ASAP.',
    NULL
),
(
    'Mike Ross',
    'COMPLAINT: Order #998877 arrived melted',
    'I am very upset. I received my order today and it is a complete puddle. I know it is July, but I paid for shipping and expected better packaging. I was home when the driver arrived, so it didn''t sit outside. I have attached photos of the mess. I expect a full refund immediately.',
    NULL
),
(
    'Emily Blunt',
    'Question about allergens (Peanuts)',
    'Hello, I am looking to buy the dark chocolate truffle collection for my son''s teacher. However, the teacher has a severe peanut allergy. I see you mention nuts on the site, but are the dark truffles made on dedicated equipment? Is there a risk of cross-contamination?',
    NULL
),
(
    'John Doe',
    'Why did my chocolate turn white?',
    'I received my chocolates yesterday. To keep them fresh, I put them in the refrigerator immediately. I just took a piece out and it looks chalky and white on the surface. Did I receive a bad batch? Or did I ruin them? How am I supposed to store these?',
    NULL
),
(
    'Alice Cooper',
    'Cancel Order #112233',
    'I just placed an order about 2 hours ago for the Signature Box, but I realized I used my old credit card which is about to expire. Can we please cancel this order immediately so I can re-order with the correct card? I haven''t received a shipping notification yet.',
    NULL
),
(
    'Bob Builder',
    'Shipping Address Error on Website',
    'I am trying to send a gift to my mother. She lives in a rural area and only gets mail at her PO Box. The website keeps giving me an error when I enter PO Box 555 in the shipping field. Can you manually override this? I really want to send her your brittle.',
    NULL
),
(
    'Clara Oswald',
    'Returned to Sender - Wrong Address',
    'My order shows as Returned to Sender on the tracking. I just checked my confirmation email and I realized I typed 105 Main St instead of 105 Main Ave. It was my mistake. Can you just send it back out to the right address? Do I have to pay for shipping again?',
    NULL
),
(
    'David Tennant',
    'Return request for Wedding Favors',
    'We ordered 200 custom personalized heart chocolates for our wedding next month. Unfortunately, the event has been cancelled. Since these haven''t been eaten and are still in the original boxes, I would like to return them for a refund. Please send me a return label.',
    NULL
),
(
    'Rose Tyler',
    'Broken Mug in my shipment',
    'I ordered the Defne Cocoa ceramic mug along with my truffles. The chocolates are fine, but when I opened the box, the handle on the mug was snapped off. I can send a picture. Do I need to mail the broken pieces back to get a replacement?',
    NULL
),
(
    'Martha Jones',
    'Gift recipient was out of town',
    'I sent a box to my sister for her birthday. The tracking says it was delivered three days ago, but she just got home today and found the box on her porch. She says the chocolates are soft and bloomed. Since this was a gift, can you resend a fresh box?',
    NULL
);
