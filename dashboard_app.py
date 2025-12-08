import os
import time
import ibm_db
import requests
import dash
from dash import dcc, html, dash_table, Input, Output, State, callback
from dotenv import load_dotenv

# 1. Load Environment Variables
load_dotenv()

DB_CONN_STR = (
    f"DATABASE={os.getenv('DB2_DATABASE')};HOSTNAME={os.getenv('DB2_HOSTNAME')};"
    f"PORT={os.getenv('DB2_PORT')};PROTOCOL=TCPIP;"
    f"UID={os.getenv('DB2_UID')};PWD={os.getenv('DB2_PWD')};"
)

# Global variable to cache the token briefly
IAM_TOKEN = None
TOKEN_EXPIRY = 0

# --- HELPER: Get IBM Cloud IAM Token ---
def get_bearer_token():
    global IAM_TOKEN, TOKEN_EXPIRY
    if IAM_TOKEN and time.time() < TOKEN_EXPIRY:
        return IAM_TOKEN

    api_key = os.getenv("WATSONX_APIKEY")
    url = "https://iam.cloud.ibm.com/identity/token"
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    data = f"grant_type=urn:ibm:params:oauth:grant-type:apikey&apikey={api_key}"

    response = requests.post(url, headers=headers, data=data)
    response.raise_for_status()
    json_data = response.json()

    IAM_TOKEN = json_data["access_token"]
    TOKEN_EXPIRY = time.time() + json_data["expires_in"] - 60
    return IAM_TOKEN

# --- HELPER: Query Watsonx.ai ---
def query_watsonx(prompt):
    try:
        token = get_bearer_token()
        project_id = os.getenv("WATSONX_PROJECT_ID")
        url = os.getenv("WATSONX_URL") + "/ml/v1/text/generation?version=2023-05-29"

        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }

        body = {
            "input": prompt,
            "parameters": {
                "decoding_method": "greedy",
                "max_new_tokens": 600,
                "repetition_penalty": 1.1,
                "min_new_tokens": 10
            },
            "model_id": "meta-llama/llama-3-3-70b-instruct",
            "project_id": project_id
        }

        response = requests.post(url, headers=headers, json=body, timeout=30)
        if response.status_code != 200:
            return f"Error from Watsonx: {response.text}"
        return response.json().get("results", [{}])[0].get("generated_text", "No text generated.")
    except Exception as e:
        return f"System Error: {str(e)}"

# --- HELPER: Fetch Emails ---
def get_emails():
    try:
        conn = ibm_db.connect(DB_CONN_STR, "", "")
        sql = "SELECT EMAIL_ID, SENDER_NAME, SUBJECT_LINE, EMAIL_BODY FROM TEST.CUSTOMER_EMAILS ORDER BY EMAIL_ID"
        stmt = ibm_db.exec_immediate(conn, sql)
        data = []
        row = ibm_db.fetch_assoc(stmt)
        while row:
            data.append(row)
            row = ibm_db.fetch_assoc(stmt)
        ibm_db.close(conn)
        return data
    except Exception as e:
        print(f"Db Error: {e}")
        return []

# --- HELPER: RAG Search ---
def perform_rag_search(email_id):
    try:
        conn = ibm_db.connect(DB_CONN_STR, "", "")

        # 1. Fetch Email
        email_sql = "SELECT SUBJECT_LINE, EMAIL_BODY FROM TEST.CUSTOMER_EMAILS WHERE EMAIL_ID = ?"
        stmt = ibm_db.prepare(conn, email_sql)
        ibm_db.bind_param(stmt, 1, email_id)
        ibm_db.execute(stmt)
        email_row = ibm_db.fetch_assoc(stmt)

        if not email_row:
            ibm_db.close(conn)
            return None, None, 0

        full_email_text = f"Subject: {email_row['SUBJECT_LINE']}\nBody: {email_row['EMAIL_BODY']}"

        # 2. Vector Search
        search_sql = """
            SELECT P.SECTION_NAME, P.SUBSECTION_NAME, P.CONTENT,
                   VECTOR_DISTANCE(E.EMBEDDING, P.EMBEDDING, COSINE) as SCORE
            FROM TEST.DEFNE_POLICY P, TEST.CUSTOMER_EMAILS E
            WHERE E.EMAIL_ID = ?
            ORDER BY SCORE ASC
            FETCH FIRST 4 ROWS ONLY
        """

        start_time = time.time()
        search_stmt = ibm_db.prepare(conn, search_sql)
        ibm_db.bind_param(search_stmt, 1, email_id)
        ibm_db.execute(search_stmt)

        retrieved_docs = []
        row = ibm_db.fetch_assoc(search_stmt)
        while row:
            retrieved_docs.append(row)
            row = ibm_db.fetch_assoc(search_stmt)

        ibm_db.close(conn)
        return full_email_text, retrieved_docs, (time.time() - start_time)
    except Exception as e:
        print(f"RAG Error: {e}")
        return None, [], 0

