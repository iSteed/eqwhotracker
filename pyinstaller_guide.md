# Creating a Standalone EverQuest /who Tracker .exe

This guide shows how to create a standalone .exe file that users can simply double-click to run - no Python installation required!

## For the App Creator (One-Time Setup)

### Step 1: Install Python and PyInstaller
```bash
# Install Python from python.org (if not already installed)
# Then install PyInstaller
pip install pyinstaller
```

### Step 2: Save the Tracker Script
Save this as `eq_who_tracker.py`:

```python
#!/usr/bin/env python3
"""
EverQuest /who Tracker - Desktop Application
A reliable file monitor for capturing /who results during raids.
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import os
import time
import threading
from datetime import datetime
import re
import json

class EQWhoTracker:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("EverQuest /who Tracker - Raid Edition")
        self.root.geometry("1200x800")
        self.root.configure(bg='#f0f0f0')
        
        # Application state
        self.log_file_path = None
        self.monitoring = False
        self.last_file_size = 0
        self.initial_file_size = 0
        self.who_results = []
        self.selected_result_index = None
        self.monitor_thread = None
        self.stop_monitoring = False
        
        # Load settings
        self.settings_file = "eq_tracker_settings.json"
        self.load_settings()
        
        self.create_widgets()
        self.setup_styles()
        
        # Auto-load last used file if it exists
        if self.log_file_path and os.path.exists(self.log_file_path):
            self.load_log_file(self.log_file_path)
            
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
    def setup_styles(self):
        """Configure custom styles for better appearance"""
        style = ttk.Style()
        style.theme_use('clam')
        
        # Configure button styles
        style.configure('Action.TButton', font=('Arial', 10, 'bold'))
        style.configure('Success.TButton', background='#28a745', foreground='white')
        style.configure('Danger.TButton', background='#dc3545', foreground='white')
        style.configure('Primary.TButton', background='#007bff', foreground='white')
        
    def create_widgets(self):
        """Create the main UI"""
        # Main title
        title_frame = tk.Frame(self.root, bg='#2c3e50', height=80)
        title_frame.pack(fill='x', padx=0, pady=0)
        title_frame.pack_propagate(False)
        
        title_label = tk.Label(title_frame, text="🎮 EverQuest /who Tracker - Raid Edition", 
                              font=('Arial', 18, 'bold'), fg='white', bg='#2c3e50')
        title_label.pack(expand=True)
        
        # Main container
        main_frame = tk.Frame(self.root, bg='#f0f0f0')
        main_frame.pack(fill='both', expand=True, padx=20, pady=20)
        
        # File selection section
        file_frame = tk.LabelFrame(main_frame, text="📁 Log File Setup", 
                                  font=('Arial', 12, 'bold'), bg='#f0f0f0', fg='#2c3e50')
        file_frame.pack(fill='x', pady=(0, 15))
        
        file_inner = tk.Frame(file_frame, bg='#f0f0f0')
        file_inner.pack(fill='x', padx=15, pady=15)
        
        ttk.Button(file_inner, text="Select EverQuest Log File", 
                  command=self.select_log_file, style='Action.TButton').pack(side='left')
        
        self.file_label = tk.Label(file_inner, text="No file selected", 
                                  font=('Arial', 10), bg='#f0f0f0', fg='#666')
        self.file_label.pack(side='left', padx=(15, 0))
        
        # Monitoring controls
        control_frame = tk.LabelFrame(main_frame, text="📡 Monitoring Control", 
                                     font=('Arial', 12, 'bold'), bg='#f0f0f0', fg='#2c3e50')
        control_frame.pack(fill='x', pady=(0, 15))
        
        control_inner = tk.Frame(control_frame, bg='#f0f0f0')
        control_inner.pack(fill='x', padx=15, pady=15)
        
        self.start_btn = ttk.Button(control_inner, text="▶ Start Monitoring", 
                                   command=self.start_monitoring, style='Success.TButton')
        self.start_btn.pack(side='left', padx=(0, 10))
        
        self.stop_btn = ttk.Button(control_inner, text="⏹ Stop Monitoring", 
                                  command=self.stop_monitoring_cmd, style='Danger.TButton', state='disabled')
        self.stop_btn.pack(side='left', padx=(0, 10))
        
        self.clear_btn = ttk.Button(control_inner, text="🗑 Clear Results", 
                                   command=self.clear_results, style='Action.TButton')
        self.clear_btn.pack(side='left', padx=(0, 10))
        
        # Status display
        self.status_label = tk.Label(control_inner, text="Status: Ready to select log file", 
                                    font=('Arial', 10, 'bold'), bg='#f0f0f0', fg='#007bff')
        self.status_label.pack(side='left', padx=(20, 0))
        
        # Results count
        self.count_label = tk.Label(control_inner, text="Results: 0", 
                                   font=('Arial', 10, 'bold'), bg='#f0f0f0', fg='#28a745')
        self.count_label.pack(side='right')
        
        # Results section
        results_frame = tk.LabelFrame(main_frame, text="📊 Captured /who Results", 
                                     font=('Arial', 12, 'bold'), bg='#f0f0f0', fg='#2c3e50')
        results_frame.pack(fill='both', expand=True)
        
        # Create paned window for split layout
        paned = ttk.PanedWindow(results_frame, orient='horizontal')
        paned.pack(fill='both', expand=True, padx=15, pady=15)
        
        # Left panel - Results list
        left_frame = tk.Frame(paned, bg='white', relief='sunken', bd=1)
        paned.add(left_frame, weight=1)
        
        list_label = tk.Label(left_frame, text="Results List", font=('Arial', 10, 'bold'), 
                             bg='#f8f9fa', fg='#495057')
        list_label.pack(fill='x', padx=2, pady=2)
        
        # Listbox with scrollbar
        list_scroll_frame = tk.Frame(left_frame, bg='white')
        list_scroll_frame.pack(fill='both', expand=True, padx=2, pady=2)
        
        self.results_listbox = tk.Listbox(list_scroll_frame, font=('Arial', 9), 
                                         selectmode='single', bg='white')
        list_scrollbar = tk.Scrollbar(list_scroll_frame, orient='vertical', command=self.results_listbox.yview)
        self.results_listbox.configure(yscrollcommand=list_scrollbar.set)
        self.results_listbox.bind('<<ListboxSelect>>', self.on_result_select)
        
        self.results_listbox.pack(side='left', fill='both', expand=True)
        list_scrollbar.pack(side='right', fill='y')
        
        # Right panel - Result details
        right_frame = tk.Frame(paned, bg='white', relief='sunken', bd=1)
        paned.add(right_frame, weight=2)
        
        detail_header = tk.Frame(right_frame, bg='#f8f9fa')
        detail_header.pack(fill='x', padx=2, pady=2)
        
        detail_label = tk.Label(detail_header, text="Selected Result", font=('Arial', 10, 'bold'), 
                               bg='#f8f9fa', fg='#495057')
        detail_label.pack(side='left')
        
        # Detail control buttons
        button_frame = tk.Frame(detail_header, bg='#f8f9fa')
        button_frame.pack(side='right')
        
        self.copy_btn = ttk.Button(button_frame, text="📋 Copy", 
                                  command=self.copy_selected_result, state='disabled')
        self.copy_btn.pack(side='left', padx=(0, 5))
        
        self.save_btn = ttk.Button(button_frame, text="💾 Save As...", 
                                  command=self.save_selected_result, state='disabled')
        self.save_btn.pack(side='left')
        
        # Result content display
        self.result_text = scrolledtext.ScrolledText(right_frame, wrap='word', 
                                                    font=('Courier New', 9), 
                                                    bg='#f8f9fa', state='normal')
        self.result_text.pack(fill='both', expand=True, padx=2, pady=2)
        
        # Make text area read-only but selectable
        self.result_text.bind("<Key>", lambda e: "break")  # Prevent editing
        self.result_text.insert(1.0, "Select a result from the list to view details")
        
        # Instructions
        instructions = ("💡 Instructions: Select your EverQuest log file, click 'Start Monitoring', then use /who commands in-game. "
                       "Results will be captured automatically and appear in the list on the left. "
                       "Select any result to view details and copy/save.")
        
        instr_label = tk.Label(main_frame, text=instructions, font=('Arial', 9), 
                              bg='#e3f2fd', fg='#1565c0', wraplength=800, justify='left')
        instr_label.pack(fill='x', pady=(15, 0))
        
    def select_log_file(self):
        """Open file dialog to select EQ log file"""
        initial_dir = os.path.expanduser("~/Documents")
        if self.log_file_path:
            initial_dir = os.path.dirname(self.log_file_path)
            
        file_path = filedialog.askopenfilename(
            title="Select EverQuest Log File",
            filetypes=[("Log files", "*.txt"), ("All files", "*.*")],
            initialdir=initial_dir
        )
        
        if file_path:
            self.load_log_file(file_path)
            
    def load_log_file(self, file_path):
        """Load the selected log file"""
        try:
            if not os.path.exists(file_path):
                messagebox.showerror("Error", "Selected file does not exist!")
                return
                
            self.log_file_path = file_path
            self.last_file_size = os.path.getsize(file_path)
            
            # Update UI
            filename = os.path.basename(file_path)
            file_size = self.format_file_size(self.last_file_size)
            self.file_label.config(text=f"📄 {filename} ({file_size})", fg='#28a745')
            self.start_btn.config(state='normal')
            self.update_status("File loaded - Ready to start monitoring", '#007bff')
            
            # Save settings
            self.save_settings()
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load file: {str(e)}")
            
    def start_monitoring(self):
        """Start monitoring the log file"""
        if not self.log_file_path or not os.path.exists(self.log_file_path):
            messagebox.showerror("Error", "Please select a valid log file first!")
            return
            
        try:
            # Set initial file size baseline (only capture new content)
            self.initial_file_size = os.path.getsize(self.log_file_path)
            self.last_file_size = self.initial_file_size
            
            # Update UI
            self.monitoring = True
            self.stop_monitoring = False
            self.start_btn.config(state='disabled')
            self.stop_btn.config(state='normal')
            self.update_status("🟢 Monitoring Active - Watching for new /who results", '#28a745')
            
            # Start monitoring thread
            self.monitor_thread = threading.Thread(target=self.monitor_file, daemon=True)
            self.monitor_thread.start()
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to start monitoring: {str(e)}")
            
    def stop_monitoring_cmd(self):
        """Stop monitoring the log file"""
        self.monitoring = False
        self.stop_monitoring = True
        
        self.start_btn.config(state='normal')
        self.stop_btn.config(state='disabled')
        self.update_status("⏹ Monitoring Stopped", '#dc3545')
        
    def monitor_file(self):
        """Background thread to monitor the log file"""
        while self.monitoring and not self.stop_monitoring:
            try:
                if not os.path.exists(self.log_file_path):
                    self.root.after(0, lambda: self.update_status("❌ Log file not found!", '#dc3545'))
                    break
                    
                current_size = os.path.getsize(self.log_file_path)
                
                if current_size > self.last_file_size:
                    # Read only the new content
                    with open(self.log_file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        f.seek(self.last_file_size)
                        new_content = f.read()
                        
                    self.last_file_size = current_size
                    
                    # Parse for /who results
                    self.parse_who_results(new_content)
                    
                time.sleep(1)  # Check every second
                
            except Exception as e:
                self.root.after(0, lambda: self.update_status(f"❌ Monitoring error: {str(e)}", '#dc3545'))
                break
                
        self.monitoring = False
        
    def parse_who_results(self, content):
        """Parse content for /who results"""
        if not content.strip():
            return
            
        lines = content.split('\n')
        current_who = []
        in_who_result = False
        who_timestamp = None
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            # Look for start of /who result
            if 'Players on EverQuest:' in line:
                in_who_result = True
                current_who = [line]
                # Extract timestamp
                timestamp_match = re.match(r'^\[([^\]]+)\]', line)
                who_timestamp = timestamp_match.group(1) if timestamp_match else datetime.now().strftime("%a %b %d %H:%M:%S %Y")
                continue
                
            if in_who_result:
                current_who.append(line)
                
                # Look for end of /who result
                if 'There are' in line and 'players in' in line:
                    # Complete /who result found
                    who_content = '\n'.join(current_who)
                    self.root.after(0, lambda w=who_content, t=who_timestamp: self.add_who_result(w, t))
                    
                    in_who_result = False
                    current_who = []
                    who_timestamp = None
                    
    def add_who_result(self, content, timestamp):
        """Add a new /who result to the list"""
        # Check for duplicates
        for existing in self.who_results:
            if existing['content'] == content and existing['timestamp'] == timestamp:
                return  # Duplicate found, don't add
                
        # Extract location and player count for display
        location_match = re.search(r'There are \d+ players in (.+)\.', content)
        location = location_match.group(1) if location_match else "Unknown"
        
        count_match = re.search(r'There are (\d+) players', content)
        player_count = count_match.group(1) if count_match else "?"
        
        result = {
            'timestamp': timestamp,
            'content': content,
            'location': location,
            'player_count': player_count,
            'display_name': f"[{timestamp}] {player_count} players in {location}"
        }
        
        self.who_results.append(result)
        
        # Update UI
        self.results_listbox.insert(0, result['display_name'])  # Add to top
        self.update_count_label()
        
        # Show brief notification in status
        self.update_status(f"✅ New /who captured: {player_count} players in {location}", '#28a745')
        
    def on_result_select(self, event):
        """Handle result selection from listbox"""
        selection = self.results_listbox.curselection()
        if not selection:
            self.selected_result_index = None
            self.result_text.config(state='normal')
            self.result_text.delete(1.0, tk.END)
            self.result_text.insert(1.0, "Select a result from the list to view details")
            self.result_text.config(state='disabled')
            self.copy_btn.config(state='disabled')
            self.save_btn.config(state='disabled')
            return
            
        # Get selected result (remember list is reversed)
        list_index = selection[0]
        result_index = len(self.who_results) - 1 - list_index
        
        if 0 <= result_index < len(self.who_results):
            self.selected_result_index = result_index
            result = self.who_results[result_index]
            
            # Display result content
            self.result_text.config(state='normal')
            self.result_text.delete(1.0, tk.END)
            self.result_text.insert(1.0, f"Timestamp: {result['timestamp']}\n")
            self.result_text.insert(tk.END, f"Location: {result['location']}\n")
            self.result_text.insert(tk.END, f"Player Count: {result['player_count']}\n")
            self.result_text.insert(tk.END, "\n" + "="*50 + "\n\n")
            self.result_text.insert(tk.END, result['content'])
            self.result_text.config(state='disabled')
            
            self.copy_btn.config(state='normal')
            self.save_btn.config(state='normal')
            
    def copy_selected_result(self):
        """Copy selected result to clipboard"""
        if self.selected_result_index is None:
            return
            
        result = self.who_results[self.selected_result_index]
        content = f"[{result['timestamp']}]\n{result['content']}"
        
        self.root.clipboard_clear()
        self.root.clipboard_append(content)
        self.root.update()  # Ensure clipboard is updated
        
        self.update_status("📋 Result copied to clipboard!", '#28a745')
        
    def save_selected_result(self):
        """Save selected result to file"""
        if self.selected_result_index is None:
            return
            
        result = self.who_results[self.selected_result_index]
        
        # Generate filename
        safe_location = re.sub(r'[^\w\s-]', '', result['location']).strip()
        safe_location = re.sub(r'[-\s]+', '_', safe_location)
        timestamp_part = result['timestamp'].split()[1] + "_" + result['timestamp'].split()[2]
        filename = f"who_{safe_location}_{timestamp_part}.txt"
        
        file_path = filedialog.asksaveasfilename(
            title="Save /who Result",
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")],
            initialvalue=filename
        )
        
        if file_path:
            try:
                content = f"[{result['timestamp']}]\n{result['content']}"
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                self.update_status(f"💾 Result saved to {os.path.basename(file_path)}", '#28a745')
            except Exception as e:
                messagebox.showerror("Error", f"Failed to save file: {str(e)}")
                
    def clear_results(self):
        """Clear all captured results"""
        if not self.who_results:
            return
            
        if messagebox.askyesno("Confirm", "Are you sure you want to clear all captured results?"):
            self.who_results.clear()
            self.results_listbox.delete(0, tk.END)
            self.selected_result_index = None
            
            self.result_text.delete(1.0, tk.END)
            self.result_text.insert(1.0, "No results captured yet")
            
            self.copy_btn.config(state='disabled')
            self.save_btn.config(state='disabled')
            self.update_count_label()
            
            self.update_status("🗑 All results cleared", '#dc3545')
            
    def update_status(self, message, color='#007bff'):
        """Update status label"""
        self.status_label.config(text=f"Status: {message}", fg=color)
        
    def update_count_label(self):
        """Update results count label"""
        self.count_label.config(text=f"Results: {len(self.who_results)}")
        
    def format_file_size(self, size_bytes):
        """Format file size in human readable format"""
        if size_bytes == 0:
            return "0 B"
        size_names = ["B", "KB", "MB", "GB"]
        i = 0
        while size_bytes >= 1024 and i < len(size_names) - 1:
            size_bytes /= 1024.0
            i += 1
        return f"{size_bytes:.1f} {size_names[i]}"
        
    def load_settings(self):
        """Load application settings"""
        try:
            if os.path.exists(self.settings_file):
                with open(self.settings_file, 'r') as f:
                    settings = json.load(f)
                    self.log_file_path = settings.get('last_log_file')
        except:
            pass  # Ignore errors loading settings
            
    def save_settings(self):
        """Save application settings"""
        try:
            settings = {
                'last_log_file': self.log_file_path
            }
            with open(self.settings_file, 'w') as f:
                json.dump(settings, f)
        except:
            pass  # Ignore errors saving settings
            
    def on_closing(self):
        """Handle application closing"""
        self.stop_monitoring_cmd()
        self.save_settings()
        self.root.destroy()
        
    def run(self):
        """Start the application"""
        self.root.mainloop()

if __name__ == "__main__":
    import sys
    if sys.version_info < (3, 6):
        print("Error: This application requires Python 3.6 or newer")
        sys.exit(1)
        
    try:
        app = EQWhoTracker()
        app.run()
    except KeyboardInterrupt:
        print("\nApplication interrupted by user")
    except Exception as e:
        print(f"Error starting application: {e}")
        sys.exit(1)
```

