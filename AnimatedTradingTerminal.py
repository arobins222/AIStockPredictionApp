"""
=========================================================
AI Trading Terminal
Version 4.0 (Multi-Stock Ticker Edition)
Copyright (c) 2026 Drew Robinson
All Rights Reserved.
=========================================================
"""

import tkinter as tk
from tkinter import ttk, filedialog
from tkcalendar import DateEntry
import threading
import pandas as pd
import numpy as np
import yfinance as yf
import matplotlib
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
from datetime import datetime, timedelta

matplotlib.use("TkAgg")


# ================= Indicators =================

def extract_close_series(df):
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    close = df.get("Close")
    if isinstance(close, pd.DataFrame):
        close = close.iloc[:, 0]
    return close.astype(float)


def calculate_rsi(prices, period=14):
    delta = prices.diff()
    gain = delta.clip(lower=0).fillna(0)
    loss = -delta.clip(upper=0).fillna(0)
    avg_gain = gain.rolling(period).mean()
    avg_loss = loss.rolling(period).mean()
    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))


def moving_average(prices, window=5):
    return prices.rolling(window).mean()


def forecast_future(prices, days=15):
    prices = prices.dropna()
    if len(prices) < 10:
        return None, None, None, None

    x = np.arange(len(prices))
    y = prices.to_numpy()

    slope, intercept = np.polyfit(x, y, 1)
    future_x = np.arange(len(prices), len(prices) + days)
    future_y = slope * future_x + intercept

    std = np.std(y - (slope * x + intercept))
    upper = future_y + std
    lower = future_y - std

    direction = "▲ Bullish" if slope > 0 else "▼ Bearish"
    return future_y, upper, lower, direction


# ================= Application =================

