
import os
from datetime import datetime
from kivy.app import App
from kivy.lang import Builder
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.storage.jsonstore import JsonStore

KV = """
<MainScreen>:
    BoxLayout:
        orientation: "vertical"
        padding: dp(12)
        spacing: dp(8)
        canvas.before:
            Color:
                rgba: .035, .055, .09, 1
            Rectangle:
                pos: self.pos
                size: self.size
        Label:
            text: "[b]IMAX AI[/b]  |  Risk & Account Monitor"
            markup: True
            size_hint_y: None
            height: dp(48)
            color: .25, .78, 1, 1
        ScrollView:
            GridLayout:
                cols: 1
                spacing: dp(8)
                padding: dp(4)
                size_hint_y: None
                height: self.minimum_height
                Label:
                    text: "[b]ACCOUNT SETUP[/b]"
                    markup: True
                    size_hint_y: None
                    height: dp(30)
                    color: .25, .78, 1, 1
                TextInput:
                    id: name
                    hint_text: "Account name"
                    multiline: False
                    size_hint_y: None
                    height: dp(44)
                TextInput:
                    id: start
                    text: "10000"
                    hint_text: "Starting balance"
                    input_filter: "float"
                    multiline: False
                    size_hint_y: None
                    height: dp(44)
                Spinner:
                    id: dtype
                    text: "Trailing"
                    values: ["Static", "Trailing", "Unknown"]
                    size_hint_y: None
                    height: dp(44)
                TextInput:
                    id: maxdd
                    text: "500"
                    hint_text: "Maximum drawdown amount"
                    input_filter: "float"
                    multiline: False
                    size_hint_y: None
                    height: dp(44)
                TextInput:
                    id: daily
                    text: "300"
                    hint_text: "Daily drawdown amount (optional)"
                    input_filter: "float"
                    multiline: False
                    size_hint_y: None
                    height: dp(44)
                TextInput:
                    id: buffer
                    text: "100"
                    hint_text: "Protected buffer amount"
                    input_filter: "float"
                    multiline: False
                    size_hint_y: None
                    height: dp(44)
                TextInput:
                    id: slots
                    text: "20"
                    hint_text: "Planned trade slots"
                    input_filter: "int"
                    multiline: False
                    size_hint_y: None
                    height: dp(44)
                TextInput:
                    id: cap
                    text: "20"
                    hint_text: "Maximum risk per trade"
                    input_filter: "float"
                    multiline: False
                    size_hint_y: None
                    height: dp(44)
                TextInput:
                    id: equity
                    text: "10000"
                    hint_text: "Current equity"
                    input_filter: "float"
                    multiline: False
                    size_hint_y: None
                    height: dp(44)
                TextInput:
                    id: high
                    text: "10000"
                    hint_text: "Highest equity (trailing accounts)"
                    input_filter: "float"
                    multiline: False
                    size_hint_y: None
                    height: dp(44)
                Button:
                    text: "SAVE ACCOUNT & CALCULATE"
                    size_hint_y: None
                    height: dp(48)
                    on_release: root.save_and_calculate()
                Label:
                    id: output
                    text: "Set up an account to see your risk plan."
                    markup: True
                    size_hint_y: None
                    height: dp(190)
                    text_size: self.width - dp(12), None
                    halign: "left"
                    valign: "top"
                    color: .92, .95, 1, 1
                Label:
                    text: "[b]RECORD COMPLETED TRADE[/b]"
                    markup: True
                    size_hint_y: None
                    height: dp(30)
                    color: .25, .78, 1, 1
                Spinner:
                    id: symbol
                    text: "XAUUSD"
                    values: ["XAUUSD", "NAS100", "US30", "Other"]
                    size_hint_y: None
                    height: dp(44)
                TextInput:
                    id: pnl
                    hint_text: "Trade P/L (+ win, - loss)"
                    input_filter: "float"
                    multiline: False
                    size_hint_y: None
                    height: dp(44)
                Button:
                    text: "ADD TRADE RESULT"
                    size_hint_y: None
                    height: dp(46)
                    on_release: root.add_trade()
                Label:
                    id: history
                    text: "No trades recorded."
                    markup: True
                    size_hint_y: None
                    height: dp(150)
                    text_size: self.width - dp(12), None
                    halign: "left"
                    valign: "top"
                    color: .78, .85, .94, 1
                Label:
                    text: "Planning tool only. Verify your firm's rules. No broker connection; never enter broker passwords."
                    size_hint_y: None
                    height: dp(55)
                    text_size: self.width - dp(12), None
                    color: 1, .72, .35, 1
"""

