import sys; print(sys.version)
import streamlit as st
import pandas as pd
import yfinance as yf
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib import gridspec

# Set the title of the app
st.title('OO Swing Calls')

# Create an input field for the user to enter the stock symbol
stock_symbol = st.text_input("Enter a stock symbol", "AAPL")

# Download the historical data
data = yf.download(stock_symbol, period='1y')

# Calculate the MACD
exp12     = data['Close'].ewm(span=12, adjust=False).mean()
exp26     = data['Close'].ewm(span=26, adjust=False).mean()
macd      = exp12 - exp26
signal    = macd.ewm(span=9, adjust=False).mean()
histogram = macd - signal

# Identify local minima and maxima
window_size = 45  # Define the window size
local_minima = (data['Close'] == data['Close'].rolling(window=window_size, center=True).min())
local_maxima = (data['Close'] == data['Close'].rolling(window=window_size, center=True).max())

support_levels = data[local_minima]['Close']
resistance_levels = data[local_maxima]['Close']

# Calculate days from current day
current_day = data.index[-1]
support_days_from_current = (current_day - support_levels.index).days
resistance_days_from_current = (current_day - resistance_levels.index).days

# Convert to Series to use rank()
support_days_from_current = pd.Series(support_days_from_current, index=support_levels.index)
resistance_days_from_current = pd.Series(resistance_days_from_current, index=resistance_levels.index)

# Rank support and resistance levels
support_ranks = support_days_from_current.rank().astype(int)
resistance_ranks = resistance_days_from_current.rank().astype(int)

# Filter to get the top 2 highest-ranked support and resistance levels
top_support_levels = support_levels[support_ranks <= 2]
top_resistance_levels = resistance_levels[resistance_ranks <= 2]

# Create a new figure and an axes
fig = plt.figure(figsize=(10, 7))
gs = gridspec.GridSpec(2, 1, height_ratios=[2.5, 1])
ax0 = plt.subplot(gs[0])
ax1 = plt.subplot(gs[1], sharex=ax0)

# Plot the data and MACD lines
ax0.plot(data.index, data['Close'], label='Close')
ax0.set_ylabel('Price (USD)')
ax1.plot(data.index, macd, label='MACD', color='b')
ax1.plot(data.index, signal, label='Signal Line', color='r')
ax1.fill_between(data.index, histogram, 0, alpha=0.5, facecolor='orange', edgecolor='b')
ax1.set_ylabel('MACD')

# Plot horizontal lines for top support levels
for date, support in top_support_levels.items():
    ax0.axhline(support, color='green', linestyle='--', label='Support')
    rank = support_ranks.loc[date]
    ax0.annotate(f'{rank}', xy=(date, support), xytext=(10, 0), textcoords='offset points',
                bbox=dict(facecolor='white', edgecolor='none', boxstyle='round,pad=0.3'),
                color='black', ha='center', va='center')

# Plot horizontal lines for top resistance levels
for date, resistance in top_resistance_levels.items():
    ax0.axhline(resistance, color='red', linestyle='--', label='Resistance')
    rank = resistance_ranks.loc[date]
    ax0.annotate(f'{rank}', xy=(date, resistance), xytext=(10, 0), textcoords='offset points',
                bbox=dict(facecolor='white', edgecolor='none', boxstyle='round,pad=0.3'),
                color='black', ha='center', va='center')

# Find the point where MACD surpasses the Signal Line closest to the current day
crossover_points = (macd > signal) & (macd.shift(1) <= signal.shift(1))
if not crossover_points.empty:
    closest_crossover = crossover_points[crossover_points].index[-1]
    ax0.axvline(closest_crossover, color='purple', linestyle='--', label='MACD Crossover')

# Format the x-axis to display months
ax0.xaxis.set_major_locator(mdates.MonthLocator())
ax0.xaxis.set_major_formatter(mdates.DateFormatter('%b'))

# Display the legend
ax0.legend()
#ax1.legend()

# Remove x-axis label for the top subplot
#plt.setp(ax0.get_xticklabels(), visible=False)

# Adjust the spacing between the subplots
plt.subplots_adjust(hspace=0.4)

# Display the plot in Streamlit
st.pyplot(fig)
