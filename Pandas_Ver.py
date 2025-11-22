import tkinter as tk
from tkinter import ttk, messagebox
import ttkbootstrap as tb
from ttkbootstrap.constants import *
import pandas as pd
from datetime import datetime
import matplotlib.pyplot as plt 
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg


# === GLOBAL DATA ===
CSV_FILE = "transactions.csv"
COLUMNS = ["Date", "Type", "Category", "Amount", "Notes"]

# Initialize DataFrame
try:
    df = pd.read_csv(CSV_FILE)
    df["Amount"] = df["Amount"].astype(float)
except FileNotFoundError:
    df = pd.DataFrame(columns=COLUMNS)
    df.to_csv(CSV_FILE, index=False)


# === FUNCTIONS ===
def refresh_treeview():
    """Clear treeview and reload all rows from df"""
    for item in treeview.get_children():
        treeview.delete(item)
    for i, row in df.iterrows():
        treeview.insert("", "end", iid=i, values=tuple(row))


def save_data():
    """Save DataFrame to CSV"""
    df.to_csv(CSV_FILE, index=False)


def clear_inputs():
    type_entry.set("")
    category_entry.delete(0, "end")
    amount_entry.delete(0, "end")
    note_entry.delete(0, "end")


def add_entry():
    global df
    # Always use current date
    date_value = datetime.now().strftime("%Y-%m-%d")

    type_value = type_entry.get()
    category_value = category_entry.get().strip()
    amount_value = amount_entry.get().strip()
    notes_value = note_entry.get().strip()
    
    # Validation
    if not type_value or not category_value or not amount_value:
        messagebox.showwarning("Missing Information", "Please fill in all required fields!")
        return

    # Validate amount
    try:
        amount_value = float(amount_value)
    except ValueError:
        messagebox.showerror("Invalid Amount", "Please enter a numeric amount.")
        amount_entry.focus()
        return

    # Append new entry to DataFrame
    new_row = pd.DataFrame([{
        "Date": date_value,
        "Type": type_value,
        "Category": category_value,
        "Amount": amount_value,
        "Notes": notes_value
    }])
    df = pd.concat([df, new_row], ignore_index=True)
    save_data()
    refresh_treeview()
    update_dashboard()  # Update chart after adding entry
    clear_inputs()
    messagebox.showinfo("Success", "Entry added successfully!")


def edit_entry():
    global df
    cur_item = treeview.focus()
    if not cur_item:
        messagebox.showwarning("No selection", "Select a row to edit!")
        return
    
    values = treeview.item(cur_item, "values")
    date_val, type_val, cat_val, amount_val, notes_val = values

    edit_win = tk.Toplevel(root)
    edit_win.title("Edit Transaction")
    edit_win.geometry("400x400")
    edit_win.grab_set()
    
    # Form
    ttk.Label(edit_win, text="Date (YYYY-MM-DD):").grid(row=0, column=0, padx=5, pady=5, sticky="w")
    date_popup = ttk.Entry(edit_win)
    date_popup.insert(0, date_val)
    date_popup.grid(row=0, column=1)

    ttk.Label(edit_win, text="Type:").grid(row=1, column=0, padx=5, pady=5, sticky="w")
    type_popup = ttk.Combobox(edit_win, values=["Income", "Expense"], state="readonly")
    type_popup.set(type_val)
    type_popup.grid(row=1, column=1)

    ttk.Label(edit_win, text="Category:").grid(row=2, column=0, padx=5, pady=5, sticky="w")
    cat_popup = ttk.Entry(edit_win)
    cat_popup.insert(0, cat_val)
    cat_popup.grid(row=2, column=1)

    ttk.Label(edit_win, text="Amount:").grid(row=3, column=0, padx=5, pady=5, sticky="w")
    amount_popup = ttk.Entry(edit_win)
    amount_popup.insert(0, amount_val)
    amount_popup.grid(row=3, column=1)

    ttk.Label(edit_win, text="Notes:").grid(row=4, column=0, padx=5, pady=5, sticky="w")
    notes_popup = ttk.Entry(edit_win)
    notes_popup.insert(0, notes_val)
    notes_popup.grid(row=4, column=1)

    def save_changes():
        try:
            new_amount = float(amount_popup.get())
        except ValueError:
            messagebox.showerror("Invalid", "Amount must be numeric.")
            return

        idx = int(cur_item)
        df.loc[idx] = [
            date_popup.get(),
            type_popup.get(),
            cat_popup.get(),
            new_amount,
            notes_popup.get()
        ]
        save_data()
        refresh_treeview()
        update_dashboard()  # Update chart after editing
        edit_win.destroy()
        messagebox.showinfo("Updated", "Entry updated successfully!")

    ttk.Button(edit_win, text="Save Changes", command=save_changes).grid(row=5, column=0, columnspan=2, pady=10)


