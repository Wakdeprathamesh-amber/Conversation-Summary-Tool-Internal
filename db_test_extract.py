import yaml
import redshift_connector
import pandas as pd
import os
import json
from datetime import datetime
import numpy as np
from concurrent.futures import ThreadPoolExecutor
import logging
import traceback
from sqlalchemy import create_engine

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler('timeline_extraction.log'),
        logging.StreamHandler()
    ]
)

# class Databaseconnect:
#     def __init__(self, config_path='redshift.yaml'):
#         with open(config_path, 'r') as file:
#             self.config = yaml.safe_load(file)

class Databaseconnect:
    def __init__(self, config_path='/etc/secrets/redshift.yaml'):
        with open(config_path, 'r') as file:
            self.config = yaml.safe_load(file)



    def connect_database(self):
        # Create SQLAlchemy engine for better pandas compatibility
        connection_string = f"postgresql://{self.config['USER']}:{self.config['PASS']}@{self.config['HOST']}:{self.config['PORT']}/{self.config['NAME']}"
        engine = create_engine(connection_string)
        return engine

def normalize_timestamp(ts):
    """Convert various timestamp formats to ISO string format"""
    try:
        if ts is None:
            return None
        if isinstance(ts, str):
            return pd.to_datetime(ts).isoformat()
        if isinstance(ts, (pd.Timestamp, datetime)):
            return ts.isoformat()
        return pd.to_datetime(ts).isoformat()
    except Exception as e:
        logging.warning(f"Warning: Could not normalize timestamp {ts}: {e}")
        return str(ts) if ts is not None else None

def make_json_serializable(obj):
    """Convert pandas/numpy objects to JSON serializable formats"""
    import datetime
    if isinstance(obj, (pd.Timestamp, datetime.datetime)):
        return obj.isoformat()
    elif isinstance(obj, datetime.date):
        return obj.isoformat()
    elif isinstance(obj, np.integer):
        return int(obj)
    elif isinstance(obj, np.floating):
        return float(obj)
    elif isinstance(obj, np.bool_):
        return bool(obj)
    elif isinstance(obj, np.ndarray):
        return obj.tolist()
    elif pd.isna(obj):
        return None
    else:
        return obj

def clean_dataframe_for_json(df):
    """Clean DataFrame to ensure all values are JSON serializable"""
    df_clean = df.copy()
    for col in df_clean.columns:
        df_clean[col] = df_clean[col].apply(make_json_serializable)
    return df_clean

