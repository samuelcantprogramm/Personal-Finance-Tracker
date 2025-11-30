import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import ttkbootstrap as tb
import pandas as pd
from datetime import datetime
import matplotlib.pyplot as plt 
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

# === GLOBAL DATA ===
CSV_FILE = "transactions.csv"
COLUMNS = ["Date", "Type", "Category", "Amount", "Notes"]

# Initialize DataFrame from CSV or create a new one if file doesn't exist
try:
    df = pd.read_csv(CSV_FILE)
    df["Amount"] = df["Amount"].astype(float)
except FileNotFoundError:
    df = pd.DataFrame(columns=COLUMNS)
    df.to_csv(CSV_FILE, index=False)


# === FUNCTIONS ===
def refresh_treeview():
    """Clear the treeview and reload all rows from DataFrame"""
    for item in treeview.get_children():
        treeview.delete(item)
    for i, row in df.iterrows():
        formatted_date = format_date(row["Date"])
        values = (
            formatted_date,
            row["Type"],
            row["Category"],
            f"₱{row['Amount']:,.2f}",
            row["Notes"]
        )
        treeview.insert("", "end", iid=i, values=values)


def save_data():
    """Save DataFrame to CSV"""
    df.to_csv(CSV_FILE, index=False)


def format_date(raw_date):
    """Convert to 'dd Mon YYYY' or return raw value if invalid."""
    try:
        d = pd.to_datetime(raw_date, errors="coerce")
        if pd.isna(d):
            return raw_date
        return d.strftime("%d %b %Y")
    except Exception:
        return raw_date


def clear_inputs():
    """Clears all input fields"""
    type_entry.set("")
    category_entry.delete(0, "end")
    amount_entry.delete(0, "end")
    note_entry.delete(0, "end")


def add_entry():
    """Add a new transaction entry to the DataFrame"""
    global df

    # Always use today's date (store as Day Month Year for display/storage)
    date_value = datetime.now().strftime("%d %b %Y")

    type_value = type_entry.get().strip()
    category_value = category_entry.get().strip()
    amount_raw = amount_entry.get().strip()
    notes_value = note_entry.get().strip()

    # === VALIDATIONS ===

    # Required fields check
    if not type_value or not category_value or not amount_raw:
        messagebox.showwarning("Missing Information", "Please fill in all required fields!")
        return

    # Validate Type
    if type_value not in ["Income", "Expense"]:
        messagebox.showerror("Invalid Type", "Type must be either Income or Expense.")
        return

    # Clean amount input (remove ₱, commas, spaces)
    cleaned_amount = amount_raw.replace("₱", "").replace(",", "").strip()

    # Validate numeric
    try:
        amount_value = float(cleaned_amount)
    except ValueError:
        messagebox.showerror("Invalid Amount", "Amount must be numeric (e.g., 500 or 500.50).")
        amount_entry.focus()
        return

    # Prevent zero or negative amounts
    if amount_value <= 0:
        messagebox.showerror("Invalid Amount", "Amount must be greater than zero.")
        return
    
    # Validate category letters/numbers only + spaces/hyphens
    import re
    if not re.match(r"^[A-Za-z0-9\s\-]+$", category_value):
        messagebox.showerror("Invalid Category", "Category cannot contain symbols.\nAllowed: letters, numbers, spaces, hyphens.")
        return

    # Category cannot be just numbers
    if category_value.isdigit():
        messagebox.showerror("Invalid Category", "Category cannot contain only numbers.")
        return

    # === If everything is valid → Append the data ===
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
    update_dashboard()
    clear_inputs()

    messagebox.showinfo("Success", "Entry added successfully!")