def delete_entry():
    global df
    cur_item = treeview.focus()
    if not cur_item:
        messagebox.showwarning("No selection", "Please select a row to delete")
        return
    confirm = messagebox.askyesno("Confirm Delete", "Delete this entry?")
    if confirm:
        df.drop(index=int(cur_item), inplace=True)
        df.reset_index(drop=True, inplace=True)
        save_data()
        refresh_treeview()
        update_dashboard()  # Update chart after deleting
        messagebox.showinfo("Deleted", "Entry deleted successfully")


def filter_sort():
    """Filter DataFrame by search text and sort by date"""
    search_text = search_entry.get().strip().lower()
    filtered_df = df.copy()

    # Filter by search text in Type, Category, or Notes
    if search_text:
        filtered_df = filtered_df[
            filtered_df["Type"].str.lower().str.contains(search_text) |
            filtered_df["Category"].str.lower().str.contains(search_text) |
            filtered_df["Notes"].str.lower().str.contains(search_text)
        ]

    # Sort by date
    ascending = True if sort_var.get() == "Ascending" else False
    filtered_df = filtered_df.sort_values(by="Date", ascending=ascending)

    # Update Treeview
    for item in treeview.get_children():
        treeview.delete(item)
    for i, row in filtered_df.iterrows():
        treeview.insert("", "end", iid=i, values=tuple(row))


def toggle_scrolling(event=None):
    """Bind mouse wheel only if not fullscreen"""
    if root.state() == "zoomed":  # fullscreen
        summary_canvas.unbind_all("<MouseWheel>")
        summary_scrollbar.pack_forget()
    else:
        summary_canvas.bind_all("<MouseWheel>", lambda e: summary_canvas.yview_scroll(int(-1*(e.delta/120)), "units"))
        summary_scrollbar.pack(side="right", fill="y")


def update_dashboard():
    ax.clear()
    ax.set_aspect('equal')

    # Filter by month
    if month_var.get() != "All Months":
        month_num = datetime.strptime(month_var.get(), "%B").month
        df_filtered = df[pd.to_datetime(df["Date"], errors="coerce").dt.month == month_num]
    else:
        df_filtered = df.copy()

    # PIE CHART: Expenses per Category
    expenses = df_filtered[df_filtered["Type"].str.lower() == "expense"]
    total_expenses = expenses["Amount"].sum() if not expenses.empty else 0

    if not expenses.empty and total_expenses > 0:
        cat_totals = expenses.groupby("Category")["Amount"].sum()
        cat_totals = cat_totals[cat_totals > 0]

        if not cat_totals.empty:
            colors = plt.cm.Set3(range(len(cat_totals)))
            ax.pie(
                cat_totals.values,
                labels=cat_totals.index,
                autopct="%1.1f%%",
                startangle=90,
                colors=colors,
                wedgeprops={"edgecolor": "white", "linewidth": 1.5},
                textprops={"color": "black", "fontsize": 10}
            )
            ax.set_title("Expenses per Category", fontsize=14, pad=15, color="white")
        else:
            ax.text(0.5, 0.5, "No valid data", ha="center", va="center", fontsize=12, color="white")
            ax.set_title("Expenses per Category", fontsize=14, pad=15, color="white")
            ax.axis('off')
    else:
        ax.text(0.5, 0.5, "No Expenses", ha="center", va="center", fontsize=12, color="white")
        ax.set_title("Expenses per Category", fontsize=14, pad=15, color="white")
        ax.axis('off')

    fig.tight_layout()
    canvas.draw()

    # UPDATE BUDGET PROGRESS
    income = df_filtered[df_filtered["Type"].str.lower() == "income"]
    total_income = income["Amount"].sum() if not income.empty else 0
    remaining = total_income - total_expenses
    percentage = (total_expenses / total_income * 100) if total_income > 0 else 0

    budget_progress['value'] = min(percentage, 100)
    if percentage >= 90:
        budget_progress.configure(bootstyle="danger")
    elif percentage >= 75:
        budget_progress.configure(bootstyle="warning")
    else:
        budget_progress.configure(bootstyle="success")

    budget_income_label.config(text=f"Income: ${total_income:.2f}")
    budget_spent_label.config(text=f"Spent: ${total_expenses:.2f}")
    budget_remaining_label.config(text=f"Remaining: ${remaining:.2f}")

    if total_income == 0:
        budget_percent_label.config(text="No income data available", foreground="gray")
    elif remaining < 0:
        budget_remaining_label.config(foreground="red")
        budget_percent_label.config(text=f"{percentage:.1f}% - OVER BUDGET!", foreground="red")
    else:
        budget_remaining_label.config(foreground="")
        budget_percent_label.config(text=f"{percentage:.1f}% of income used", foreground="")


