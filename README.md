Trading Bot with Alpaca and Gemini APIs

This is a Python trading bot with a Tkinter GUI that connects to:

Alpaca API for placing real-time stock trades (market & limit orders).

Gemini (Google Generative AI) API for portfolio analysis.

Features

Add equities to your portfolio.

Toggle trading systems on/off.

Place market and limit orders based on strategy.

Get portfolio insights using AI.

Runs continuously and updates in the GUI.

Requirements

Python 3.8 or newer

alpaca_trade_api Python package

google.generativeai Python package

Tkinter (comes with Python)

Setup

Make sure you have Python installed.

Install dependencies by running: pip install alpaca-trade-api google-generativeai

Put your Alpaca API keys and Gemini API key in the script where needed.

Running

Run the main Python script in VS Code or your terminal.

The GUI will open, letting you add stocks, toggle systems, and monitor trades.

Notes

You need active Alpaca API keys with trading permissions.

The bot uses threading to run in the background smoothly.

Check your API key security; don’t share them publicly.