### Step 3: Create the Executable
```bash
# Navigate to the folder containing eq_who_tracker.py
cd /path/to/your/script

# Create a standalone executable (includes everything users need)
pyinstaller --onefile --windowed --name "EQ_Who_Tracker" eq_who_tracker.py

# Optional: Add an icon (if you have one)
# pyinstaller --onefile --windowed --icon=eq_icon.ico --name "EQ_Who_Tracker" eq_who_tracker.py
```

### Step 4: Find Your Executable
After PyInstaller finishes, you'll find:
- `dist/EQ_Who_Tracker.exe` - This is your standalone executable!

## For Users (Super Simple!)

### What Users Get:
1. A single `.exe` file (around 50-100MB)
2. No Python installation needed
3. No command line knowledge required
4. Just double-click and it works!

### User Instructions:
1. **Download** the `EQ_Who_Tracker.exe` file
2. **Double-click** to run (Windows may ask "Do you want to run this file?" - click Yes)
3. **Select your EQ log file** (usually in `EverQuest/Logs/` folder)
4. **Click "Start Monitoring"**
5. **Done!** Use `/who` in-game and results are captured automatically

## Sharing Options

### Option A: Direct File Sharing
- Upload the `.exe` to Google Drive, Dropbox, or file hosting
- Share the download link with your guild/friends
- Users download and double-click to run

### Option B: Guild Website
- Host the `.exe` on your guild website
- Add a download page with simple instructions

### Option C: Discord/Forums
- Upload to Discord (if under 8MB) or use file hosting
- Post download link with instructions

## Benefits of This Approach

✅ **Zero Setup** - Users just double-click  
✅ **No Python Required** - Everything is bundled  
✅ **No Command Line** - Pure GUI application  
✅ **Works Offline** - No internet needed after download  
✅ **Professional** - Looks and feels like a real application  
✅ **Raid-Friendly** - Set it once and forget it  

## Potential Issues & Solutions

### Windows Security Warning
- Windows Defender might flag the .exe as suspicious (common with PyInstaller)
- **Solution**: Users can click "More info" → "Run anyway"
- **Better**: Get the .exe code-signed (costs money but removes warnings)

### Large File Size
- The .exe will be 50-100MB (includes Python runtime)
- **Solution**: Use file hosting or compress with 7-Zip

### Auto-Updates
- Users need to download new versions manually
- **Solution**: Include version info in filename (e.g., `EQ_Who_Tracker_v1.0.exe`)

This approach gives you a truly user-friendly solution that works exactly like any other Windows application!