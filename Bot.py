import tkinter as tk
from tkinter import ttk, messagebox
import json
import time
import threading
import random
import alpaca_trade_api as tradeapi
import google.generativeai as genai

DATA_FILE = 'equities.json'

key = "PKI8CTPYSJCSYQMWQO3O"
secret_key="abt12oNpdtGU1fs2SQ1bACReT5JH8cwMMIkpKN8g"
BASE_URL = "https://paper-api.alpaca.markets/"
api = tradeapi.REST(key, secret_key, BASE_URL, api_version='v2')
def fetch_portfolio():
    positions = api.list_positions()
    portfolio = []
    for position in positions:
        portfolio.append({
            "symbol": position.symbol,
            "qty": position.qty,
            "entry_price": position.avg_entry_price,
            "current_price": position.current_price,
            "unrealized_pl": position.unrealized_pl,
            "side" : 'long'
        })
    return portfolio

def fetch_open_orders():
    orders = api.list_orders(status='open')
    open_orders = []
    for order in orders:
        open_orders.append({
            "symbol": order.symbol,
            "qty": order.qty,
            "side": order.side,
            "limit_price": order.limit_price,
        })
    return open_orders

def fetch_mock_API(symbol):
    return {
        "price": 100
    }
    
genai.configure(api_key="AIzaSyAqukhpb05XCD58w4Kiv2hzJpKSIxrD_qI")

def analyze_message(message):
    portfolio_data = fetch_portfolio()
    open_orders = fetch_open_orders()
    
    pre_prompt = f"""
You are an AI portfolio manager responsible for analyzing my portfolio.
Your tasks are:
1. Evaluate risk exposure.
2. Analyze open limit orders and their potential impact.
3. Provide insights on the portfolio's performance.
4. Speculate on the market outlook based on current conditions.

Here is my portfolio: {portfolio_data}
Here are my open orders: {open_orders}
"""

    model = genai.GenerativeModel("gemini-1.5-flash")
    chat = model.start_chat(history=[])
    response = chat.send_message(f"{pre_prompt}\n\nUser Question: {message}")
    
    return response.text