class TradingTerminal(tk.Tk):
    def __init__(self, stocks):
        super().__init__()

        self.title("AI Trading Terminal v4.0 © 2026 Drew Robinson")
        self.geometry("1550x950")
        self.configure(bg="#111111")

        self.stocks = stocks
        self.selected_stock = tk.StringVar(value=stocks[0])
        self.date_range = tk.StringVar(value="6mo")
        self.search_symbol = tk.StringVar()

        self.df_cache = {}
        self.running = True
        self.loading = False

        self.create_widgets()

        self.after(300, self.fetch_all_data_async)
        self.start_ticker()

    # ================= UI =================

    def create_widgets(self):

        notebook = ttk.Notebook(self)
        notebook.pack(fill=tk.BOTH, expand=True)

        self.main_frame = tk.Frame(notebook, bg="#111111")
        self.about_frame = tk.Frame(notebook, bg="#111111")

        notebook.add(self.main_frame, text="Terminal")
        notebook.add(self.about_frame, text="About")

        top = tk.Frame(self.main_frame, bg="#111111")
        top.pack(fill=tk.X, pady=5)

        ttk.OptionMenu(top, self.selected_stock,
                       self.selected_stock.get(),
                       *self.stocks,
                       command=lambda x: self.update_graph()).pack(side=tk.LEFT, padx=5)

        search_entry = ttk.Entry(top, textvariable=self.search_symbol, width=10)
        search_entry.pack(side=tk.LEFT, padx=5)
        search_entry.bind("<Return>", self.search_stock)

        ttk.Button(top, text="Search", command=self.search_stock).pack(side=tk.LEFT)

        ttk.OptionMenu(top, self.date_range,
                       self.date_range.get(),
                       "30d", "60d", "6mo", "1y",
                       command=lambda x: self.fetch_all_data_async()).pack(side=tk.LEFT, padx=5)

        today = datetime.today()
        six_months_ago = today - timedelta(days=180)

        self.start_picker = DateEntry(top, width=12, date_pattern='yyyy-mm-dd')
        self.start_picker.set_date(six_months_ago)
        self.start_picker.pack(side=tk.LEFT, padx=5)

        self.end_picker = DateEntry(top, width=12, date_pattern='yyyy-mm-dd')
        self.end_picker.set_date(today)
        self.end_picker.pack(side=tk.LEFT, padx=5)

        ttk.Button(top, text="Apply Dates",
                   command=self.update_graph).pack(side=tk.LEFT)

        ttk.Button(top, text="Export Excel",
                   command=self.export_excel).pack(side=tk.RIGHT, padx=5)

        ttk.Button(top, text="Export PNG",
                   command=self.export_png).pack(side=tk.RIGHT)

        # Graph
        self.fig = Figure(figsize=(11, 6), dpi=100, facecolor="#111111")
        self.ax = self.fig.add_subplot(111)
        self.ax.set_facecolor("#1e1e1e")

        self.canvas = FigureCanvasTkAgg(self.fig, master=self.main_frame)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        # Bottom Ticker
        self.ticker_canvas = tk.Canvas(self,
                                       height=40,
                                       bg="#0f0f0f",
                                       highlightthickness=0)
        self.ticker_canvas.pack(side=tk.BOTTOM, fill=tk.X)

        self.build_about_tab()

    # ================= About (Restored Full Info) =================

    def build_about_tab(self):

        about_text = """
AI Trading Terminal
© 2026 Drew Robinson
All Rights Reserved.

=================================================
TECHNICAL OVERVIEW
=================================================

This application combines technical indicators
with statistical forecasting models to provide
trend analysis and predictive insight.

-------------------------------------------------
1) Relative Strength Index (RSI)
-------------------------------------------------

RS  = Average Gain / Average Loss
RSI = 100 - (100 / (1 + RS))

RSI < 30  → Oversold (Potential Buy)
RSI > 70  → Overbought (Potential Sell)

-------------------------------------------------
2) Moving Average (MA)
-------------------------------------------------

MA(n) = (P₁ + P₂ + ... + Pₙ) / n

Short MA (5)  → Short-term trend
Long MA (20) → Medium-term trend

-------------------------------------------------
3) Linear Regression Forecast
-------------------------------------------------

ŷ = mx + b

m = slope
b = intercept

Future projection is estimated using
least-squares regression.

-------------------------------------------------
4) Confidence Interval
-------------------------------------------------

ŷ ± σ

σ = standard deviation of regression residuals

This creates the shaded prediction band.

=================================================
BEGINNER GUIDE
=================================================

• Solid Line → Historical closing price
• MA Lines → Trend smoothing
• ▲ Green → Oversold (Possible Buy)
• ▼ Red → Overbought (Possible Sell)
• Dashed Line → Future projection
• Shaded Band → Uncertainty range
• Bottom Ticker → Live snapshot of all stocks

=================================================
DISCLAIMER
=================================================

This software is for educational and analytical
purposes only. It does not constitute financial
advice or trading recommendations.
"""

        text = tk.Text(self.about_frame,
                       bg="#111111",
                       fg="white",
                       font=("Consolas", 11),
                       borderwidth=0,
                       highlightthickness=0)

        text.insert("1.0", about_text)
        text.config(state="disabled")
        text.pack(fill=tk.BOTH, expand=True, padx=40, pady=40)

    # ================= Data =================

    def search_stock(self, event=None):
        symbol = self.search_symbol.get().upper().strip()
        if symbol and symbol not in self.stocks:
            self.stocks.append(symbol)
            self.selected_stock.set(symbol)
            self.fetch_all_data_async()

    def fetch_all_data_async(self):
        if self.loading:
            return
        self.loading = True
        threading.Thread(target=self.fetch_all_data, daemon=True).start()

    def fetch_all_data(self):
        for stock in self.stocks:
            df = yf.download(stock,
                             period=self.date_range.get(),
                             interval="1d",
                             progress=False)
            if df.empty:
                continue

            close = extract_close_series(df)
            df['Close'] = close
            df['RSI'] = calculate_rsi(close)
            df['MA5'] = moving_average(close, 5)
            df['MA20'] = moving_average(close, 20)

            self.df_cache[stock] = df

        self.loading = False
        self.after(0, self.update_graph)

    # ================= Filtering =================

    def get_filtered_data(self, stock):
        df = self.df_cache.get(stock)
        if df is None:
            return None

        start = pd.Timestamp(self.start_picker.get_date())
        end = pd.Timestamp(self.end_picker.get_date())

        filtered = df[(df.index >= start) & (df.index <= end)]
        return filtered if not filtered.empty else df

    # ================= Graph =================

    def update_graph(self):
        stock = self.selected_stock.get()
        df = self.get_filtered_data(stock)
        if df is None:
            return

        self.ax.clear()
        self.ax.grid(True, alpha=0.2)

        self.ax.plot(df.index, df['Close'], label="Close")

        buys = df[df['RSI'] < 30]
        sells = df[df['RSI'] > 70]

        if not buys.empty:
            self.ax.scatter(buys.index, buys['Close'],
                            marker='^', color="green", s=90, label="Buy ▲")
        if not sells.empty:
            self.ax.scatter(sells.index, sells['Close'],
                            marker='v', color="red", s=90, label="Sell ▼")

        future, upper, lower, direction = forecast_future(df['Close'])
        if future is not None:
            last_date = df.index[-1]
            future_dates = pd.date_range(start=last_date,
                                         periods=len(future)+1,
                                         freq='B')[1:]
            self.ax.plot(future_dates, future,
                         linestyle="--",
                         label=f"Forecast {direction}")
            self.ax.fill_between(future_dates, lower, upper, alpha=0.2)

        self.ax.legend()
        self.canvas.draw()

    # ================= Multi-Stock Ticker =================

    def start_ticker(self):
        self.ticker_x = 0
        self.after(50, self.update_ticker)

    def update_ticker(self):
        self.ticker_canvas.delete("all")

        ticker_text = ""

        for stock in self.stocks:
            df = self.df_cache.get(stock)
            if df is None or len(df) < 2:
                continue

            last = float(df['Close'].iloc[-1])
            prev = float(df['Close'].iloc[-2])
            change = ((last - prev) / prev) * 100
            rsi = float(df['RSI'].iloc[-1])

            if rsi < 30:
                icon = "⚡"
            elif change > 0:
                icon = "▲"
            else:
                icon = "▼"

            ticker_text += f"  {stock} ${last:.2f} {change:+.2f}% {icon}   "

        width = self.winfo_width()
        self.ticker_canvas.create_text(width - self.ticker_x,
                                       20,
                                       text=ticker_text,
                                       fill="white",
                                       font=("Segoe UI", 12),
                                       anchor="w")

        self.ticker_x += 2
        if self.ticker_x > width + 1000:
            self.ticker_x = 0

        self.after(50, self.update_ticker)

    # ================= Export =================

    def export_png(self):
        file = filedialog.asksaveasfilename(defaultextension=".png")
        if file:
            self.fig.savefig(file)

    def export_excel(self):
        stock = self.selected_stock.get()
        df = self.get_filtered_data(stock)
        if df is None:
            return
        file = filedialog.asksaveasfilename(defaultextension=".xlsx")
        if file:
            df.to_excel(file)


# ================= Run =================

if __name__ == "__main__":
    stocks = [
        "AAPL","MSFT","GOOG","TSLA","NVDA","AMZN","META","AMD",
        "SPY","QQQ","NFLX","BRK-B","JPM","XOM","V","BAC"
    ]

    app = TradingTerminal(stocks)
    app.mainloop()