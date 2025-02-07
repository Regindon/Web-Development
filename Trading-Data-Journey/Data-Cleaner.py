import pandas as pd
import re
import os
import yfinance as yf

# -----------------------------
# 📌 STEP 1: Load & Clean Trade Data
# -----------------------------

# Define file path
trade_data_path = os.path.join("Trade-Data", "trades.csv")

# Check if the file exists before proceeding
if not os.path.exists(trade_data_path):
    print(f"❌ Error: Trades CSV file not found at {trade_data_path}")
    exit()

# Load the CSV file
df = pd.read_csv(trade_data_path)

# Remove unnecessary columns
df = df.drop(columns=["_priceFormat", "_priceFormatType", "_tickSize"], errors="ignore")

# Extract only the main contract symbol (removing last 2 characters)
df["symbol"] = df["symbol"].apply(lambda x: x[:-2])

# Determine if the trade is Long or Short
df["Side"] = df.apply(lambda row: "Long" if row["buyFillId"] < row["sellFillId"] else "Short", axis=1)

# Define contract fee structure
# fee_dict = {"NQ": 4.68/2, "MNQ": 1.54/2, "MYM": 2.2/2}
fee_dict = {"NQ": 4.73/2, "MNQ": 1.57/2, "MYM": 2.2/2}


# Modify PnL calculation to deduct fees per contract type
def classify_pnl(pnl, symbol, quantity, pts):
    numeric_pnl = float(re.sub(r"[\$\(\)]", "", str(pnl)))  # Ensure PnL is a string before regex
    if "(" in str(pnl):
        numeric_pnl = -abs(numeric_pnl)  # Convert losses to negative

    # Apply fees based on contract type
    fee_per_qty = fee_dict.get(symbol[:3], 0)  # Use dictionary lookup
    total_fees = quantity * fee_per_qty  # Deduct total fees
    adjusted_pnl = numeric_pnl - total_fees  # Subtract fees from PnL

    # Determine Result (Win/Loss/Breakeven)
    if pts > 0:
        return "Win", adjusted_pnl
    elif pts < 0:
        return "Loss", adjusted_pnl
    else:
        return "Breakeven", 0

    

df["Pts"] = df.apply(lambda row: 0 if row["sellPrice"] == row["buyPrice"] else (row["sellPrice"] - row["buyPrice"]) if row["sellPrice"] > row["buyPrice"] else -(row["buyPrice"] - row["sellPrice"]), axis=1)

# Apply the modified function to calculate Pnl with fees
df[["Result", "Pnl"]] = df.apply(lambda row: pd.Series(classify_pnl(row["pnl"], row["symbol"], row["qty"],row["Pts"])), axis=1)


# Convert timestamps to datetime
df["boughtTimestamp"] = pd.to_datetime(df["boughtTimestamp"], format="%m/%d/%Y %H:%M:%S")
df["soldTimestamp"] = pd.to_datetime(df["soldTimestamp"], format="%m/%d/%Y %H:%M:%S")

# Determine the correct trade entry timestamp (earliest timestamp)
df["Trade Entry Time"] = df.apply(lambda row: row["boughtTimestamp"] if row["Side"] == "Long" else row["soldTimestamp"], axis=1)

# Function to convert duration into total seconds
def convert_duration(duration):
    if isinstance(duration, float) or pd.isna(duration):  # Handle NaN or unexpected floats
        return None  # Return None for invalid/missing values
    
    match = re.match(r"(?:(\d+)min\s*)?(\d+)sec", duration)
    if match:
        minutes = int(match.group(1)) if match.group(1) else 0
        seconds = int(match.group(2))
        return (minutes * 60) + seconds  # Convert to total seconds
    
    return None  # If format is wrong, return None

# Apply the function safely
df["duration"] = df["duration"].astype(str).apply(convert_duration)  


# Categorize Duration into Groups
def categorize_duration(sec):
    if sec <= 30:
        return "0-30 sec"
    elif sec <= 120:
        return "30-120 sec"
    elif sec <= 300:
        return "2-5 min"
    else:
        return "5+ min"

df["Duration Category"] = df["duration"].apply(categorize_duration)

# Categorize Session based on market opening time (17:30:00)
def categorize_session(timestamp):
    market_open = timestamp.replace(hour=17, minute=30, second=0)  # Market opens at 17:30:00
    minutes_since_open = (timestamp - market_open).total_seconds() / 60  # Convert to minutes

    if 0 <= minutes_since_open < 30:
        return "0-30 min"
    elif 30 <= minutes_since_open < 60:
        return "30-60 min"
    elif 60 <= minutes_since_open < 120:
        return "1-2 hour"
    else:
        return "2+ hour"

df["Session"] = df["Trade Entry Time"].apply(categorize_session)

# Calculate "Point" as the difference between buyPrice and sellPrice
df["Point"] = df.apply(lambda row: -abs(row["sellPrice"] - row["buyPrice"]) if row["Result"] == "Loss" else abs(row["sellPrice"] - row["buyPrice"]), axis=1)

# -----------------------------
# 📌 STEP 2: Merge Trades Within 5 Seconds (Improved Logic)
# -----------------------------

def clean_pnl(pnl, symbol, quantity):
    fee_per_qty = fee_dict.get(symbol[:3], 0)
    total_fees = quantity * fee_per_qty
    numeric_pnl = float(re.sub(r"[\$\(\)]", "", str(pnl))) * (-1 if "(" in str(pnl) else 1)
    return round(numeric_pnl - total_fees, 2)