class TradingBotGUI:
    
    def __init__(self, root):
        self.root = root
        self.root.title("Trading Bot")
        self.equities = self.load_equities()
        self.system_running = False
        
        
        self.form_frame=tk.Frame(root)
        self.form_frame.pack(pady=10)
        
        
        
        #form to add new equity to our bot
        tk.Label(self.form_frame, text="Symbol:").grid(row=0,column=0)
        self.symbol_entry = tk.Entry(self.form_frame)
        self.symbol_entry.grid(row=0, column=1)
        
        tk.Label(self.form_frame, text = "levels:").grid(row=0, column=2)
        self.levels_entry = tk.Entry(self.form_frame)
        self.levels_entry.grid(row=0, column=3)
        
        tk.Label(self.form_frame, text="Drawdown%:").grid(row=0, column=4)
        self.drawdown_entry = tk.Entry(self.form_frame)
        self.drawdown_entry.grid(row=0, column=5)
        
        self.add_button = tk.Button(self.form_frame, text="Add Equity", command=self.add_equity)
        self.add_button.grid(row=0, column=6)
        
        # Table to track the traded equities
        self.tree = ttk.Treeview(root, columns=("Symbol", "Position", "entry price","Levels", "Status"), show='headings')
        for col in ["Symbol", "Position", "entry price", "Levels", "Status"]:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=120)
        self.tree.pack(pady=10)
        
        
        #Buttons to control bot
        self.toggle_system_button = tk.Button(root, text="Toggle selected system", command=self.toggle_selected_system)
        self.toggle_system_button.pack(pady=5)
        
        self.remove_button = tk.Button(root, text="Remove selected equity", command=self.remove_selected_equity)
        self.remove_button.pack(pady=5)
        
        
        #AI component
        self.chatgpt_frame = tk.Frame(root)
        self.chatgpt_frame.pack(pady=10)
        
        self.chat_input = tk.Entry(self.chatgpt_frame, width=50)
        self.chat_input.grid(row=0, column=0, padx=5)
        
        self.send_button = tk.Button(self.chatgpt_frame, text="Send", command=self.send_message)
        self.send_button.grid(row=0, column=1)
        
        self.chat_output = tk.Text(root, height=5, width=60,state=tk.DISABLED)
        self.chat_output.pack()
        
        #load saved data
        self.refresh_table()
        
        #auto refreshing
        self.running = True
        self.auto_update_threat = threading.Thread(target=self.auto_update, daemon=True)
        self.auto_update_threat.start()
        
    def add_equity(self):
        symbol = self.symbol_entry.get().upper()
        levels = self.levels_entry.get()
        drawdown = self.drawdown_entry.get()
        
        if not symbol or not levels.isdigit() or not drawdown.replace('.', '', 1).isdigit():
            messagebox.showerror("Error", "invalid input")
            return
        
        levels = int(levels)
        drawdown = float(drawdown) / 100
        entry_price = self.fetch_alpaca_data(symbol)["price"]
        
        level_prices = {i+1: round(entry_price * (1-drawdown*(i+1)),2) for i in range(levels)}

        
        self.equities[symbol] = {
            "position":0,
            "entry_price": entry_price,
            "levels": level_prices,
            "drawdown": drawdown,
            "status": "Off"
        }
        
        
        self.save_equities()
        self.refresh_table()
        
    def toggle_selected_system(self):
        selected_item = self.tree.selection()
        if not selected_item:
            messagebox.showwarning("Warning", "No equity selected")
            return
        
        for item in selected_item:
            symbol = self.tree.item(item)["values"][0]
            self.equities[symbol]['status'] = "On" if self.equities[symbol]['status'] == "Off" else "Off"
            
        self.save_equities()
        self.refresh_table()
    
    def remove_selected_equity(self):
        selected_item = self.tree.selection()
        if not selected_item:
            messagebox.showwarning("Warning", "No equity selected")
            return
        
        for item in selected_item:
            symbol = self.tree.item(item)["values"][0]
            if symbol in self.equities:
                del self.equities[symbol]
        
        self.save_equities()
        self.refresh_table()
        
    def send_message(self):
        message = self.chat_input.get()
        if not message:
            return
        
        response = analyze_message(message)
        
        
        self.chat_output.config(state=tk.NORMAL)
        self.chat_output.insert(tk.END, f"You: {message}\n")
        self.chat_output.insert(tk.END, f"Bot: {response}\n")
        self.chat_output.config(state=tk.DISABLED)
        self.chat_input.delete(0, tk.END)
        
        
    def fetch_alpaca_data(self, symbol):
        try:
            barset = api.get_latest_trade(symbol)
            return{"price":barset.price}
        except Exception as e:
            return {"price":-1}
        
    
    def check_existing_orders(self,symbol,price):
        try:
            orders = api.list_orders(status='open', symbols = symbol)
            for order in orders:
                if float(order.limit_price) == price:
                    return True
        except Exception as e:
            print(f"Error checking existing orders for {symbol}: {e}")
        return False
    

    def get_max_entry_price(self, symbol):
        try:
            orders=api.list_orders(status='filled', limit =50)
            prices = [float(order.filled_avg_price) for order in orders if order.filled_avg_price and order.symbol == symbol]
            if prices:
                return max(prices)
            else:
                latest_trade = api.get_latest_trade(symbol)
                return latest_trade.price
        except Exception as e:
            messagebox.showerror("Error", f"Failed to get max entry price for {symbol}: {e}")
            return 0
        
    def has_any_open_orders(self, symbol):
        try:
            orders = api.list_orders(status='open', symbols=[symbol])
            return len(orders) > 0
        except Exception as e:
            print(f"Error checking open orders for {symbol}: {e}")
            return False

    def trade_systems(self):
        for symbol, data in self.equities.items():
            if data['status'] == "On":
                position_exists = False

                
                try:
                    position = api.get_position(symbol)
                    entry_price = self.get_max_entry_price(symbol)
                    position_exists = True
                except Exception as e:
                    if self.has_any_open_orders(symbol):
                        print(f"Open order exist for {symbol}, skipping new market order.")
                        entry_price = self.get_max_entry_price(symbol)
                        
                    else:
                        api.submit_order(
                            symbol=symbol,
                            qty=1,
                            side="buy",
                            type="market",
                            time_in_force="gtc"
                        )
                        messagebox.showinfo("Order Placed", f"Iniital Order Placed for {symbol}")
                        time.sleep(2)
                        entry_price = self.get_max_entry_price(symbol)
                print(entry_price)
                
                if entry_price <= 0:
                    messagebox.showerror("Error", f"Failed to fetch entry price for {symbol}. Skipping.")
                    continue
                
                level_prices = {}
                for i in range(len(data['levels'])):
                    price = round(entry_price * (1 - data['drawdown'] * (i+1)), 2)
                    if price > 0:
                        level_prices[i+1] = price
                    else:
                        print(f"Skipping invalid price {price} at level {i+1} for {symbol}")

                
                existing_levels = self.equities.get(symbol, {}).get('levels', {})
                for level, price in level_prices.items():
                    if level not in existing_levels and -level not in existing_levels:
                        existing_levels[level] = price
                        
                self.equities[symbol]['entry_price'] = entry_price
                self.equities[symbol]['levels'] = existing_levels
                self.equities[symbol]['position'] = 1
                
                for level,prices in level_prices.items():
                    if level in self.equities[symbol]['levels']:
                        if not self.check_existing_orders(symbol, prices):
                            self.place_order(symbol, prices, level)
                        
                
            self.save_equities()
            self.refresh_table()
            
        else:
            return
        
    def place_order(self, symbol, price, level):
        if -level in self.equities[symbol]['levels'] or '-1' in self.equities[symbol]['levels'].keys():
            return
        
        try:
            api.submit_order(
                symbol=symbol,
                qty=1,
                side='buy',
                type='limit',
                time_in_force='gtc',
                limit_price=price
            )
            self.equities[symbol]['levels'][-level] = price
            del self.equities[symbol]['levels'][level]
            print(f"Placed order for {symbol}@{price}")
        except Exception as e:
            messagebox.showerror("Order Error", f"Error placing order {e}")
    
            
        
    def refresh_table(self):
        for row in self.tree.get_children():
            self.tree.delete(row)
            
        for symbol, data in self.equities.items():
            self.tree.insert("", "end", values=(
                symbol,
                data["position"],
                data["entry_price"],
                str(data["levels"]),
                data["status"]
                ))
        
        
    def auto_update(self):
        while self.running:
            time.sleep(5)
            self.trade_systems()
    
    
    def save_equities(self):
        with open(DATA_FILE, 'w') as f:
            json.dump(self.equities, f)
            
    def load_equities(self):
        try:
            with open(DATA_FILE, 'r') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return {} 
        
    def on_close(self):
        self.running = False
        self.save_equities()
        self.root.destroy()
        
if __name__ == "__main__":
    root = tk.Tk()
    app = TradingBotGUI(root)
    root.protocol("WM_DELETE_WINDOW", app.on_close)
    root.mainloop()
            