def edit_entry():
    """Open a popup to edit the selected transaction"""
    global df
    cur_item = treeview.focus()
    if not cur_item:
        messagebox.showwarning("No selection", "Select a row to edit!")
        return
    
    values = treeview.item(cur_item, "values")
    date_val, type_val, cat_val, amount_val, notes_val = values

    # Popup window for editing
    edit_win = tk.Toplevel(root)
    edit_win.title("Edit Transaction")
    edit_win.geometry("400x300")
    edit_win.resizable(False, False)  
    edit_win.rowconfigure(0, minsize=30)   # space at top
    edit_win.grab_set()
    def validate_amount_edit(p):
        clean_p = p.replace("₱", "").replace(",", "").strip()
        digits_only = ''.join(filter(str.isdigit, clean_p.split('.')[0]))
        return len(digits_only) <= 6
   
    # Form fields
    fixed_width = 20
    ttk.Label(edit_win, text="Type:").grid(row=1, column=0, padx=10, pady=5, sticky="w")
    type_popup = ttk.Combobox(edit_win, values=["Income", "Expense"], state="readonly", width= 18)
    type_popup.set(type_val)
    type_popup.grid(row=1, column=1)

    ttk.Label(edit_win, text="Category:").grid(row=2, column=0, padx=10, pady=5, sticky="w")
    cat_popup = ttk.Entry(edit_win, width= fixed_width)
    cat_popup.insert(0, cat_val)
    cat_popup.grid(row=2, column=1)
    cat_popup.configure(validate="key", 
                       validatecommand=(edit_win.register(lambda p: len(p) <= 20), '%P'))
    
    ttk.Label(edit_win, text="Amount:").grid(row=3, column=0, padx=10, pady=5, sticky="w")
    amount_popup = ttk.Entry(edit_win, width= fixed_width)
    amount_popup.insert(0, amount_val)
    amount_popup.grid(row=3, column=1)
    amount_popup.configure(validate="key", 
                      validatecommand=(edit_win.register(validate_amount_edit), '%P'))

    ttk.Label(edit_win, text="Notes:").grid(row=4, column=0, padx=10, pady=5, sticky="w")
    notes_popup = ttk.Entry(edit_win, width= fixed_width)
    notes_popup.insert(0, notes_val)   
    notes_popup.grid(row=4, column=1)
    notes_popup.configure(validate="key", 
                         validatecommand=(edit_win.register(lambda p: len(p) <= 50), '%P'))

    # Helper function of edit_entry
    def save_changes():
        raw_amount = amount_popup.get()

        clean_amount = raw_amount.replace("₱", "").replace(",", "").strip()
        
        # === AMOUNT VALIDATION ===
        try:
            new_amount = float(clean_amount)
        except ValueError:
            messagebox.showerror("Invalid", "Amount must be numeric.")
            return

        if new_amount <= 0:
            messagebox.showerror("Invalid Amount", "Amount must be greater than zero.")
            return

        idx = int(cur_item)
        df.at[idx, "Type"] = type_popup.get()
        df.at[idx, "Category"] = cat_popup.get()
        df.at[idx, "Amount"] = new_amount
        df.at[idx, "Notes"] = notes_popup.get()
 
        save_data()
        refresh_treeview()
        update_dashboard()
        edit_win.destroy()
        messagebox.showinfo("Updated", "Entry updated successfully!")

    ttk.Button(edit_win, text="Save Changes", command=save_changes).grid(row=5, column=0, columnspan=2, padx=(80,0), pady=10)


def delete_entry():
    """Delete the selected transaction"""
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
        update_dashboard() 
        messagebox.showinfo("Deleted", "Entry deleted successfully")


def export_csv():
    """Export the DataFrame to a CSV file at user-specified path"""
    file_path = filedialog.asksaveasfilename(
        defaultextension=".csv",
        filetypes=[("CSV Files", "*.csv")],
        title="Save CSV As"
    )
    if not file_path:
        return
    df.to_csv(file_path, index=False)
    messagebox.showinfo("Export Complete", f"CSV has been exported to:\n{file_path}")


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
    if sort_var.get() in ["Ascending", "Descending"]: 
        ascending = (sort_var.get() == "Ascending")
        filtered_df = filtered_df.sort_values(by="Date", ascending=ascending)

    # Update Treeview - FIXED: Use filtered_df
    for item in treeview.get_children():
        treeview.delete(item)
    for i, row in filtered_df.iterrows():
        values = (
            format_date(row["Date"]),
            row["Type"],
            row["Category"],
            f"₱{row['Amount']:,.2f}",
            row["Notes"]
        )
        treeview.insert("", "end", iid=i, values=values)


def toggle_scrolling(event=None):
    """Bind mouse wheel only if not fullscreen"""
    if root.state() == "zoomed":  # fullscreen
        summary_canvas.unbind_all("<MouseWheel>")
        summary_scrollbar.pack_forget()
    else:
        # Content exceeds canvas: enable scrolling and show scrollbar
        summary_canvas.bind_all("<MouseWheel>", lambda e: summary_canvas.yview_scroll(int(-1*(e.delta/120)), "units"))
        summary_scrollbar.pack(side="right", fill="y")



