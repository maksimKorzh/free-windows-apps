# Packages
import json
import requests
import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
from tkinter import filedialog
from bs4 import BeautifulSoup, Tag, NavigableString

# Main window
class GUI(tk.Frame):
    def __init__(self, root, *args, **kwargs):
        # Main workspace panel
        view_panel = tk.Frame(root)
        view_panel.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Left panel
        panel_left = tk.Frame(view_panel)
        panel_left.pack(side="left", fill="both", expand=True, padx=5, pady=5)
        
        # Right panel
        panel_right = tk.Frame(view_panel)
        panel_right.pack(side="left", fill="both", expand=True, padx=5, pady=5)
        
        # Selector search panel
        selector_panel = tk.Frame(panel_left)
        selector_panel.pack(fill="x", pady=5)
        self.selector_var = tk.StringVar()
        
        # Selector search entry
        ttk.Entry(
            selector_panel,
            textvariable=self.selector_var
        ).pack(side="left", fill="x", expand=True)

        # Selector search button
        ttk.Button(
            selector_panel,
            text="Select",
            command=self.search
        ).pack(side="left")
        
        # Search results storage & curent index
        self.search_results = []
        self.current = None

        # Tree frame, used for scroll bar
        tree_frame = ttk.Frame(panel_left)
        tree_frame.pack(fill="both", expand=True)
        
        # Tree view scroll bar
        tree_scroll = ttk.Scrollbar(tree_frame, orient="vertical")
        tree_scroll.pack(side="right", fill="y")

        # Parsed HTML tree
        self.tree = ttk.Treeview(
            tree_frame,
            yscrollcommand=tree_scroll.set
        )
        self.tree.pack(side="left", fill="both", expand=True)

        # Bind vertical scroll bar
        tree_scroll.config(command=self.tree.yview)
        
        # Previous selector instance
        ttk.Button(
            panel_left,
            text="Previous",
            command=self.previous
        ).pack(side="left", fill="x", expand=True, pady=5)

        # Next selector instance
        ttk.Button(
            panel_left,
            text="Next",
            command=self.next
        ).pack(side="left", fill="x", expand=True, pady=5)

        # Scrape panel
        scrape_panel = tk.Frame(panel_right)
        scrape_panel.pack(fill="x", pady=5)
        self.addr_var = tk.StringVar()

        # Crawl through all links
        ttk.Button(
            scrape_panel,
            text="Crawl",
            command=self.crawl
        ).pack(side="left")

        # Address entry
        ttk.Entry(
            scrape_panel,
            textvariable=self.addr_var,
        ).pack(side="left", fill="x", expand=True)

        # Start scraper button
        ttk.Button(
            scrape_panel,
            text="Scrape",
            command=self.make_request
        ).pack(side="left")
        
        # Selectors frame, used for scroll bar
        selector_frame = ttk.Frame(panel_right)
        selector_frame.pack(fill="both", expand=True)
        
        # Selector view scroll bar
        selector_scroll = ttk.Scrollbar(selector_frame, orient="vertical")
        selector_scroll.pack(side="right", fill="y")

        # Extracted selectors
        self.selectors = tk.Text(
            selector_frame,
            yscrollcommand=selector_scroll.set,
            width=25, wrap="none")
        self.selectors.pack(fill="both", expand=True)
        
        # Bind vertical scroll bar
        selector_scroll.config(command=self.selectors.yview)
        
        # Add selector
        ttk.Button(
            panel_right,
            text="Add",
            command=self.add
        ).pack(side="left", fill="x", expand=True, pady=5)
        
        # Remove selector
        ttk.Button(
            panel_right,
            text="Remove",
            command=self.remove
        ).pack(side="left", fill="x", expand=True, pady=5)
        
        # Load selectors file
        ttk.Button(
            panel_right,
            text="Load",
            command=self.load
        ).pack(side="left", fill="x", expand=True, pady=5)
        
        # Save selectors file
        ttk.Button(
            panel_right,
            text="Save",
            command=self.save
        ).pack(side="left", fill="x", expand=True, pady=5)
        
        # Selectors storage
        self.data = []
        self.print_selectors()
    
    # Find next selector
    def next(self):
        if self.current is not None:
            if self.current < len(self.search_results)-1:
                self.current += 1
            
            else:
                self.current = 0
            
            self.highlight(self.search_results[self.current])

    # Find previous selector
    def previous(self):
        if self.current is not None:
            if self.current > 0:
                self.current -= 1

            else:
                self.current = len(self.search_results)-1
            
            self.highlight(self.search_results[self.current])

    # Add selector
    def add(self):
        sel = self.tree.selection()

        if not sel:
            return

        tag = self.node_map[sel[0]]

        selector = self.css_selector(tag)
        text = self.extract_text(selector, self.content)
        
        self.data.append({
            'text': text,
            'selector': selector
        })
        
        self.print_selectors()
    
    # Remove selector
    def remove(self):
        sel = self.tree.selection()

        try:
            self.data.pop()
        except:
            messagebox.showerror("Error", "Selector is not deleted")
        
        self.print_selectors()
    
    # Load selectors from file
    def load(self):
        filename = filedialog.askopenfilename(
            title="Open selectors file",
            filetypes=[("JSON files", "*.json")]
        )

        if filename:
            with open(filename, "r", encoding="utf-8") as f:
                self.data = json.loads(f.read())
                self.print_selectors()
        else:
            messagebox.showerror("Error", "File is not loaded")

    # Save selectors to file
    def save(self):
        filename = filedialog.asksaveasfilename(
            title="Save selectors file",
            defaultextension=".json",
            filetypes=[("JSON files", "*.json")]
        )

        if filename:
            with open(filename, "w", encoding="utf-8") as f:
                f.write(json.dumps(self.data, indent=2))
        else:
            messagebox.showerror("Error", "File is not saved")
    
    # Extract text from selector
    def extract_text(self, selector, content):
        text = content.select_one(selector).get_text(separator=" ", strip=True)
        
        if "href" in content.select_one(selector).attrs.keys():
            text = self.content.select_one(selector).attrs["href"]
        
        return text

    # Crawl through links
    def crawl(self):
        # Make sure selectors are loaded
        if not len(self.data):
            messagebox.showerror("Error", "Selectors are not loaded")
            return
        
        # Open file with URLs
        filename = filedialog.askopenfilename(
            title="Open links file",
            filetypes=[("Text files", "*.txt")]
        )

        # Success
        if filename:
            with open(filename, "r", encoding="utf-8") as f:
                # List of URLs
                urls = f.read().split('\n')
                
                # Scraped data
                data = []
                
                # Scraping starts here
                messagebox.showinfo("Info", "Scraping data, please wait")
                
                # Loop over URLs
                for url in urls:
                    try:
                        # Make HTTP requests & parse response
                        response = requests.get(url)
                        content = BeautifulSoup(response.text, 'lxml')
                        
                        # Single data row
                        line = []
                        
                        # Extract data
                        for item in self.data:
                            # Extract text
                            text = self.extract_text(item["selector"], content)
                            
                            # Save single selector data
                            line.append(text)

                        # Save single data row
                        data.append(line)
                    
                    except:
                        messagebox.showerror("Error", f"Failed scraping '{url}'")
                
                # Scraping is done
                messagebox.showinfo("Info", "Scraping has been completed")
                
                # Save scraped data
                filename = filedialog.asksaveasfilename(
                    title="Save scraped data",
                    defaultextension=".json",
                    filetypes=[("JSON files", "*.json")]
                )
                
                # Success
                if filename:
                    with open(filename, "w", encoding="utf-8") as f:
                        f.write(json.dumps(data, indent=2))
                
                # Failure
                else:
                    messagebox.showerror("Error", "File is not saved")
        
        # Failure
        else:
            messagebox.showerror("Error", "File is not loaded")

    # Update used selectors view
    def print_selectors(self):
        self.selectors.delete("1.0", "end")
        self.selectors.insert("1.0", json.dumps(self.data, indent=2))

    # Make HTTP request
    def make_request(self):
        # Get URL or local file addr
        addr = self.addr_var.get().lower().strip()
        
        # Make sure addr is available
        if not addr:
            messagebox.showerror("Error", "Enter URL or addr of the local file containing URLs")
            return
        
        # Make HTTP request
        response = requests.get(addr)
        
        # Success
        if response.status_code == 200:
            self.content = BeautifulSoup(response.text, 'lxml')
            self.node_map = {}
            self.checked = {}
            self.data = []
            self.tree.delete(*self.tree.get_children())
            self.build_tree("", self.content)
            self.print_selectors()
        
        # Failure
        else:
            messagebox.showerror("Error", "Enter URL or addr of the local file containing URLs")
            return

    # Build HTML tree
    def build_tree(self, parent, node):
        if isinstance(node, NavigableString):
            return

        if not isinstance(node, Tag):
            return

        if not bool(node.get_text(strip=True)):
            return

        iid = self.tree.insert(
            parent,
            "end",
            text=self.make_label(node),
            open=True
        )

        self.node_map[iid] = node
        self.checked[iid] = False

        for child in node.children:
            self.build_tree(iid, child)

    # Search selector in document
    def search(self):
        self.search_results = []
        self.current = None
        query = self.selector_var.get().lower().strip()

        if not query:
            return

        for iid, tag in self.node_map.items():
            if query in tag.get_text(" ", strip=True).lower():
                self.search_results.append(iid)
        
        if len(self.search_results):
            self.current = 0
            self.highlight(self.search_results[self.current])

    # Highlight matching selector
    def highlight(self, iid):
        parent = self.tree.parent(iid)
        while parent:
            self.tree.item(parent, open=True)
            parent = self.tree.parent(parent)

        self.tree.selection_set(iid)
        self.tree.focus(iid)
        self.tree.see(iid)

    # Label selector
    def make_label(self, tag):
        text = tag.get_text(" ", strip=True)

        if len(text) > 40:
            text = text[:37] + "..."
        
        return f"<{tag.name}> {text}"
    
    # Convert tag into a valid CSS selector
    def css_selector(self, tag):
        parts = []

        while tag and tag.name != "[document]":
            parent = tag.parent

            if parent is None:
                break

            siblings = [
                x for x in parent.find_all(tag.name, recursive=False)
            ]

            if len(siblings) == 1:
                part = tag.name
            else:
                idx = siblings.index(tag) + 1
                part = f"{tag.name}" + f":nth-of-type({idx})"

            parts.append(part)

            tag = parent

        return " > ".join(reversed(parts))

# Main driver
if __name__ == "__main__":
    root = tk.Tk()
    root.geometry("800x600")
    root.minsize(800, 600)
    root.title("Visual Web Scraper")
    app = GUI(root)
    root.mainloop()