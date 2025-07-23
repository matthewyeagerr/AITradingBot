import tkinter as tk
from tkinter import ttk, messagebox
import time
import threading
import alpaca_trade_api as tradeapi
import google.generativeai as genai


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
        self.equities = {}
        self.system_running = False
        
        self.account_value=tk.Label(root, text=f"Account Value: $0.00", font=("Arial", 14))
        self.account_value.pack(pady=5)
        
        self.pnl_value = tk.Label(root, text="Open PnL: $0.00")
        self.pnl_value.pack(pady=2)

        
        self.sync_with_alpaca()
        self.update_account_value()
    
        
        
        
        
        self.form_frame=tk.Frame(root)
        self.form_frame.pack(pady=10)
        
        
        
        
        
        #form to add new equity to our bot
        tk.Label(self.form_frame, text="Symbol:").grid(row=0,column=0)
        self.symbol_entry = tk.Entry(self.form_frame)
        self.symbol_entry.grid(row=0, column=1)
        
        tk.Label(self.form_frame, text="Qty").grid(row=0, column=2)
        self.qty_entry = tk.Entry(self.form_frame)
        self.qty_entry.grid(row=0, column=3)
        
        
        
        self.add_button = tk.Button(self.form_frame, text="Add Equity", command=self.add_equity)
        self.add_button.grid(row=0, column=6)
        
        self.sell_button = tk.Button(self.form_frame, text="Sell equity", command=self.sell_equity)
        self.sell_button.grid(row=0, column=7)

        
        self.tree = ttk.Treeview(root, columns=("Symbol", "Position", "PnL", "entry price", "total value"), show='headings')
        for col in ["Symbol", "Position", "PnL", "entry price", "total value"]:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=120)
        self.tree.pack(pady=10)
        
        self.tree.tag_configure("pnl_positive", background="green")
        self.tree.tag_configure("pnl_negative", background="red")

        #AI component
        self.chatgpt_frame = tk.Frame(root)
        self.chatgpt_frame.pack(pady=10)
        
        self.chat_input = tk.Entry(self.chatgpt_frame, width=50)
        self.chat_input.grid(row=0, column=0, padx=5)
        
        self.send_button = tk.Button(self.chatgpt_frame, text="Send", command=self.send_message)
        self.send_button.grid(row=0, column=1)
        
        self.chat_output = tk.Text(root, height=15, width=60,state=tk.DISABLED)
        self.chat_output.pack()

        
        #load saved data
        self.refresh_table()
        
        #auto refreshing
        self.running = True
        self.auto_update_threat = threading.Thread(target=self.auto_update, daemon=True)
        self.auto_update_threat.start()
        
    def update_account_value(self):
        try:
            account = api.get_account()
            value = float(account.equity)
            pnl = self.get_open_pnl()
            self.account_value.config(text=f"Account Value: ${value:,.2f}")
            self.pnl_value.config(text=f"Open PnL: ${pnl:,.2f}")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to fetch account value: {e}")
            self.pnl_value.config(text="Open PnL: $0.00")
            
    def get_open_pnl(self):
        try:
            positions=api.list_positions()
            total_pnl = 0.0
            for position in positions:
                total_pnl += float(position.unrealized_pl)
            return total_pnl
        except Exception as e:
            messagebox.showerror("Error", f"Failed to fetch open PnL: {e}")
            return 0.0
        
    def add_equity(self):
        symbol = self.symbol_entry.get().upper()
        
        if not symbol:
            messagebox.showerror("Error", "invalid input")
            return
        
        entry_price = self.fetch_alpaca_data(symbol)["price"]
        
        qty = self.qty_entry.get()
        if not qty.isdigit() or int(qty) <= 0:
            messagebox.showerror("Error", "Invalid quantity")
            return
        qty = int(qty)
        
        if symbol in self.equities:
            currentQTY = self.equities[symbol]["position"]
            newQTY = currentQTY + qty
        else:
            newQTY = qty

        
        self.equities[symbol] = {
            "position": newQTY,
            "entry_price": entry_price,
        }
        
        try:
            api.submit_order(
                symbol=symbol,
                qty=qty,
                side="buy",
                type="market",
                time_in_force="gtc"
            
            )
            messagebox.showinfo("Order Placed", f"Initial Order Placed for {symbol}")   
        except Exception as e:
            messagebox.showerror("Order Error", f"Error placing order: {e}")
            return
        

        self.refresh_table()
    
    
    def sell_equity(self):
        symbol = self.symbol_entry.get().upper()
        if not symbol or symbol not in self.equities:
            messagebox.showerror("Error", "Invalid symbol")
            return
        qtystr = self.qty_entry.get()
        if not qtystr.isdigit() or int(qtystr) <= 0:
            messagebox.showerror("Error", "Invalid quantity")
            return
        qty = int(qtystr)
        
        current_position = self.equities[symbol]["position"]
        if qty > current_position:
            messagebox.showerror("Error", "Quantity exceeds current position")
            return
        try:
            api.submit_order(
                symbol=symbol,
                qty=qty,
                side="sell",
                type="market",
                time_in_force="gtc"
            )
            messagebox.showinfo("Order Placed", f"Sell Order Placed for {symbol}")
            
            time.sleep(2)
            
            try:
                pos = api.get_position(symbol)
                position = int(float(pos.qty))
            except Exception as e:
                position = 0
            if position > 0:
                self.equities[symbol]["position"] = position
            else:
                del self.equities[symbol]
                
            self.refresh_table()
        except Exception as e:
            messagebox.showerror("Order Error", f"Error placing order: {e}")
            return        
    
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
        
    
    def sync_with_alpaca(self):
        try:
            positions = api.list_positions()
            self.equities = {}  # clear and refresh with live data

            for pos in positions:
                symbol = pos.symbol
                qty = int(float(pos.qty))
                entry_price = float(pos.avg_entry_price)

                self.equities[symbol] = {
                    "position": qty,
                    "entry_price": entry_price
                }


        except Exception as e:
            messagebox.showerror("Sync Error", f"Failed to sync with Alpaca: {e}")


   
    def refresh_table(self):
        for row in self.tree.get_children():
            self.tree.delete(row)
            
        for symbol, data in self.equities.items():
            current_price = self.fetch_alpaca_data(symbol)["price"]
            entry_price= data["entry_price"]
            qty = data["position"]
            
            pnl = round((current_price - entry_price) * qty, 2)
            pnl_str = f"${pnl:,.2f}"
            tag = "pnl_positive" if pnl >= 0 else "pnl_negative"
            
            total_value = round(data["position"] * current_price,2)
            total_value_str = f"${total_value:,.2f}"
            entry_price_str = f"${data['entry_price']:,.2f}"
            self.tree.insert("", "end", values=(
                symbol,
                data["position"],
                pnl_str,
                entry_price_str,
                total_value_str
                ), tags=(tag,))
        
        
    def auto_update(self):
        while self.running:
            time.sleep(10)
            self.sync_with_alpaca()
            self.refresh_table()
            
    
    

        
    def on_close(self):
        self.running = False
        self.root.destroy()
        
if __name__ == "__main__":
    root = tk.Tk()
    app = TradingBotGUI(root)
    root.protocol("WM_DELETE_WINDOW", app.on_close)
    root.mainloop()
            