class MainScreen(Screen):
    def on_kv_post(self, *args):
        self.store = JsonStore(os.path.join(App.get_running_app().user_data_dir, "imax.json"))
        self.trades = self.store.get("trades")["items"] if self.store.exists("trades") else []
        self.refresh_history()

    def val(self, key, default=0):
        try:
            return float(self.ids[key].text or default)
        except ValueError:
            return float(default)

    def save_and_calculate(self):
        cfg = {k: self.ids[k].text for k in
               ["name", "start", "dtype", "maxdd", "daily", "buffer", "slots", "cap", "equity", "high"]}
        self.store.put("account", **cfg)
        self.calculate()

    def calculate(self):
        start, maxdd = self.val("start", 10000), self.val("maxdd", 500)
        buffer, slots = self.val("buffer", 100), max(0, int(self.val("slots", 20)))
        cap, equity = self.val("cap", 20), self.val("equity", start)
        high = max(self.val("high", start), equity)
        spent = sum(max(0, -float(t["pnl"])) for t in self.trades)
        remaining_slots = max(0, slots - len(self.trades))
        budget = max(0, maxdd - buffer)
        remaining = max(0, budget - spent)
        next_risk = min(cap, remaining / remaining_slots) if remaining_slots else 0
        kind = self.ids.dtype.text
        if kind == "Static":
            floor = f"Static floor estimate: {start-maxdd:,.2f}"
        elif kind == "Trailing":
            floor = f"Trailing floor estimate: {high-maxdd:,.2f}"
        else:
            floor = "Breach floor: UNKNOWN — no floor calculated"
        warning = "RULES UNVERIFIED" if kind == "Unknown" else "Estimate only — verify official firm rules"
        self.ids.output.text = (
            f"[b]{warning}[/b]\\n{floor}\\n\\n"
            f"Planned risk budget: {budget:,.2f}\\n"
            f"Losses charged: {spent:,.2f}\\n"
            f"Remaining budget: {remaining:,.2f}\\n"
            f"Trade slots remaining: {remaining_slots}\\n"
            f"[b]Suggested next-trade risk: {next_risk:,.2f}[/b]\\n"
            f"Protected buffer: {buffer:,.2f} (excluded from budget)"
        )

    def add_trade(self):
        if not self.ids.pnl.text.strip():
            self.ids.output.text = "Enter a trade P/L first."
            return
        pnl = float(self.ids.pnl.text)
        self.trades.append({"symbol": self.ids.symbol.text, "pnl": pnl,
                            "time": datetime.now().strftime("%Y-%m-%d %H:%M")})
        self.store.put("trades", items=self.trades)
        self.ids.pnl.text = ""
        self.refresh_history()
        self.calculate()

    def refresh_history(self):
        if not self.trades:
            self.ids.history.text = "No trades recorded."
            return
        rows = ["[b]Recent trades[/b]"]
        for t in self.trades[-8:][::-1]:
            rows.append(f'{t["time"]}  {t["symbol"]}  {t["pnl"]:+.2f}')
        wins = sum(t["pnl"] > 0 for t in self.trades)
        losses = sum(t["pnl"] < 0 for t in self.trades)
        rows.append(f"Total {len(self.trades)} | Wins {wins} | Losses {losses}")
        self.ids.history.text = "\\n".join(rows)

class IMAXAIApp(App):
    def build(self):
        Builder.load_string(KV)
        manager = ScreenManager()
        manager.add_widget(MainScreen(name="main"))
        return manager

if __name__ == "__main__":
    IMAXAIApp().run()