# === MAIN WINDOW ===
root = tb.Window(themename="darkly")
root.title("Personal Finance Tracker (Pandas)")
root.geometry("1000x700")
root.minsize(900, 650)


# === NOTEBOOK (TABS) ===
notebook = ttk.Notebook(root)
notebook.pack(fill="both", expand=True)

tracker_tab = ttk.Frame(notebook)
summary_tab = ttk.Frame(notebook)

notebook.add(tracker_tab, text="Tracker")
notebook.add(summary_tab, text="Dashboard")


# === TRACKER TAB ===
## --- Add Transaction Frame ---
top_frame = ttk.LabelFrame(tracker_tab, text="Add Transaction")
top_frame.pack(fill="x", padx=10, pady=10)

ttk.Label(top_frame, text="Category:").grid(row=0, column=0, padx=5, pady=5)
category_entry = ttk.Entry(top_frame, width=15)
category_entry.grid(row=0, column=1, padx=5, pady=5)

ttk.Label(top_frame, text="Type:").grid(row=0, column=2, padx=5, pady=5)
type_entry = ttk.Combobox(top_frame, values=["Income", "Expense"], state="readonly", width=13)
type_entry.grid(row=0, column=3, padx=5, pady=5)

ttk.Label(top_frame, text="Amount:").grid(row=1, column=0, padx=5, pady=5)
amount_entry = ttk.Entry(top_frame, width=15)
amount_entry.grid(row=1, column=1, padx=5, pady=5)

ttk.Label(top_frame, text="Notes:").grid(row=2, column=0, padx=5, pady=5)
note_entry = ttk.Entry(top_frame, width=43)
note_entry.grid(row=2, column=1, columnspan=3, padx=5, pady=5)


## --- Buttons Frame ---
button_frame = ttk.Frame(tracker_tab)
button_frame.pack(fill="x", padx=10, pady=5)

ttk.Button(button_frame, text="Add Entry", command=add_entry, bootstyle="success").pack(side="left", padx=5)
ttk.Button(button_frame, text="Edit Entry", command=edit_entry, bootstyle="info").pack(side="left", padx=5)
ttk.Button(button_frame, text="Delete Entry", command=delete_entry, bootstyle="danger").pack(side="left", padx=5)
ttk.Button(button_frame, text="Export CSV", command=save_data, bootstyle="warning").pack(side="left", padx=5)


## --- Filter/Search + Sort Frame ---
filter_frame = ttk.LabelFrame(tracker_tab, text="Search / Sort")
filter_frame.pack(fill="x", padx=10, pady=5)

ttk.Label(filter_frame, text="Search:").grid(row=0, column=0, padx=5, pady=5)
search_entry = ttk.Entry(filter_frame, width=30)
search_entry.grid(row=0, column=1, padx=5, pady=5)

ttk.Label(filter_frame, text="Sort by Date:").grid(row=0, column=2, padx=5, pady=5)
sort_var = tk.StringVar(value="Ascending")
sort_dropdown = ttk.Combobox(filter_frame, values=["Ascending", "Descending"], textvariable=sort_var, state="readonly", width=12)
sort_dropdown.grid(row=0, column=3, padx=5, pady=5)

ttk.Button(filter_frame, text="Apply", bootstyle="primary", command=lambda: filter_sort()).grid(row=0, column=4, padx=5, pady=5)


