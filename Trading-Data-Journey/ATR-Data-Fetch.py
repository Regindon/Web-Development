import yfinance as yf

# Fetch 1-minute historical data for E-mini Nasdaq 100 futures
nq = yf.Ticker("NQ=F")  # Use "MNQ=F" for Micro Nasdaq
nq_data = nq.history(period="7d", interval="1m")  # Last 7 days, 1-minute data

# Calculate ATR (14-period)
nq_data["ATR"] = nq_data["High"].rolling(window=14).mean() - nq_data["Low"].rolling(window=14).mean()

# Display latest ATR values
print(nq_data.tail())
