import tkinter as tk
from tkinter import ttk, messagebox
import threading
import time
import alpaca_trade_api as tradeapi
import google.generativeai as genai
from datetime import datetime

# === Alpaca API credentials - replace with your own ===
key = "ENTER YOUR OWN KEY"
secret_key = "ENTER YOUR OWN SECRET KEY"
BASE_URL = "https://paper-api.alpaca.markets/"
api = tradeapi.REST(key, secret_key, BASE_URL, api_version='v2')

# Configure Google Generative AI key
genai.configure(api_key="ENTER YOUR OWN GOOGLE GENERATIVE AI KEY")

# AI analyze function
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


# Fetch portfolio helper
def fetch_portfolio():
    try:
        positions = api.list_positions()
    except Exception as e:
        positions = []
        messagebox.showerror("Error", f"Failed to fetch portfolio: {e}")

    portfolio = []
    for position in positions:
        portfolio.append({
            "symbol": position.symbol,
            "qty": position.qty,
            "entry_price": position.avg_entry_price,
            "current_price": position.current_price,
            "unrealized_pl": position.unrealized_pl,
            "side": 'long'
        })
    return portfolio


# Fetch open orders helper
def fetch_open_orders():
    try:
        orders = api.list_orders(status='open')
    except Exception as e:
        orders = []
        messagebox.showerror("Error", f"Failed to fetch open orders: {e}")

    open_orders = []
    for order in orders:
        open_orders.append({
            "symbol": order.symbol,
            "qty": order.qty,
            "side": order.side,
            "limit_price": order.limit_price,
        })
    return open_orders


class TradingBotGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Trading Bot")
        self.root.geometry("900x700")
        self.root.configure(bg="#F8F9FA")
        

        self.font_title = ("Segoe UI", 20, "bold")
        self.font_normal = ("Segoe UI", 12)
        self.font_small = ("Segoe UI", 10)

        style = ttk.Style(self.root)
        style.theme_use('clam')

        style.configure('AI.TLabel',
                        background='#F8F9FA',
                        foreground='#212529',
                        font=self.font_normal)

        style.configure('AI.Title.TLabel',
                        background='#F8F9FA',
                        foreground='#212529',
                        font=self.font_title)

        style.configure('AI.TEntry',
                        fieldbackground='white',
                        foreground='#212529',
                        font=self.font_normal,
                        borderwidth=1,
                        relief='solid',
                        padding=5)

        style.configure('AI.Buy.TButton',
                        background='#00C853',
                        foreground='white',
                        font=('Segoe UI', 12, 'bold'),
                        borderwidth=0,
                        padding=8)
        style.map('AI.Buy.TButton',
                  background=[('active', '#00E676')])

        style.configure('AI.Sell.TButton',
                        background='#D50000',
                        foreground='white',
                        font=('Segoe UI', 12, 'bold'),
                        borderwidth=0,
                        padding=8)
        style.map('AI.Sell.TButton',
                  background=[('active', '#FF1744')])

        style.configure('AI.Treeview',
                        background='white',
                        foreground='#212529',
                        fieldbackground='white',
                        font=self.font_small,
                        rowheight=25)
        style.configure('AI.Treeview.Heading',
                        background='#E9ECEF',
                        foreground='#212529',
                        font=('Segoe UI', 12, 'bold'))

        style.map('AI.Treeview',
                  background=[('selected', '#00C853')],
                  foreground=[('selected', 'white')])

        self.main_frame = tk.Frame(root, bg="#F8F9FA")
        self.main_frame.pack(fill='both', expand=True, padx=20, pady=20)

        self.title_label = ttk.Label(self.main_frame, text="Trading Bot", style='AI.Title.TLabel')
        self.title_label.pack(pady=(0, 20))

        self.account_frame = tk.Frame(self.main_frame, bg="#F8F9FA")
        self.account_frame.pack(fill='x', pady=10)

        self.account_value = ttk.Label(self.account_frame, text="Account Value: $0.00", style='AI.TLabel')
        self.account_value.grid(row=0, column=0, padx=15)

        self.pnl_value = ttk.Label(self.account_frame, text="Open PnL: $0.00", style='AI.TLabel')
        self.pnl_value.grid(row=0, column=1, padx=15)

        self.buyingpower = ttk.Label(self.account_frame, text="Buying Power: $0.00", style='AI.TLabel')
        self.buyingpower.grid(row=0, column=2, padx=15)

        self.form_frame = tk.Frame(self.main_frame, bg="#F8F9FA")
        self.form_frame.pack(fill='x', pady=10)

        labels = ["Symbol:", "Qty:", "Order Type:", "Limit Price:"]
        for i, text in enumerate(labels):
            lbl = ttk.Label(self.form_frame, text=text, style='AI.TLabel')
            lbl.grid(row=0, column=i*2, sticky='w', padx=5, pady=8)

        self.symbol_entry = ttk.Entry(self.form_frame, style='AI.TEntry', width=10)
        self.symbol_entry.grid(row=0, column=1, padx=5)

        self.qty_entry = ttk.Entry(self.form_frame, style='AI.TEntry', width=8)
        self.qty_entry.grid(row=0, column=3, padx=5)

        self.order_type = ttk.Combobox(self.form_frame, values=["Market", "Limit"], state="readonly", width=10)
        self.order_type.grid(row=0, column=5, padx=5)
        self.order_type.set("Market")
        self.order_type.bind("<<ComboboxSelected>>", self.on_order_type_change)

        self.limit_price_entry = ttk.Entry(self.form_frame, style='AI.TEntry', width=12, state='disabled')
        self.limit_price_entry.grid(row=0, column=7, padx=5)

        self.buy_button = ttk.Button(self.form_frame, text="Buy", style='AI.Buy.TButton', command=self.add_equity)
        self.buy_button.grid(row=0, column=8, padx=(20, 10))

        self.sell_button = ttk.Button(self.form_frame, text="Sell", style='AI.Sell.TButton', command=self.sell_equity)
        self.sell_button.grid(row=0, column=9, padx=10)

        self.tree_frame = tk.Frame(self.main_frame, bg="#F8F9FA")
        self.tree_frame.pack(fill='both', expand=True, pady=15)

        columns = ("Symbol", "Position", "PnL", "PnL %", "Entry Price", "Current Price", "Total Value")
        self.tree = ttk.Treeview(self.tree_frame, columns=columns, show='headings', style='AI.Treeview')
        for col in columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=110, anchor='center')
        self.tree.pack(fill='both', expand=True)

        self.tree.tag_configure("pnl_positive", foreground="#28a745")
        self.tree.tag_configure("pnl_negative", foreground="#dc3545")

        self.orders_frame = tk.Frame(self.main_frame, bg="#F8F9FA")
        self.orders_frame.pack(fill='both', expand=True, pady=10)

        order_columns = ("Symbol", "Qty", "Side", "Price", "Status", "Filled At")
        self.orders_tree = ttk.Treeview(self.orders_frame, columns=order_columns, show='headings', style='AI.Treeview')
        for col in order_columns:
            self.orders_tree.heading(col, text=col)
            self.orders_tree.column(col, width=110, anchor="center")
        self.orders_tree.pack(fill='both', expand=True)

        self.chatgpt_frame = tk.Frame(self.main_frame, bg="#F8F9FA")
        self.chatgpt_frame.pack(fill='x', pady=15)

        self.chat_input = ttk.Entry(self.chatgpt_frame, style='AI.TEntry', width=60)
        self.chat_input.grid(row=0, column=0, padx=(0, 10))

        self.send_button = ttk.Button(self.chatgpt_frame, text="Send", command=self.send_message)
        self.send_button.grid(row=0, column=1)

        self.chat_output = tk.Text(self.main_frame, height=15, bg='white', fg='#212529', font=self.font_normal, wrap='word', relief='solid', borderwidth=1)
        self.chat_output.pack(fill='both', expand=True, padx=10, pady=10)
        self.chat_output.config(state=tk.DISABLED)

        self.equities = {}

        self.sync_with_alpaca()
        self.update_account_value()
        self.refresh_table()
        self.refresh_orders()

        self.running = True
        self.auto_update_thread = threading.Thread(target=self.auto_update, daemon=True)
        self.auto_update_thread.start()

    def on_order_type_change(self, event=None):
        selected = self.order_type.get().lower()
        if selected == "limit":
            self.limit_price_entry.config(state=tk.NORMAL)
        else:
            self.limit_price_entry.config(state=tk.DISABLED)
            self.limit_price_entry.delete(0, tk.END)

    def fetch_alpaca_data(self, symbol):
        try:
            barset = api.get_latest_trade(symbol)
            return {"price": barset.price}
        except Exception:
            return {"price": -1}

    def add_equity(self):
        symbol = self.symbol_entry.get().upper()

        if not symbol:
            messagebox.showerror("Error", "Invalid input")
            return

        qty = self.qty_entry.get()
        if not qty.isdigit() or int(qty) <= 0:
            messagebox.showerror("Error", "Invalid quantity")
            return
        qty = int(qty)

        order_type = self.order_type.get().lower()
        limit_price = self.limit_price_entry.get()

        order_args = {
            "symbol": symbol,
            "qty": qty,
            "side": "buy",
            "type": order_type,
            "time_in_force": "gtc"
        }

        current_price = self.fetch_alpaca_data(symbol)["price"]
        if order_type == "limit":
            try:
                limit_price_float = float(limit_price)
            except ValueError:
                messagebox.showerror("Error", "Invalid limit price")
                return
            if limit_price_float > current_price:
                messagebox.showerror("Error", "Limit price cannot be greater than current price")
                return
            order_args["limit_price"] = limit_price_float

        try:
            api.submit_order(**order_args)
            messagebox.showinfo("Order Placed", f"Order placed for {symbol}")
            self.refresh_orders()
        except Exception as e:
            messagebox.showerror("Order Error", f"Error placing order: {e}")
            return

        entry_price = current_price

        if symbol in self.equities:
            current_qty = self.equities[symbol]["position"]
            new_qty = current_qty + qty
        else:
            new_qty = qty

        self.equities[symbol] = {
            "position": new_qty,
            "entry_price": entry_price,
        }
        self.refresh_table()

    def sell_equity(self):
        symbol = self.symbol_entry.get().upper()
        if not symbol or symbol not in self.equities:
            messagebox.showerror("Error", "Invalid symbol")
            return

        qty_str = self.qty_entry.get()
        if not qty_str.isdigit() or int(qty_str) <= 0:
            messagebox.showerror("Error", "Invalid quantity")
            return
        qty = int(qty_str)

        current_position = self.equities[symbol]["position"]
        if qty > current_position:
            messagebox.showerror("Error", "Quantity exceeds current position")
            return

        order_type = self.order_type.get().lower()
        limit_price = self.limit_price_entry.get()

        order_args = {
            "symbol": symbol,
            "qty": qty,
            "side": "sell",
            "type": order_type,
            "time_in_force": "gtc"
        }

        if order_type == "limit":
            try:
                limit_price_float = float(limit_price)
            except ValueError:
                messagebox.showerror("Error", "Invalid limit price")
                return

            current_price = self.fetch_alpaca_data(symbol)["price"]
            if limit_price_float < current_price:
                messagebox.showerror("Error", "Limit price cannot be lower than current price")
                return

            order_args["limit_price"] = limit_price_float

        try:
            api.submit_order(**order_args)
            messagebox.showinfo("Order Placed", f"Sell order placed for {symbol}")
            self.refresh_orders()
            time.sleep(5)

            try:
                pos = api.get_position(symbol)
                position = int(float(pos.qty))
            except Exception:
                position = 0

            if position > 0:
                self.equities[symbol]["position"] = position
            else:
                del self.equities[symbol]

            self.refresh_table()
        except Exception as e:
            messagebox.showerror("Order Error", f"Error placing order: {e}")

    def send_message(self):
        message = self.chat_input.get()
        if not message:
            return
        response = analyze_message(message)

        self.chat_output.config(state=tk.NORMAL)
        self.chat_output.insert(tk.END, f"You: {message}\n")
        self.chat_output.insert(tk.END, f"Bot: {response}\n\n")
        self.chat_output.see(tk.END)
        self.chat_output.config(state=tk.DISABLED)
        self.chat_input.delete(0, tk.END)

    def sync_with_alpaca(self):
        try:
            positions = api.list_positions()
            self.equities = {}

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

    def update_account_value(self):
        try:
            account = api.get_account()
            value = float(account.equity)
            buying_power = float(account.buying_power)
            pnl = self.get_open_pnl()
            self.account_value.config(text=f"Account Value: ${value:,.2f}")
            self.pnl_value.config(text=f"Open PnL: ${pnl:,.2f}")
            self.buyingpower.config(text=f"Buying Power: ${buying_power:,.2f}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to fetch account value: {e}")
            self.pnl_value.config(text="Open PnL: $0.00")
            self.account_value.config(text="Account Value: $0.00")
            self.buyingpower.config(text="Buying Power: $0.00")

    def get_open_pnl(self):
        try:
            positions = api.list_positions()
            total_pnl = 0.0
            for position in positions:
                total_pnl += float(position.unrealized_pl)
            return total_pnl
        except Exception as e:
            messagebox.showerror("Error", f"Failed to fetch open PnL: {e}")
            return 0.0

    def refresh_table(self):
        for row in self.tree.get_children():
            self.tree.delete(row)

        for symbol, data in self.equities.items():
            current_price = self.fetch_alpaca_data(symbol)["price"]
            entry_price = data["entry_price"]
            qty = data["position"]

            pnl = round((current_price - entry_price) * qty, 2)
            pnl_str = f"${pnl:,.2f}"

            if entry_price > 0:
                pnl_percent = ((current_price - entry_price) / entry_price) * 100
            else:
                pnl_percent = 0.0
            pnl_percent_str = f"{pnl_percent:.2f}%"

            tag = "pnl_positive" if pnl >= 0 else "pnl_negative"

            total_value = round(data["position"] * current_price, 2)
            total_value_str = f"${total_value:,.2f}"
            entry_price_str = f"${entry_price:,.2f}"
            current_price_str = f"${current_price:,.2f}"

            self.tree.insert("", "end", values=(
                symbol,
                qty,
                pnl_str,
                pnl_percent_str,
                entry_price_str,
                current_price_str,
                total_value_str
            ), tags=(tag,))

    def refresh_orders(self):
        for row in self.orders_tree.get_children():
            self.orders_tree.delete(row)

        try:
            orders = api.list_orders(status='all')
            for order in orders:
                filled_val = order.filled_at
                if filled_val:
                    if isinstance(filled_val, str):
                        dt = datetime.strptime(filled_val, "%Y-%m-%dT%H:%M:%SZ")
                    else:
                        dt = filled_val
                    filled_at = dt.strftime("%Y-%m-%d %H:%M:%S")
                else:
                    filled_at = "N/A"

                def safeformat(price):
                    try:
                        return f"${float(price):.2f}"
                    except (ValueError, TypeError):
                        return "N/A"

                self.orders_tree.insert("", "end", values=(
                    order.symbol,
                    order.qty,
                    order.side,
                    safeformat(order.limit_price),
                    order.status,
                    filled_at,
                ))
        except Exception as e:
            messagebox.showerror("Error", f"Failed to fetch orders: {e}")

    def auto_update(self):
        while self.running:
            self.sync_with_alpaca()
            self.update_account_value()
            self.refresh_table()
            self.refresh_orders()
            time.sleep(15)

    def on_close(self):
        self.running = False
        self.root.destroy()


if __name__ == "__main__":
    root = tk.Tk()
    app = TradingBotGUI(root)
    root.protocol("WM_DELETE_WINDOW", app.on_close)
    root.mainloop()