# --- DASH APP SETUP ---
external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']
app = dash.Dash(__name__, title="Defne AI Support", external_stylesheets=external_stylesheets)

# Define Styles
STYLES = {
    'container': {
        'display': 'flex',
        'flexDirection': 'row',
        'height': 'calc(100vh - 100px)',
        'gap': '20px',
        'padding': '20px',
        'maxWidth': '1400px',
        'margin': '0 auto'
    },
    'sidebar': {
        'flex': '0 0 350px',
        'backgroundColor': '#ffffff',
        'padding': '20px',
        'borderRadius': '8px',
        'boxShadow': '0 2px 4px rgba(0,0,0,0.1)',
        'overflowY': 'auto'
    },
    # UPDATED MAIN STYLE: Changed from flex to block to prevent overlap issues
    'main': {
        'flex': '1',
        'backgroundColor': '#ffffff',
        'padding': '30px',
        'borderRadius': '8px',
        'boxShadow': '0 2px 4px rgba(0,0,0,0.1)',
        'overflowY': 'auto',
        'display': 'block', # Fix: Ensures standard flow
        'position': 'relative'
    },
    'header': {
        'backgroundColor': '#4a3b32',
        'color': 'white',
        'padding': '15px 30px',
        'textAlign': 'center',
        'marginBottom': '0'
    }
}

app.layout = html.Div([
    # HEADER
    html.Div([
        html.H1("🍫 Defne Chocolates Support AI", style={'margin': 0, 'fontSize': '28px'}),
        html.P("Powered by Db2 Vector Search & Watsonx", style={'margin': 0, 'opacity': 0.8})
    ], style=STYLES['header']),

    # FLEX CONTAINER
    html.Div([

        # LEFT SIDEBAR: INBOX
        html.Div([
            html.H4("📩 Inbox", style={'marginTop': 0}),
            html.Button('Refresh', id='btn-refresh', n_clicks=0, style={'width': '100%', 'marginBottom': '10px'}),

            dash_table.DataTable(
                id='email-table',
                columns=[
                    {'name': 'Sender', 'id': 'SENDER_NAME'},
                    {'name': 'Subject', 'id': 'SUBJECT_LINE'}
                ],
                data=get_emails(),
                row_selectable='single',
                style_table={'overflowX': 'hidden'},
                style_cell={'textAlign': 'left', 'padding': '12px', 'whiteSpace': 'normal', 'height': 'auto'},
                style_header={'backgroundColor': '#f1f1f1', 'fontWeight': 'bold'},
                style_data_conditional=[
                    {'if': {'row_index': 'odd'}, 'backgroundColor': '#f9f9f9'},
                    {'if': {'state': 'selected'}, 'backgroundColor': '#e2e6ea', 'border': '1px solid #adb5bd'}
                ]
            ),
        ], style=STYLES['sidebar']),

        # RIGHT MAIN: CONTENT
        html.Div([
            html.H4("Agent Console", style={'marginTop': 0}),

            # Email Viewer
            html.Div(id='selected-email-display', style={
                'backgroundColor': '#f8f9fa',
                'padding': '20px',
                'borderRadius': '5px',
                'borderLeft': '5px solid #4a3b32',
                'marginBottom': '20px',
                'minHeight': '80px'
            }, children="Select an email from the inbox to begin."),

            # Action Button Container (Fixed spacing issues)
            html.Div([
                html.Button("Get AI Draft Response", id='btn-generate', n_clicks=0, disabled=True,
                            style={'backgroundColor': '#4a3b32', 'color': 'white', 'width': '200px'}),
            ], style={'marginBottom': '25px', 'borderTop': '1px solid #eee', 'paddingTop': '20px'}),

            # Loading & Output
            dcc.Loading(
                id="loading-1",
                type="circle",
                children=html.Div(id='ai-response-output', style={'marginTop': '10px'})
            )

        ], style=STYLES['main'])

    ], style=STYLES['container'])
], style={'backgroundColor': '#f4f4f4', 'minHeight': '100vh', 'fontFamily': 'Arial, sans-serif'})