def consolidate_and_save_timeline(mobile_number=None, email=None):
    if not mobile_number and not email:
        logging.error("Either mobile_number or email must be provided")
        return

    logging.info(f"Starting timeline extraction for: {mobile_number or email}")

    # Queries
    whatsapp_query = '''
    WITH m AS (
        SELECT *, to_number AS agent_number, from_number AS customer_number
        FROM whatsapp_messages
        WHERE direction = 'inbound' AND source = 'eazybe'
        UNION
        SELECT *, from_number AS agent_number, to_number AS customer_number
        FROM whatsapp_messages
        WHERE direction = 'outbound' AND source = 'eazybe'
    )
    SELECT * FROM m WHERE customer_number = %s ORDER BY created_at;
    '''
    mail_query = '''
    WITH student_lead AS (
      SELECT
        json_extract_path_text(user_details, 'email') AS email,
        json_extract_path_text(user_details, 'phone') AS phone
      FROM leads
      WHERE 
        json_extract_path_text(user_details, 'phone') = %s
        OR json_extract_path_text(user_details, 'email') = %s
      LIMIT 1
    )
    SELECT
      le.timestamp,
      le.from_email AS sender_email,
      le.to_email AS recipient_email,
      le.subject,
      json_extract_path_text(le.data, 'content') AS message,
      json_extract_path_text(le.data, 'snippet') AS snippet,
      json_extract_path_text(le.data, 'direction') AS direction,
      CASE 
        WHEN le.from_email = (SELECT email FROM student_lead) THEN 'student'
        ELSE 'agent'
      END AS sender_type,
      CASE 
        WHEN le.from_email = (SELECT email FROM student_lead) THEN le.to_email
        ELSE le.from_email
      END AS agent_email,
      (SELECT email FROM student_lead) AS student_email
    FROM leads_emails le
    WHERE 
      (le.from_email = (SELECT email FROM student_lead) 
       OR le.to_email = (SELECT email FROM student_lead))
      AND json_extract_path_text(le.data, 'content') IS NOT NULL
      AND json_extract_path_text(le.data, 'content') <> ''
    ORDER BY le.timestamp DESC;
    '''
    call_query = '''
    WITH student_lead AS (
      SELECT
        json_extract_path_text(user_details, 'phone') AS phone
      FROM leads
      WHERE 
        json_extract_path_text(user_details, 'phone') = %s
        OR json_extract_path_text(user_details, 'email') = %s
      LIMIT 1
    )
    SELECT
      lc.id,
      lc.timestamp,
      json_extract_path_text(lc.data, 'duration') AS duration,
      lc.to_number,
      lc.from_number,
      lc.source,
      json_extract_path_text(lc.data, 'RecordUrl') AS record_url
    FROM leads_calls lc
    JOIN student_lead sl 
      ON lc.to_number = sl.phone OR lc.from_number = sl.phone
    ORDER BY lc.timestamp DESC
    LIMIT 100;
    '''
    lead_query = '''
    SELECT
      leads.id AS lead_id,
      json_extract_path_text(user_details, 'name') AS user_name,
      json_extract_path_text(user_details, 'email') AS email,
      json_extract_path_text(user_details, 'phone') AS phone,
      json_extract_path_text(data, 'university') AS university,
      json_extract_path_text(data, 'move_in_date') AS move_in_date,
      json_extract_path_text(data, 'lease_duration') AS lease_duration,
      move_out_date,
      CAST(json_extract_path_text(data, 'budget') AS INTEGER) AS budget,
      json_extract_path_text(data, 'budget_currency') AS budget_currency,
      json_extract_path_text(data, 'budget_duration') AS budget_duration,
      json_extract_path_text(location, 'locality', 'long_name') AS city,
      json_extract_path_text(location, 'state', 'long_name') AS state,
      json_extract_path_text(location, 'country', 'long_name') AS country,
      json_extract_path_text(data, 'program_type') AS program_type,
      json_extract_path_text(data, 'is_share_room') = 'true' AS is_share_room,
      region_id,
      agent_id,
      inventory_id
    FROM
      leads
    WHERE 1=1
      AND (json_extract_path_text(user_details, 'phone') = %s OR json_extract_path_text(user_details, 'email') = %s)
    LIMIT 1;
    '''

    contact = mobile_number if mobile_number else email

    def fetch_whatsapp():
        try:
            engine = Databaseconnect().connect_database()
            df = pd.read_sql(whatsapp_query, engine, params=[contact])
            logging.info("Fetched WhatsApp data successfully.")
            return df
        except Exception as e:
            logging.error(f"WhatsApp query failed: {e}\n{traceback.format_exc()}")
            return pd.DataFrame()
    def fetch_mail():
        try:
            engine = Databaseconnect().connect_database()
            df = pd.read_sql(mail_query, engine, params=[contact, contact])
            logging.info("Fetched mail data successfully.")
            return df
        except Exception as e:
            logging.warning(f"Mail query failed: {e}\n{traceback.format_exc()}")
            return pd.DataFrame()
    def fetch_call():
        try:
            engine = Databaseconnect().connect_database()
            df = pd.read_sql(call_query, engine, params=[contact, contact])
            logging.info("Fetched call data successfully.")
            return df
        except Exception as e:
            logging.error(f"Call query failed: {e}\n{traceback.format_exc()}")
            return pd.DataFrame()
    def fetch_lead():
        try:
            engine = Databaseconnect().connect_database()
            df = pd.read_sql(lead_query, engine, params=[contact, contact])
            logging.info("Fetched lead info successfully.")
            return df
        except Exception as e:
            logging.error(f"Lead info query failed: {e}\n{traceback.format_exc()}")
            return pd.DataFrame()

    try:
        with ThreadPoolExecutor() as executor:
            futures = {
                'whatsapp': executor.submit(fetch_whatsapp),
                'mail': executor.submit(fetch_mail),
                'call': executor.submit(fetch_call),
                'lead': executor.submit(fetch_lead)
            }
            results = {key: future.result() for key, future in futures.items()}

        whatsapp_df = clean_dataframe_for_json(results['whatsapp'])
        mail_df = clean_dataframe_for_json(results['mail'])
        call_df = clean_dataframe_for_json(results['call'])
        lead_df = clean_dataframe_for_json(results['lead'])

        # Build events list
        events = []

        # Process WhatsApp messages
        for _, row in whatsapp_df.iterrows():
            event = {
                'type': 'whatsapp',
                'timestamp': normalize_timestamp(row.get('created_at')),
                **{k: v for k, v in row.dropna().to_dict().items() if k != 'created_at'}
            }
            if event['timestamp']:
                events.append(event)

        # Process email messages
        for _, row in mail_df.iterrows():
            event = {
                'type': 'email',
                'timestamp': normalize_timestamp(row.get('timestamp')),
                **{k: v for k, v in row.dropna().to_dict().items() if k != 'timestamp'}
            }
            if event['timestamp']:
                events.append(event)

        # Process call records
        for _, row in call_df.iterrows():
            event = {
                'type': 'call',
                'timestamp': normalize_timestamp(row.get('timestamp')),
                **{k: v for k, v in row.dropna().to_dict().items() if k != 'timestamp'}
            }
            if event['timestamp']:
                events.append(event)

        # Process lead information
        if not lead_df.empty:
            lead_info = lead_df.iloc[0].dropna().to_dict()
            lead_event = {
                'type': 'lead_info',
                'timestamp': normalize_timestamp(lead_info.get('move_in_date', datetime.now())),
                **{k: v for k, v in lead_info.items() if k != 'move_in_date'}
            }
            if lead_event['timestamp']:
                events.append(lead_event)

        # Filter out events without timestamps and sort
        events = [e for e in events if e.get('timestamp')]
        events.sort(key=lambda x: x['timestamp'])

        # Ensure all data is JSON serializable
        for event in events:
            for key, value in event.items():
                event[key] = make_json_serializable(value)

        # --- WhatsApp Pack Logic ---
        packed_events = []
        i = 0
        while i < len(events):
            if events[i]['type'] == 'whatsapp':
                pack = [events[i]]
                j = i + 1
                while j < len(events) and events[j]['type'] == 'whatsapp':
                    pack.append(events[j])
                    j += 1
                # Create a whatsapp_pack event
                packed_events.append({
                    'type': 'whatsapp_pack',
                    'start_timestamp': pack[0]['timestamp'],
                    'end_timestamp': pack[-1]['timestamp'],
                    'messages': pack
                })
                i = j
            else:
                packed_events.append(events[i])
                i += 1
        events = packed_events
        # --- End WhatsApp Pack Logic ---

        # Create output directory and save
        os.makedirs('data', exist_ok=True)

        if mobile_number:
            timeline_path = os.path.join('data', f'timeline_{mobile_number}.json')
        elif email:
            # Replace @ and . with _ for filename
            email_safe = email.replace('@', '_').replace('.', '_')
            timeline_path = os.path.join('data', f'timeline_{email_safe}.json')
        else:
            timeline_path = os.path.join('data', 'timeline_unknown.json')

        try:
            with open(timeline_path, 'w', encoding='utf-8') as f:
                json.dump(events, f, indent=2, ensure_ascii=False)
            logging.info(f"Timeline saved to {timeline_path} with {len(events)} events.")
        except Exception as e:
            logging.error(f"Failed to save timeline to {timeline_path}: {e}\n{traceback.format_exc()}")

        # Print summary
        event_types = {}
        for event in events:
            event_type = event.get('type', 'unknown')
            event_types[event_type] = event_types.get(event_type, 0) + 1

        logging.info("Event summary:")
        for event_type, count in event_types.items():
            logging.info(f"  {event_type}: {count} events")
        logging.info(f"Timeline extraction completed for: {mobile_number or email}")
    except Exception as e:
        logging.critical(f"Timeline extraction failed: {e}\n{traceback.format_exc()}")

# Optional: Simple test function
if __name__ == "__main__":
    test_mobile = "917007220975"  # Example from your data
    test_email = None  # Or set to a test email
    logging.info("Running timeline extraction test...")
    consolidate_and_save_timeline(mobile_number=test_mobile, email=test_email) 