def get_multiplier(symbol):
    """Return the multiplier based on contract type (NQ, MNQ, MYM)."""
    if symbol.startswith("NQ"):
        return 20
    elif symbol.startswith("MNQ"):
        return 2
    elif symbol.startswith("MYM"):
        return 0.5
    return 1  # Default fallback

merged_trades = []
previous_trade = None

for _, row in df.iterrows():
    if previous_trade is not None:
        entry_diff = (row["Trade Entry Time"] - previous_trade["Trade Entry Time"]).total_seconds()
        same_position = row["Side"] == previous_trade["Side"]
        same_contract = row["symbol"][:2] == previous_trade["symbol"][:2]  # ✅ Check contract type

        # Merge trades if all conditions are met
        if same_position and same_contract and entry_diff <= 5 and row["duration"] > entry_diff and previous_trade["duration"] > entry_diff:
            # ✅ Sum qty (Quantity)
            previous_trade["qty"] += row["qty"]
            # ✅ Merge Points (Use 'Point' instead of 'Pts')
            previous_trade["Point"] = max(previous_trade["Point"], row["Point"])
            # ✅ Fix PnL using formula
            multiplier = get_multiplier(previous_trade["symbol"])
            previous_trade["Pnl"] = previous_trade["qty"] * previous_trade["Point"] * multiplier - ((previous_trade["qty"]+row["qty"]) * fee_dict.get(previous_trade["symbol"][:3], 0))
            continue  # Skip adding the current row as it's merged

    # Ensure PnL is converted to numeric before adding to merged trades
    row["Pnl"] = clean_pnl(row["pnl"], row["symbol"], row["qty"])  # ✅ Directly use "Pnl" to prevent later overwrites
    merged_trades.append(row.to_dict())  # Add trade to list
    previous_trade = merged_trades[-1]  # Update reference to last added trade

df = pd.DataFrame(merged_trades)  # Convert back to DataFrame
# -----------------------------
# 📌 STEP 3: Fetch ATR Data from Yahoo Finance
# -----------------------------

ticker_symbol = "MNQ=F"  # Change to "MNQ=F" if you're trading Micro Nasdaq Futures

# Fetch historical ATR data
futures_data = yf.Ticker(ticker_symbol)
atr_df = futures_data.history(period="7d", interval="1m")
atr_df_5m = futures_data.history(period="7d", interval="5m")

# Reset index
atr_df = atr_df.reset_index()
atr_df_5m = atr_df_5m.reset_index()

# Calculate ATR (14-period)
atr_df["ATR 1M"] = (atr_df["High"] - atr_df["Low"]).rolling(window=14).mean()
atr_df_5m["ATR 5M"] = (atr_df_5m["High"] - atr_df_5m["Low"]).rolling(window=14).mean()

# Convert ATR timestamps to UTC and adjust for the 8-hour delay
atr_df["Datetime"] = pd.to_datetime(atr_df["Datetime"]).dt.tz_localize(None) + pd.Timedelta(hours=8)
atr_df_5m["Datetime"] = pd.to_datetime(atr_df_5m["Datetime"]).dt.tz_localize(None) + pd.Timedelta(hours=8)

print("✅ Fetched ATR data successfully!")

# -----------------------------
# 📌 STEP 4: Merge ATR with Trade Data
# -----------------------------

df["Trade Entry Time"] = pd.to_datetime(df["Trade Entry Time"])

df = pd.merge_asof(df.sort_values("Trade Entry Time"), atr_df[["Datetime", "ATR 1M"]].sort_values("Datetime"),
                   left_on="Trade Entry Time", right_on="Datetime", direction="backward").drop(columns=["Datetime"])

df = pd.merge_asof(df.sort_values("Trade Entry Time"), atr_df_5m[["Datetime", "ATR 5M"]].sort_values("Datetime"),
                   left_on="Trade Entry Time", right_on="Datetime", direction="backward").drop(columns=["Datetime"])

df["ATR 1M"] = df["ATR 1M"].round(1)
df["ATR 5M"] = df["ATR 5M"].round(1)

# -----------------------------
# 📌 STEP 5: Rename Columns & Save in Correct Order
# -----------------------------

df = df.rename(columns={"qty": "Quantity", "symbol": "Symbol", "duration": "Duration",
                        "Duration Category": "Drt Category", "buyPrice": "Buy Price", "sellPrice": "Sell Price",
                        "boughtTimestamp": "Bought Time", "soldTimestamp": "Sold Time"})

df = df[["Quantity", "Symbol", "Side", "Pnl", "Pts", "Result", "Drt Category", "Session", "ATR 1M", "ATR 5M",
         "Duration", "Buy Price", "Sell Price", "Bought Time", "Sold Time"]]


# ✅ Print Debug Output Before Saving
print("✅ Final Trade Data Before Saving:")
df["Pnl"] = df.apply(lambda row: clean_pnl(row["Pnl"], row["Symbol"], row["Quantity"]), axis=1)
print(df[["Quantity", "Symbol", "Side", "Pnl", "Pts"]].head())  # Check PnL before saving

# Convert "Bought Time" to datetime if it's not already
df["Bought Time"] = pd.to_datetime(df["Bought Time"])

# Extract the first and last trade dates
first_trade_day = df["Bought Time"].min().strftime("%d.%m.%Y")
last_trade_day = df["Bought Time"].max().strftime("%d.%m.%Y")

# Generate the filename with the correct date range
output_filename = f"Cleaned_Trades_{first_trade_day}-{last_trade_day}.csv"
output_file_path = os.path.join("Trade-Data", output_filename)

# Save the cleaned data
df.to_csv(output_file_path, index=False)

print(f"✅ Cleaned, Merged & Ordered trade data saved to: {output_file_path}")
print(df.head())