# --- CALLBACKS ---

@callback(
    [Output('selected-email-display', 'children'),
     Output('btn-generate', 'disabled')],
    Input('email-table', 'selected_rows'),
    State('email-table', 'data')
)
def display_selected_email(selected_rows, data):
    if not selected_rows:
        return html.P("Select an email from the inbox to begin.", style={'color': '#777'}), True

    row = data[selected_rows[0]]

    return html.Div([
        html.H5(row['SUBJECT_LINE'], style={'marginBottom': '5px', 'fontWeight': 'bold'}),
        html.P([html.Strong("From: "), f"{row['SENDER_NAME']} (ID: {row['EMAIL_ID']})"], style={'color': '#555', 'marginBottom': '15px'}),
        html.Hr(style={'borderTop': '1px solid #ccc'}),
        html.Div(row['EMAIL_BODY'], style={'whiteSpace': 'pre-wrap', 'fontFamily': 'sans-serif', 'fontSize': '14px', 'lineHeight': '1.5'})
    ]), False

@callback(
    Output('ai-response-output', 'children'),
    Input('btn-generate', 'n_clicks'),
    State('email-table', 'selected_rows'),
    State('email-table', 'data'),
    prevent_initial_call=True
)
def generate_ai_response(n_clicks, selected_rows, data):
    if not selected_rows:
        return ""

    email_id = data[selected_rows[0]]['EMAIL_ID']
    full_email_text, retrieved_docs, db_duration = perform_rag_search(email_id)

    if not retrieved_docs:
        return html.Div("Error: No vectors found. Please check database content.", style={'color': 'red'})

    # Build Context
    context_str = ""
    for idx, doc in enumerate(retrieved_docs):
        context_str += f"\n--- Source {idx+1}: {doc['SECTION_NAME']} ---\n{doc['CONTENT']}\n"

    # Build Prompt
    system_prompt = f"""You are a professional customer support agent for Defne Chocolates.

Your task is to draft a response to the customer inquiry below using ONLY the information provided in the policy documents.

Structure your response in TWO sections:

1. A well-formatted, professional, and courteous reply addressing the customer's concerns. Reference specific policies where applicable and maintain a helpful, empathetic tone.
2. INTERNAL NOTES: Bullet points highlighting key actions for the human support agent, including policy references, verification steps, and any follow-up required.

POLICY DOCUMENTS:
{context_str}

CUSTOMER EMAIL:
{full_email_text}

RESPONSE:
    """

    wx_start = time.time()
    ai_response = query_watsonx(system_prompt)
    wx_duration = time.time() - wx_start

    return html.Div([
        # Metrics Bar
        html.Div([
            html.Span(f"Db2 Search: {db_duration:.4f}s", style={'marginRight': '20px', 'fontWeight': 'bold', 'color': '#28a745'}),
            html.Span(f"Watsonx AI: {wx_duration:.2f}s", style={'fontWeight': 'bold', 'color': '#007bff'})
        ], style={'backgroundColor': '#e9ecef', 'padding': '10px', 'borderRadius': '5px', 'marginBottom': '20px'}),

        # AI Response
        html.Label("Drafted Response:", style={'fontWeight': 'bold'}),
        dcc.Markdown(ai_response, style={'backgroundColor': '#fff', 'border': '1px solid #ddd', 'padding': '15px', 'borderRadius': '5px'}),

        # Sources
        html.Br(),
        html.Details([
            html.Summary("Show Retrieval Evidence", style={'cursor': 'pointer', 'color': '#4a3b32'}),
            html.Pre(context_str, style={'backgroundColor': '#f8f9fa', 'padding': '15px', 'borderRadius': '5px', 'whiteSpace': 'pre-wrap', 'marginTop': '10px'})
        ])
    ])

if __name__ == '__main__':
    app.run_server(debug=True, host='0.0.0.0', port=8050)