## --- Transaction History (Treeview) ---
table_frame = ttk.LabelFrame(tracker_tab, text="Transaction History")
table_frame.pack(fill="both", expand=True, padx=10, pady=10)

treeview = ttk.Treeview(table_frame, columns=COLUMNS, show="headings")
for col in COLUMNS:
    treeview.heading(col, text=col, anchor="c")
    treeview.column(col, anchor="c", width=120)
treeview.pack(side="left", fill="both", expand=True)

scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=treeview.yview)
scrollbar.pack(side="right", fill="y")
treeview.configure(yscrollcommand=scrollbar.set)


# === SUMMARY TAB ===
## --- Scrollable Canvas Setup ---
summary_canvas = tk.Canvas(summary_tab, bg='#222222')
summary_scrollbar = ttk.Scrollbar(summary_tab, orient="vertical", command=summary_canvas.yview)
scrollable_summary = ttk.Frame(summary_canvas)

if root.state() == "zoomed":
    summary_scrollbar.pack_forget()
else:
    summary_scrollbar.pack(side="right", fill="y")

scrollable_summary.bind(
    "<Configure>",
    lambda e: summary_canvas.configure(scrollregion=summary_canvas.bbox("all"))
)

summary_canvas.create_window((0, 0), window=scrollable_summary, anchor="nw", width=summary_canvas.winfo_reqwidth())
summary_canvas.configure(yscrollcommand=summary_scrollbar.set)
summary_canvas.bind("<Configure>", lambda e: summary_canvas.itemconfig(1, width=e.width))
summary_canvas.pack(side="left", fill="both", expand=True)
summary_scrollbar.pack(side="right", fill="y")

def _on_mousewheel(event):
    summary_canvas.yview_scroll(int(-1*(event.delta/120)), "units")

summary_canvas.bind_all("<MouseWheel>", _on_mousewheel)


## --- Expenses Breakdown Frame ---
summary_frame = ttk.LabelFrame(scrollable_summary, text="Expenses Breakdown")
summary_frame.pack(fill="both", expand=True, padx=10, pady=10)

### Top Controls
controls_frame = ttk.Frame(summary_frame)
controls_frame.pack(fill="x", padx=5, pady=5)

ttk.Label(controls_frame, text="Filter by Month:").pack(side="left", padx=5)
month_var = tk.StringVar(value="All Months")
month_choices = ["All Months"] + [datetime.strptime(str(i), "%m").strftime("%B") for i in range(1, 13)]
month_dropdown = ttk.Combobox(controls_frame, values=month_choices, textvariable=month_var, state="readonly", width=15)
month_dropdown.pack(side="left", padx=5)


### Chart Container
chart_frame = ttk.Frame(summary_frame)
chart_frame.pack(fill="both", expand=True, padx=10, pady=10)

fig, ax = plt.subplots(figsize=(6, 6))
canvas = FigureCanvasTkAgg(fig, master=chart_frame)
canvas.get_tk_widget().pack(fill="both", expand=True)


## --- Budget Frame ---
budget_frame = ttk.LabelFrame(scrollable_summary, text="Budget Percentage (Income vs Expenses)")
budget_frame.pack(fill="x", padx=10, pady=10)

budget_info_frame = ttk.Frame(budget_frame)
budget_info_frame.pack(fill="x", padx=10, pady=5)

budget_income_label = ttk.Label(budget_info_frame, text="Income: $0.00", font=("Arial", 10))
budget_income_label.pack(side="left", padx=5)

budget_spent_label = ttk.Label(budget_info_frame, text="Spent: $0.00", font=("Arial", 10))
budget_spent_label.pack(side="left", padx=5)

budget_remaining_label = ttk.Label(budget_info_frame, text="Remaining: $0.00", font=("Arial", 10))
budget_remaining_label.pack(side="right", padx=5)

budget_progress = ttk.Progressbar(budget_frame, mode='determinate', bootstyle="success")
budget_progress.pack(fill="x", padx=10, pady=10)

budget_percent_label = ttk.Label(budget_frame, text="0% of budget used", font=("Arial", 11, "bold"))
budget_percent_label.pack(pady=5)


# === BINDINGS & INIT ===
month_dropdown.bind("<<ComboboxSelected>>", lambda e: update_dashboard())
root.bind("<Configure>", toggle_scrolling)
toggle_scrolling()
update_dashboard()

root.mainloop()
