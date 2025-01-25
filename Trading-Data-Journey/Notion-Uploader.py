from notion_client import Client
import pandas as pd
import os
import time

# -----------------------------
# 👉 STEP 1: Set Up Notion API Client
# -----------------------------
NOTION_TOKEN = "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"
DATABASE_ID = "186e69f71a04806197eed7edba0a7000"  # Replace with your Notion database ID
notion = Client(auth=NOTION_TOKEN)

# -----------------------------
# 👉 STEP 2: Load and Verify the Cleaned Trade Data
# -----------------------------
trade_data_folder = "Trade-Data"
files = [f for f in os.listdir(trade_data_folder) if f.startswith("Cleaned_Trades_") and f.endswith(".csv")]

if not files:
    print("❌ No cleaned trade data found. Run the first script first!")
    exit()

files.sort(reverse=True)  # Sort to get the latest file
csv_file = os.path.join(trade_data_folder, files[0])
df = pd.read_csv(csv_file)
print(f"✅ Loaded cleaned trade data from {csv_file}")

# Ensure all required columns are present
def validate_and_clean_data(df):
    required_columns = ["Quantity", "Symbol", "Side", "Pnl", "Pts", "Result", "Drt Category", "Session", 
                        "ATR 1M", "ATR 5M", "Duration", "Buy Price", "Sell Price", "Bought Time", "Sold Time"]
    missing_cols = [col for col in required_columns if col not in df.columns]
    if missing_cols:
        print(f"❌ Missing columns: {missing_cols}. Ensure the CSV format is correct.")
        exit()
    
    df["Bought Time"] = pd.to_datetime(df["Bought Time"], errors='coerce')
    df["Sold Time"] = pd.to_datetime(df["Sold Time"], errors='coerce')
    
    numeric_fields = ["Pnl", "Pts", "ATR 1M", "ATR 5M", "Duration", "Buy Price", "Sell Price"]
    for field in numeric_fields:
        df[field] = pd.to_numeric(df[field], errors='coerce')
    
    df = df.dropna(subset=["Symbol", "Side", "Pnl", "Bought Time", "Sold Time"])
    return df

df = validate_and_clean_data(df)

print(f"📊 Total trades before upload: {len(df)}")

# -----------------------------
# 👉 STEP 3: Fetch Existing Trades from Notion
# -----------------------------
def fetch_existing_trades():
    existing_trades = {}
    query = notion.databases.query(database_id=DATABASE_ID)
    
    for page in query["results"]:
        properties = page["properties"]
        try:
            symbol_field = properties["Symbol"].get("select", {})
            if not symbol_field:
                print("⚠️ Warning: 'Symbol' is empty in a trade entry, skipping...")
                continue
            symbol = symbol_field["name"]
        except KeyError:
            print("⚠️ Warning: Missing 'Symbol' select in a trade entry, skipping...")
            continue
        
        bought_time = properties.get("Bought Time", {}).get("date", {}).get("start", None)
        if not bought_time:
            print(f"⚠️ Warning: Missing 'Bought Time' for trade {symbol}, skipping...")
            continue
        
        existing_trades[(symbol, bought_time)] = page["id"]
    
    return existing_trades
existing_trades = fetch_existing_trades()
print(f"🔍 Found {len(existing_trades)} existing trades in Notion.")

# -----------------------------
# 👉 STEP 4: Function to Upload New Trades to Notion
# -----------------------------
failed_trades = []

def add_trade_to_notion(row):
    trade_key = (row["Symbol"], row["Bought Time"].isoformat())
    if trade_key in existing_trades:
        print(f"⏭️ Skipping duplicate trade: {trade_key}")
        return  # Skip duplicate trade
    
    try:
        notion.pages.create(
            parent={"database_id": DATABASE_ID},
            properties={
                "Quantity": {"number": row["Quantity"]},
                "Symbol": {"select": {"name": row["Symbol"]}},
                "Side": {"select": {"name": row["Side"]}},
                "Pnl": {"number": row["Pnl"] if not pd.isna(row["Pnl"]) else 0},
                "Pts": {"number": row["Pts"]},
                "Result": {"select": {"name": row["Result"]}},
                "Drt Category": {"select": {"name": row["Drt Category"]}},
                "Session": {"select": {"name": row["Session"]}},
                "ATR 1M": {"number": row["ATR 1M"] if not pd.isna(row["ATR 1M"]) else 0},
                "ATR 5M": {"number": row["ATR 5M"] if not pd.isna(row["ATR 5M"]) else 0},
                "Duration": {"number": row["Duration"] if not pd.isna(row["Duration"]) else 0},
                "Buy Price": {"number": row["Buy Price"] if not pd.isna(row["Buy Price"]) else 0},
                "Sell Price": {"number": row["Sell Price"] if not pd.isna(row["Sell Price"]) else 0},
                "Bought Time": {"date": {"start": row["Bought Time"].isoformat()}},
                "Sold Time": {"date": {"start": row["Sold Time"].isoformat()}},
            }
        )
        print(f"✅ Uploaded trade for {row['Symbol']} ({row['Side']})")
        time.sleep(0.5)  # Avoid API rate limits
    except Exception as e:
        print(f"❌ Error uploading {row['Symbol']} trade at {row['Bought Time']}: {e}")
        failed_trades.append(row.to_dict())  # Save failed trades

# -----------------------------
# 👉 STEP 5: Upload New Trades to Notion
# -----------------------------
print("🚀 Uploading new trades to Notion...")
for _, row in df.iterrows():
    add_trade_to_notion(row)

if failed_trades:
    failed_df = pd.DataFrame(failed_trades)
    failed_df.to_csv("failed_trades.csv", index=False)
    print(f"⚠️ Some trades failed to upload. Saved to failed_trades.csv")

print("🎉 All new trades uploaded successfully!")
