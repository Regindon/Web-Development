import gspread
import pandas as pd
import os
import time
from google.oauth2.service_account import Credentials

# -----------------------------
# 👉 STEP 1: Google Sheets Setup
# -----------------------------
SHEET_NAME = "Trading Data"  # Change to your actual sheet name
CREDENTIALS_FILE = "google_sheets_credentials.json"  # Replace with your credentials file path

# Google Sheets Authentication
scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
creds = Credentials.from_service_account_file(CREDENTIALS_FILE, scopes=scope)
client = gspread.authorize(creds)

def get_gsheet():
    try:
        sheet = client.open(SHEET_NAME).sheet1  # Access the first sheet
        return sheet
    except Exception as e:
        print(f"❌ Error: Unable to access Google Sheet - {e}")
        exit()

sheet = get_gsheet()
print("✅ Connected to Google Sheets!")

# -----------------------------
# 👉 STEP 2: Load the Cleaned Trade Data
# -----------------------------
trade_data_folder = "Trade-Data"
files = [f for f in os.listdir(trade_data_folder) if f.startswith("Cleaned_Trades_") and f.endswith(".csv")]

if not files:
    print("❌ No cleaned trade data found. Run the first script first!")
    exit()

files.sort(reverse=True)
csv_file = os.path.join(trade_data_folder, files[0])
df = pd.read_csv(csv_file)
print(f"✅ Loaded cleaned trade data from {csv_file}")

# -----------------------------
# 👉 STEP 3: Validate & Clean Data
# -----------------------------
def validate_and_clean_data(df):
    required_columns = ["Quantity", "Symbol", "Side", "Pnl", "Pts", "Result", "Drt Category", "Session", 
                        "ATR 1M", "ATR 5M", "Duration", "Buy Price", "Sell Price", "Bought Time", "Sold Time"]
    missing_cols = [col for col in required_columns if col not in df.columns]
    if missing_cols:
        print(f"❌ Missing columns: {missing_cols}. Ensure the CSV format is correct.")
        exit()
    
    df["Bought Time"] = pd.to_datetime(df["Bought Time"], errors='coerce').dt.strftime("%Y-%m-%d %H:%M:%S")
    df["Sold Time"] = pd.to_datetime(df["Sold Time"], errors='coerce').dt.strftime("%Y-%m-%d %H:%M:%S")
    
    numeric_fields = ["Pnl", "Pts", "ATR 1M", "ATR 5M", "Duration", "Buy Price", "Sell Price"]
    for field in numeric_fields:
        df[field] = pd.to_numeric(df[field], errors='coerce')
    
    df = df.dropna(subset=["Symbol", "Side", "Pnl", "Bought Time", "Sold Time"])
    
    # Replace NaN values in Duration with 1
    df.fillna({"Duration": 1}, inplace=True)
    
    return df

df = validate_and_clean_data(df)
print(f"📊 Total trades before upload: {len(df)}")

# -----------------------------
# 👉 STEP 4: Fetch Existing Trades from Google Sheets
# -----------------------------
def fetch_existing_trades(sheet):
    try:
        existing_records = sheet.get_all_values()
        headers = existing_records[0]  # First row contains headers
        
        # Find correct column indices for "Symbol" and "Bought Time"
        symbol_index = headers.index("Symbol")
        bought_time_index = headers.index("Bought Time")
        
        existing_trades = set()
        
        for row in existing_records[1:]:  # Skip headers
            if len(row) > bought_time_index:
                symbol = row[symbol_index].strip()
                bought_time = row[bought_time_index].strip()

                # Convert to standardized datetime format
                bought_time = pd.to_datetime(bought_time, errors="coerce").strftime("%Y-%m-%d %H:%M:%S")
                existing_trades.add((symbol, bought_time))
        
        return existing_trades
    except Exception as e:
        print(f"❌ Error fetching existing trades: {e}")
        return set()

existing_trades = fetch_existing_trades(sheet)
print(f"🔍 Found {len(existing_trades)} existing trades in Google Sheets.")

# -----------------------------
# 👉 STEP 5: Upload New Trades to Google Sheets
# -----------------------------
def upload_trades_in_batches(sheet, trades):
    try:
        batch_data = []
        for row in trades:
            batch_data.append(row.tolist())

        last_row = len(sheet.get_all_values()) + 1  # Find the last row
        sheet.insert_rows(batch_data, row=last_row)  # Insert new trades below table
        
        print(f"✅ Uploaded {len(batch_data)} trades inside the table.")
    except Exception as e:
        print(f"❌ Error during batch upload: {e}")

failed_trades = []
print("🚀 Uploading new trades to Google Sheets in batch mode...")
new_trades = [row for _, row in df.iterrows() if (row["Symbol"], row["Bought Time"]) not in existing_trades]

if new_trades:
    upload_trades_in_batches(sheet, new_trades)

if failed_trades:
    failed_df = pd.DataFrame(failed_trades)
    failed_df.to_csv("failed_trades.csv", index=False)
    print(f"⚠️ Some trades failed to upload. Saved to failed_trades.csv")

print("🎉 All new trades uploaded successfully!")
