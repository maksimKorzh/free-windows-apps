import csv
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, simpledialog, font

class CSVEditor:
    def __init__(self, root):
        self.root = root
        self.root.title("CSV Editor")
        self.filename = None
        self.columns = []
        self.data = []
        self.make_menu()
        style = ttk.Style()
        style.configure("Treeview", font=("Segoe UI", 11), rowheight=28)
        style.configure("Treeview.Heading", font=("Segoe UI", 11, "bold"))
        table_frame = ttk.Frame(root)
        table_frame.pack(fill="both", expand=True)
        self.tree = ttk.Treeview(table_frame, show="headings")
        self.tree.bind("<Double-1>", self.double_click)
        vsb = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview)
        hsb = ttk.Scrollbar(table_frame, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        self.tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")
        table_frame.grid_rowconfigure(0, weight=1)
        table_frame.grid_columnconfigure(0, weight=1)

    def make_menu(self):
        menu = tk.Menu(self.root)
        file_menu = tk.Menu(menu, tearoff=False)
        file_menu.add_command(label="New", command=self.new_csv)
        file_menu.add_command(label="Open", command=self.open_csv)
        file_menu.add_command(label="Save", command=self.save_csv)
        file_menu.add_command(label="Save As", command=self.save_as)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.root.destroy)
        menu.add_cascade(label="File", menu=file_menu)
        edit_menu = tk.Menu(menu, tearoff=False)
        edit_menu.add_command(label="Append Row", command=self.add_row)
        edit_menu.add_command(label="Pop Row", command=self.delete_row)
        edit_menu.add_separator()
        edit_menu.add_command(label="Append Column", command=self.add_column)
        edit_menu.add_command(label="Pop Column", command=self.delete_column)
        menu.add_cascade(label="Edit", menu=edit_menu)
        self.root.config(menu=menu)

    def new_csv(self):
        count = simpledialog.askinteger(
            "New CSV",
            "Number of columns:",
            parent=self.root,
            minvalue=1,
            initialvalue=3
        )
        if count is None: return
        self.filename = None
        self.columns = []
        self.data = []
        self.data.append([""] * count)
        for i in range(count):
            name = ""
            n = i
            while True:
                name = chr(65 + (n % 26)) + name
                n = n // 26 - 1
                if n < 0: break
            self.columns.append(name)
        self.refresh_tree()

    def open_csv(self):
        filename = filedialog.askopenfilename(
            filetypes=[("CSV Files", "*.csv")]
        )
        if not filename: return
        with open(filename, newline="", encoding="utf-8") as f:
            reader = csv.reader(f)
            try: self.columns = next(reader)
            except StopIteration: return
            self.data = [row for row in reader if len(row)]
        self.filename = filename
        self.refresh_tree()

    def refresh_tree(self):
        self.tree.delete(*self.tree.get_children())
        self.tree["columns"] = self.columns
        for col in self.columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=80, minwidth=80, stretch=False)
        for row in self.data:
            values = row + [""] * (len(self.columns) - len(row))
            self.tree.insert("", "end", values=values)
        header_font = font.Font(font=("Segoe UI", 11, "bold"))
        cell_font = font.Font(font=("Segoe UI", 11))
        for i, col in enumerate(self.columns):
            width = header_font.measure(col)
            for row in self.data:
                if i < len(row):
                    width = max(width, cell_font.measure(str(row[i])))
            self.tree.column(col, width=width+20)

    def double_click(self, event):
        region = self.tree.identify_region(event.x, event.y)
        if region == "heading": self.rename_column(event)
        elif region == "cell": self.edit_cell(event)

    def rename_column(self, event):
        column = self.tree.identify_column(event.x)
        if not column: return
        index = int(column[1:]) - 1
        new_name = simpledialog.askstring(
            "Rename Column",
            "Column name:",
            initialvalue=self.columns[index],
            parent=self.root
        )
        if not new_name: return
        self.columns[index] = new_name
        self.refresh_tree()

    def edit_cell(self, event):
        item = self.tree.identify_row(event.y)
        column = self.tree.identify_column(event.x)
        if not item or not column: return
        row_index = self.tree.index(item)
        col_index = int(column[1:]) - 1
        x, y, width, height = self.tree.bbox(item, column)
        try: value = self.data[row_index][col_index]
        except IndexError: value = ""
        entry = tk.Entry(self.tree, font=("Segoe UI", 11))
        entry.place(x=x, y=y, width=width, height=height)
        entry.insert(0, value)
        entry.select_range(0, tk.END)
        entry.focus()
        def save(event=None):
            new_value = entry.get()
            while len(self.data[row_index]) < len(self.columns):
                self.data[row_index].append("")
            self.data[row_index][col_index] = new_value
            self.tree.set(item, column, new_value)
            entry.destroy()
        entry.bind("<Return>", save)
        entry.bind("<FocusOut>", save)
        entry.bind("<Escape>", lambda e: entry.destroy())

    def save_csv(self):
        if not self.filename:
            self.save_as()
            return
        with open(self.filename, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(self.columns)
            writer.writerows(self.data)
        messagebox.showinfo("Saved", "CSV saved successfully.")

    def save_as(self):
        filename = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV Files", "*.csv")]
        )
        if not filename: return
        self.filename = filename
        self.save_csv()

    def add_row(self):
        if not self.columns:
            messagebox.showwarning(
                "No columns",
                "Create a new CSV or open an existing one first."
            )
            return
        row = [""] * len(self.columns)
        self.data.append(row)
        self.tree.insert("", "end", values=row)

    def delete_row(self):
        items = list(self.tree.selection())
        if not items: return
        indexes = sorted(
            (self.tree.index(item) for item in items),
            reverse=True
        )
        for index in indexes: del self.data[index]
        for item in items: self.tree.delete(item)
    
    def add_column(self):
        if not self.columns:
            messagebox.showwarning(
                "No CSV",
                "Create a new CSV or open an existing one first."
            )
            return

        index = len(self.columns)
        name = ""
        n = index
        while True:
            name = chr(65 + (n % 26)) + name
            n = n // 26 - 1
            if n < 0:
                break
        self.columns.append(name)
        for row in self.data:
            row.append("")
        self.refresh_tree()

    def delete_column(self):
        if not self.columns: return
        self.columns.pop()
        for row in self.data:
            if row: row.pop()
        self.refresh_tree()

if __name__ == "__main__":
    root = tk.Tk()
    root.title("CSV Editor")
    root.geometry("900x500")
    CSVEditor(root)
    root.mainloop()