def update_dashboard():
    """Update pie chart and budget progress in the Statistics tab"""
    ax.clear()
    
    # Set dark background for the figure to match your theme
    fig.patch.set_facecolor('#222222')  # Dark background
    ax.set_facecolor('#222222')  # Dark background for the plot area
    
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
            wedges, texts, autotexts = ax.pie(
                cat_totals.values,
                labels=None,  # Remove labels from pie function
                autopct="%1.1f%%",
                startangle=90,
                colors=colors,
                wedgeprops={"edgecolor": "white", "linewidth": 1.5},
                textprops={"color": "white", "fontsize": 10}
            )
            
            # Set autopct text color to black for better readability
            for autotext in autotexts:
                autotext.set_color('black')
                autotext.set_fontweight('bold')
            
            # Create horizontal legend instead of radial labels
            ax.legend(wedges, cat_totals.index,
                     title="Categories",
                     loc="center left",
                     bbox_to_anchor=(1, 0, 0.5, 1),
                     frameon=False,
                     labelcolor="white")
            
            # Set legend title color and weight separately
            legend = ax.get_legend()
            legend.get_title().set_color("white")
            legend.get_title().set_weight("bold")
            
            # Set title with proper color and padding
            ax.set_title("Expenses per Category", fontsize=14, pad=20, color="white", weight='bold')
        else:
            # No valid categories with positive amounts
            ax.axis('off')  # This removes the axes completely
            ax.text(0.5, 0.5, "No expense categories\nwith positive amounts", 
                   ha="center", va="center", fontsize=12, color="white", 
                   weight='bold', linespacing=1.5)
            ax.set_title("Expenses per Category", fontsize=14, pad=20, color="white", weight='bold')
    else:
        # No expenses at all
        ax.axis('off')  # This removes the axes completely
        ax.text(0.5, 0.5, "No Expenses Found", 
               ha="center", va="center", fontsize=14, color="white", 
               weight='bold')
        ax.text(0.5, 0.4, "Add some expense transactions\nto see the chart", 
               ha="center", va="center", fontsize=11, color="lightgray",
               linespacing=1.5)

    # Ensure tight layout and redraw
    fig.tight_layout()
    canvas.draw()

    # ... rest of your budget progress code remains the same ...
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

    budget_income_label.config(text=f"Income: ₱{total_income:.2f}")
    budget_spent_label.config(text=f"Spent: ₱{total_expenses:.2f}")
    budget_remaining_label.config(text=f"Remaining: ₱{remaining:.2f}")

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

#Logo/Favicon
icon_image = tk.PhotoImage(file="C:/Users/canci/OneDrive/Desktop/Personal Finance Tracker/logo.png")
root.iconphoto (False, icon_image)

# === NOTEBOOK (TABS) ===
notebook = ttk.Notebook(root)
notebook.pack(fill="both", expand=True)

tracker_tab = ttk.Frame(notebook)
summary_tab = ttk.Frame(notebook)

notebook.add(tracker_tab, text="Tracker")
notebook.add(summary_tab, text="Statistics")


# === TRACKER TAB ===
## --- Add Transaction Frame ---
top_frame = ttk.LabelFrame(tracker_tab, text="Add Transaction")
top_frame.pack(fill="x", padx=10, pady=10)

# Input fields
ttk.Label(top_frame, text="Category:").grid(row=0, column=0, padx=5, pady=5)
category_entry = ttk.Combobox(
    top_frame,
    values=[
        "",
        "Utility",
        "Payment",
        "Food",
        "Transport",
        "Groceries",
        "Bills",
        "School",
        "Shopping",
        "Entertainment",
        "Subscriptions",
        "Personal Care",
        "Health",
        "Savings",
        "Investments",
        "Debt",
        "Gifts / Donations",
        "Miscellaneous",
    ],
    state= "readonly",
    width=13,
    font=("Segoe UI", 10)
)
category_entry.configure(validate="key", 
                        validatecommand=(root.register(lambda p: len(p) <= 20), '%P'))
category_entry.grid(row=0, column=1, padx=5, pady=5)

ttk.Label(top_frame, text="Type:").grid(row=0, column=2, padx=5, pady=5)
type_entry = ttk.Combobox(top_frame, values=["", "Income", "Expense"], state="readonly", width=13)
type_entry.grid(row=0, column=3, padx=5, pady=5)

ttk.Label(top_frame, text="Amount:").grid(row=1, column=0, padx=5, pady=5)
amount_entry = ttk.Entry(top_frame, width=15, font=("Segoe UI", 10))
amount_entry.configure(validate="key", 
                      validatecommand=(root.register(lambda p: len(p) <= 6), '%P'))
amount_entry.grid(row=1, column=1, padx=5, pady=5)

ttk.Label(top_frame, text="Notes:").grid(row=2, column=0, padx=5, pady=5)
note_entry = ttk.Entry(top_frame, width=37, font=("Segoe UI", 10))
note_entry.configure(validate="key", 
                    validatecommand=(root.register(lambda p: len(p) <= 50), '%P'))
note_entry.grid(row=2, column=1, columnspan=3, padx=5, pady=5)

def import_csv():
    global df

    file_path = filedialog.askopenfilename(
        filetypes=[("CSV Files", "*.csv")],
        title="Import CSV Transactions"
    )
    if not file_path:
        return

    try:
        imported_df = pd.read_csv(file_path)
        imported_df.columns = imported_df.columns.str.strip().str.title()

        for col in COLUMNS:
            if col not in imported_df.columns:
                messagebox.showerror("Invalid CSV",
                    f"Missing required column: {col}")
                return

        imported_df["Amount"] = (
            imported_df["Amount"]
            .astype(str)
            .str.replace("₱", "")
            .str.replace(",", "")
            .str.strip()
            .astype(float)
        )

        imported_df["Type"] = imported_df["Type"].str.title()

        imported_df = imported_df[
            imported_df["Type"].isin(["Income", "Expense"])
        ]

        imported_df["Date"] = pd.to_datetime(
            imported_df["Date"], errors="coerce"
        ).dt.strftime("%d %b %Y")

        imported_df = imported_df.dropna(subset=["Date"])

        df = pd.concat([df, imported_df], ignore_index=True)

        save_data()
        refresh_treeview()
        update_dashboard()

        messagebox.showinfo("Success", "CSV imported successfully!")

    except Exception as e:
        messagebox.showerror("Error", f"Failed to import CSV:\n{e}")


## --- Buttons Frame ---
button_frame = ttk.Frame(tracker_tab)
button_frame.pack(fill="x", padx=10, pady=5)

ttk.Button(button_frame, text="Add Entry", command=add_entry, bootstyle="success").pack(side="left", padx=5)
ttk.Button(button_frame, text="Edit Entry", command=edit_entry, bootstyle="info").pack(side="left", padx=5)
ttk.Button(button_frame, text="Delete Entry", command=delete_entry, bootstyle="danger").pack(side="left", padx=5)
ttk.Button(button_frame, text="Export CSV", command=export_csv, bootstyle="warning").pack(side="left", padx=5)
ttk.Button(button_frame, text="Import CSV", command=import_csv, bootstyle="light").pack(side="left", padx=5)


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

# Configure Treeview styles: larger header font, larger row font and row height
style = tb.Style()
style.configure("Treeview", font=("Segoe UI", 11), rowheight=30)
style.configure("Treeview.Heading", relief="solid", borderwidth=1, font=("Segoe UI", 12, "bold"))
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

# Adjust scrolling for fullscreen
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

# Enable mouse wheel scrolling
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

budget_income_label = ttk.Label(budget_info_frame, text="Income: ₱0.00", font=("Segoe UI", 10))
budget_income_label.pack(side="left", padx=5)

budget_spent_label = ttk.Label(budget_info_frame, text="Spent: ₱0.00", font=("Segoe UI", 10))
budget_spent_label.pack(side="left", padx=5)

budget_remaining_label = ttk.Label(budget_info_frame, text="Remaining: ₱0.00", font=("Segoe UI", 10))
budget_remaining_label.pack(side="right", padx=5)

budget_progress = ttk.Progressbar(budget_frame, mode='determinate', bootstyle="success")
budget_progress.pack(fill="x", padx=10, pady=10)

budget_percent_label = ttk.Label(budget_frame, text="0% of budget used", font=("Segoe UI", 11, "bold"))
budget_percent_label.pack(pady=5)

# === BINDINGS & INIT ===
month_dropdown.bind("<<ComboboxSelected>>", lambda e: update_dashboard())
root.bind("<Configure>", toggle_scrolling)
refresh_treeview()
toggle_scrolling()
update_dashboard()

root.mainloop()
