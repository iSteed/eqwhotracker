#!/usr/bin/env python3
"""
EverQuest /who Tracker - Desktop Application
A reliable file monitor for capturing /who results during raids.

Requirements: Python 3.6+ (tkinter included)
Usage: python eq_who_tracker.py
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import os
import time
import threading
from datetime import datetime, timedelta
import re
import json

class EQWhoTracker:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("EverQuest /who Tracker - Raid Edition")
        self.root.geometry("1200x900")  # Increased height to ensure instructions fit
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
        
    def prevent_edit(self, event):
        """Prevent editing but allow Ctrl+C for copying"""
        if event.state & 4 and event.keysym == 'c':  # Ctrl+C
            return  # Allow copy
        return "break"  # Block all other key presses
        
    def update_default_text(self):
        """Update the default text in result panel"""
        self.result_text.delete('1.0', tk.END)
        
        if self.who_results:
            # Show most recent result
            recent_result = self.who_results[-1]  # Last added (most recent)
            self.result_text.insert('1.0', f"Most Recent /who Result:\n")
            self.result_text.insert(tk.END, f"Location: {recent_result['location']}\n")
            self.result_text.insert(tk.END, f"Player Count: {recent_result['player_count']}\n")
            self.result_text.insert(tk.END, f"Timestamp: {recent_result['timestamp']}\n")
            self.result_text.insert(tk.END, "\n" + "="*50 + "\n\n")
            self.result_text.insert(tk.END, recent_result['content'])
        else:
            self.result_text.insert('1.0', "Select a result from the list to view details")

    def allow_selection(self, event):
        """Allow mouse clicks for text selection"""
        return  # Don't block mouse events
        
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
        
        # Historical data controls
        history_label = tk.Label(control_inner, text="Load Historical:", 
                                font=('Arial', 10), bg='#f0f0f0', fg='#333')
        history_label.pack(side='left', padx=(20, 5))
        
        self.load_5min_btn = ttk.Button(control_inner, text="5 min", 
                                       command=lambda: self.load_historical_data(5), style='Primary.TButton')
        self.load_5min_btn.pack(side='left', padx=(0, 5))
        
        self.load_15min_btn = ttk.Button(control_inner, text="15 min", 
                                        command=lambda: self.load_historical_data(15), style='Primary.TButton')
        self.load_15min_btn.pack(side='left', padx=(0, 5))
        
        self.load_1hour_btn = ttk.Button(control_inner, text="1 hour", 
                                        command=lambda: self.load_historical_data(60), style='Primary.TButton')
        self.load_1hour_btn.pack(side='left', padx=(0, 5))
        
        self.load_1day_btn = ttk.Button(control_inner, text="1 day", 
                                       command=lambda: self.load_historical_data(1440), style='Primary.TButton')
        self.load_1day_btn.pack(side='left', padx=(0, 5))
        
        # Status display
        self.status_label = tk.Label(control_inner, text="Status: Ready to select log file", 
                                    font=('Arial', 10, 'bold'), bg='#f0f0f0', fg='#007bff')
        self.status_label.pack(side='left', padx=(20, 0))
        
        # Results count
        self.count_label = tk.Label(control_inner, text="Results: 0", 
                                   font=('Arial', 10, 'bold'), bg='#f0f0f0', fg='#28a745')
        self.count_label.pack(side='right')
        
        # Results section - fixed height to ensure instructions are visible
        results_frame = tk.LabelFrame(main_frame, text="📊 Captured /who Results", 
                                     font=('Arial', 12, 'bold'), bg='#f0f0f0', fg='#2c3e50')
        results_frame.pack(fill='both', expand=True, pady=(0, 5))
        
        # Create paned window for split layout - limit height
        paned = ttk.PanedWindow(results_frame, orient='horizontal')
        paned.pack(fill='both', expand=True, padx=15, pady=10)
        
        # Left panel - Results list (fixed width to prevent layout issues)
        left_frame = tk.Frame(paned, bg='white', relief='sunken', bd=1, width=350)
        paned.add(left_frame, weight=1)
        
        list_label = tk.Label(left_frame, text="Results List", font=('Arial', 10, 'bold'), 
                             bg='#f8f9fa', fg='#495057')
        list_label.pack(fill='x', padx=2, pady=2)
        
        # Listbox with scrollbar
        list_scroll_frame = tk.Frame(left_frame, bg='white')
        list_scroll_frame.pack(fill='both', expand=True, padx=2, pady=2)
        
        self.results_listbox = tk.Listbox(list_scroll_frame, font=('Arial', 9), 
                                         selectmode='single', bg='white', height=15)
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
        
        self.opendkp_btn = ttk.Button(button_frame, text="📋 Copy for OpenDKP", 
                                     command=self.copy_opendkp_format, state='disabled', style='Primary.TButton')
        self.opendkp_btn.pack(side='left', padx=(0, 5))
        
        self.save_btn = ttk.Button(button_frame, text="💾 Save As...", 
                                  command=self.save_selected_result, state='disabled')
        self.save_btn.pack(side='left')
        
        # Result content display - using Text widget for better control
        text_frame = tk.Frame(right_frame)
        text_frame.pack(fill='both', expand=True, padx=2, pady=2)
        
        self.result_text = tk.Text(text_frame, wrap='word', font=('Courier New', 9), 
                                  bg='#f8f9fa', height=15, state='normal')
        text_scrollbar = tk.Scrollbar(text_frame, orient='vertical', command=self.result_text.yview)
        self.result_text.configure(yscrollcommand=text_scrollbar.set)
        
        # Bind events to prevent editing but allow selection
        self.result_text.bind('<KeyPress>', self.prevent_edit)
        self.result_text.bind('<Button-1>', self.allow_selection)
        
        self.result_text.pack(side='left', fill='both', expand=True)
        text_scrollbar.pack(side='right', fill='y')
        
        # Set initial content - show most recent result if available
        self.update_default_text()
        
        # Instructions - ensure they're always visible at bottom
        instr_frame = tk.Frame(main_frame, bg='#e3f2fd', relief='raised', bd=1)
        instr_frame.pack(fill='x', pady=(5, 0))
        
        instructions = ("💡 Instructions: Select your EverQuest log file, click 'Start Monitoring', then use /who commands in-game. "
                       "Results will be captured automatically and appear in the list on the left. "
                       "Select any result to view details and copy/save.")
        
        instr_label = tk.Label(instr_frame, text=instructions, font=('Arial', 9), 
                              bg='#e3f2fd', fg='#1565c0', wraplength=1150, justify='left',
                              padx=10, pady=8)
        instr_label.pack()
        
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
        
        # Update default text to show most recent result
        if not self.selected_result_index:  # Only if no specific result is selected
            self.update_default_text()
        
        # Show brief notification in status
        self.update_status(f"✅ New /who captured: {player_count} players in {location}", '#28a745')
        
    def on_result_select(self, event):
        """Handle result selection from listbox"""
        selection = self.results_listbox.curselection()
        if not selection:
            self.selected_result_index = None
            self.result_text.delete('1.0', tk.END)
            self.result_text.insert('1.0', "Select a result from the list to view details")
            self.copy_btn.config(state='disabled')
            self.opendkp_btn.config(state='disabled')
            self.save_btn.config(state='disabled')
            return
            
        # Get selected result (remember list is reversed)
        list_index = selection[0]
        result_index = len(self.who_results) - 1 - list_index
        
        if 0 <= result_index < len(self.who_results):
            self.selected_result_index = result_index
            result = self.who_results[result_index]
            
            # Display result content
            self.result_text.delete('1.0', tk.END)
            self.result_text.insert('1.0', f"Timestamp: {result['timestamp']}\n")
            self.result_text.insert(tk.END, f"Location: {result['location']}\n")
            self.result_text.insert(tk.END, f"Player Count: {result['player_count']}\n")
            self.result_text.insert(tk.END, "\n" + "="*50 + "\n\n")
            self.result_text.insert(tk.END, result['content'])
            
            self.copy_btn.config(state='normal')
            self.opendkp_btn.config(state='normal')
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
    
    def copy_opendkp_format(self):
        """Convert selected result to OpenDKP format and copy to clipboard"""
        if self.selected_result_index is None:
            return
            
        result = self.who_results[self.selected_result_index]
        opendkp_content = self.convert_to_opendkp_format(result['content'])
        
        if not opendkp_content.strip():
            messagebox.showwarning("No Data", "No valid player data found to convert to OpenDKP format.")
            return
        
        self.root.clipboard_clear()
        self.root.clipboard_append(opendkp_content)
        self.root.update()  # Ensure clipboard is updated
        
        # Count converted players
        player_count = len([line for line in opendkp_content.strip().split('\n') if line.strip()])
        self.update_status(f"📋 {player_count} players copied in OpenDKP format!", '#28a745')
    
    def convert_to_opendkp_format(self, who_content):
        """Convert /who result content to OpenDKP tab-separated format"""
        lines = who_content.split('\n')
        opendkp_lines = []
        
        # Class name mapping for consistency (including EQ class titles)
        class_mappings = {
            # Standard classes
            'warrior': 'Warrior',
            'paladin': 'Paladin',
            'ranger': 'Ranger',
            'shadow knight': 'Shadow Knight',
            'monk': 'Monk',
            'bard': 'Bard',
            'rogue': 'Rogue',
            'shaman': 'Shaman',
            'necromancer': 'Necromancer',
            'wizard': 'Wizard',
            'magician': 'Magician',
            'enchanter': 'Enchanter',
            'druid': 'Druid',
            'cleric': 'Cleric',
            'beastlord': 'Beastlord',
            'berserker': 'Berserker',
            
            # Enchanter titles
            'phantasmist': 'Enchanter',
            'illusionist': 'Enchanter',
            'beguiler': 'Enchanter',
            'arch convoker': 'Enchanter',
            'coercer': 'Enchanter',
            
            # Magician titles
            'conjurer': 'Magician',
            'elementalist': 'Magician',
            'arch mage': 'Magician',
            'wizard': 'Wizard',
            
            # Wizard titles
            'warlock': 'Wizard',
            'sorcerer': 'Wizard',
            'arcanist': 'Wizard',
            
            # Warrior titles
            'myrmidon': 'Warrior',
            'champion': 'Warrior',
            'overlord': 'Warrior',
            'warlord': 'Warrior',
            
            # Monk titles
            'master': 'Monk',
            'grandmaster': 'Monk',
            'transcendent': 'Monk',
            
            # Cleric/Paladin titles
            'templar': 'Paladin',
            'crusader': 'Paladin',
            'knight': 'Paladin',
            'cavalier': 'Paladin',
            
            # Shadow Knight titles
            'heretic': 'Shadow Knight',
            'reaver': 'Shadow Knight',
            'blackguard': 'Shadow Knight',
            
            # Common alternatives
            'sk': 'Shadow Knight',
            'shadowknight': 'Shadow Knight',
            'enc': 'Enchanter',
            'mag': 'Magician',
            'wiz': 'Wizard',
            'nec': 'Necromancer',
            'war': 'Warrior',
            'pal': 'Paladin',
            'ran': 'Ranger',
            'rog': 'Rogue',
            'mnk': 'Monk',
            'shm': 'Shaman',
            'dru': 'Druid',
            'cle': 'Cleric',
            'bst': 'Beastlord',
            'ber': 'Berserker',
            
            # Alternative names
            'minstrel': 'Bard',
            'troubadour': 'Bard',
            'unknown': 'Unknown',
        }
        
        for line in lines:
            line = line.strip()
            if not line or line.startswith('[') and (']' not in line[1:] or 'Players on EverQuest' in line):
                continue
                
            # Skip separator lines and summary lines
            if line.startswith('---') or line.startswith('There are'):
                continue
            
            # Parse player lines - look for [Level Class] Name or [ANONYMOUS] Class
            player_match = None
            
            # Remove timestamp prefix if present
            if line.startswith('[') and '] [' in line:
                parts = line.split('] ', 1)
                if len(parts) > 1:
                    line = parts[1]
            
            # Try to match [Level ClassTitle] PlayerName (Race) <Guild> pattern first
            player_match = re.match(r'^\[(\d+)\s+([A-Za-z ]+)\]\s+([A-Za-z0-9_]+)', line)
            if player_match:
                level = player_match.group(1)
                class_name = player_match.group(2).strip()
                player_name = player_match.group(3).strip()
            else:
                # Try to match [ANONYMOUS] PlayerName pattern
                anon_match = re.match(r'^\[ANONYMOUS\]\s+([A-Za-z0-9_]+)', line)
                if anon_match:
                    level = "0"  # Unknown level for anonymous
                    class_name = "Unknown"  # No class info for anonymous
                    player_name = anon_match.group(1).strip()
                else:
                    continue  # Skip lines we can't parse
            
            # Normalize class name
            class_name_lower = class_name.lower()
            normalized_class = class_mappings.get(class_name_lower, class_name)
            
            # Create OpenDKP format: 0\tPlayerName\tLevel\tClass
            opendkp_line = f"0\t{player_name}\t{level}\t{normalized_class}"
            opendkp_lines.append(opendkp_line)
        
        return '\n'.join(opendkp_lines)
        
    def save_selected_result(self):
        """Save selected result to file"""
        if self.selected_result_index is None:
            messagebox.showwarning("No Selection", "Please select a result from the list first!")
            return
            
        if not self.who_results or self.selected_result_index >= len(self.who_results):
            messagebox.showerror("Error", "Selected result is no longer valid. Please select another result.")
            return
            
        try:
            result = self.who_results[self.selected_result_index]
            
            # Generate filename with safe characters
            safe_location = re.sub(r'[^\w\s-]', '', result['location']).strip()
            safe_location = re.sub(r'[-\s]+', '_', safe_location)
            
            # Create timestamp part from the timestamp
            try:
                timestamp_parts = result['timestamp'].split()
                if len(timestamp_parts) >= 3:
                    date_part = timestamp_parts[1] + "_" + timestamp_parts[2]
                else:
                    date_part = datetime.now().strftime("%b_%d")
            except Exception:
                date_part = datetime.now().strftime("%b_%d")
            
            # Clean up the filename
            if not safe_location:
                safe_location = "unknown_location"
                
            filename = f"who_{safe_location}_{date_part}.txt"
            
            # Show save as dialog
            file_path = filedialog.asksaveasfilename(
                title="Save /who Result As...",
                defaultextension=".txt",
                filetypes=[("Text files", "*.txt"), ("All files", "*.*")],
                initialfile=filename  # Fixed: was initialvalue, should be initialfile
            )
            
            if file_path:  # User didn't cancel
                content = f"[{result['timestamp']}]\n{result['content']}"
                
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                
                saved_filename = os.path.basename(file_path)
                self.update_status(f"💾 Result saved as {saved_filename}", '#28a745')
                messagebox.showinfo("Save Successful", f"Result saved as:\n{saved_filename}")
                
        except Exception as e:
            error_msg = f"Failed to save file: {str(e)}"
            messagebox.showerror("Save Error", error_msg)
            self.update_status("❌ Save failed", '#dc3545')
                
    def clear_results(self):
        """Clear all captured results"""
        if not self.who_results:
            return
            
        if messagebox.askyesno("Confirm", "Are you sure you want to clear all captured results?"):
            self.who_results.clear()
            self.results_listbox.delete(0, tk.END)
            self.selected_result_index = None
            
            self.update_default_text()  # This will show the generic message since no results
            
            self.copy_btn.config(state='disabled')
            self.opendkp_btn.config(state='disabled')
            self.save_btn.config(state='disabled')
            self.update_count_label()
            
            self.update_status("🗑 All results cleared", '#dc3545')
    
    def load_historical_data(self, minutes_back):
        """Load historical /who results from the log file for the specified time period"""
        if not self.log_file_path or not os.path.exists(self.log_file_path):
            messagebox.showerror("Error", "Please select a valid log file first!")
            return
            
        try:
            # Calculate cutoff time
            cutoff_time = datetime.now() - timedelta(minutes=minutes_back)
            
            # Read entire log file and parse historical data
            self.update_status(f"🔍 Loading last {minutes_back} minutes of /who data...", '#007bff')
            
            historical_results = self.parse_historical_who_results(self.log_file_path, cutoff_time)
            
            if not historical_results:
                time_desc = self.format_time_description(minutes_back)
                messagebox.showinfo("No Results", f"No /who results found in the last {time_desc}")
                self.update_status("No historical results found", '#dc3545')
                return
            
            # Clear current results and load historical ones
            self.who_results.clear()
            self.results_listbox.delete(0, tk.END)
            self.selected_result_index = None
            
            # Add historical results (newest first)
            for result in reversed(historical_results):
                self.who_results.append(result)
                self.results_listbox.insert(tk.END, result['display_name'])
            
            # Update UI
            self.update_count_label()
            self.result_text.config(state='normal')
            self.result_text.delete(1.0, tk.END)
            self.result_text.insert(1.0, "Select a result from the list to view details")
            self.result_text.config(state='disabled')
            self.copy_btn.config(state='disabled')
            self.opendkp_btn.config(state='disabled')
            self.save_btn.config(state='disabled')
            
            time_desc = self.format_time_description(minutes_back)
            self.update_status(f"✅ Loaded {len(historical_results)} /who results from last {time_desc}", '#28a745')
            
        except Exception as e:
            error_msg = f"Error loading historical data: {str(e)}"
            messagebox.showerror("Error", error_msg)
            self.update_status("❌ Failed to load historical data", '#dc3545')
    
    def parse_historical_who_results(self, file_path, cutoff_time):
        """Parse the entire log file for /who results newer than cutoff_time"""
        results = []
        
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            lines = content.split('\n')
            current_who = []
            in_who_result = False
            who_timestamp = None
            who_datetime = None
            
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                
                # Look for start of /who result
                if 'Players on EverQuest:' in line:
                    in_who_result = True
                    current_who = [line]
                    
                    # Extract and parse timestamp
                    timestamp_match = re.match(r'^\[([^\]]+)\]', line)
                    if timestamp_match:
                        who_timestamp = timestamp_match.group(1)
                        who_datetime = self.parse_eq_timestamp(who_timestamp)
                    else:
                        who_timestamp = datetime.now().strftime("%a %b %d %H:%M:%S %Y")
                        who_datetime = datetime.now()
                    
                    continue
                
                if in_who_result:
                    current_who.append(line)
                    
                    # Look for end of /who result
                    if 'There are' in line and 'players in' in line:
                        # Complete /who result found
                        if who_datetime and who_datetime >= cutoff_time:
                            # This result is within our time range
                            who_content = '\n'.join(current_who)
                            
                            # Extract location and player count
                            location_match = re.search(r'There are \d+ players in (.+)\.', line)
                            location = location_match.group(1) if location_match else "Unknown"
                            
                            count_match = re.search(r'There are (\d+) players', line)
                            player_count = count_match.group(1) if count_match else "?"
                            
                            result = {
                                'timestamp': who_timestamp,
                                'content': who_content,
                                'location': location,
                                'player_count': player_count,
                                'display_name': f"[{who_timestamp}] {player_count} players in {location}",
                                'datetime': who_datetime
                            }
                            results.append(result)
                        
                        in_who_result = False
                        current_who = []
                        who_timestamp = None
                        who_datetime = None
        
        except Exception as e:
            raise Exception(f"Failed to parse log file: {str(e)}")
        
        # Sort by datetime (oldest first, will be reversed when adding to list)
        results.sort(key=lambda x: x['datetime'])
        return results
    
    def parse_eq_timestamp(self, timestamp_str):
        """Parse EverQuest timestamp string to datetime object"""
        try:
            # EQ timestamp format: "Wed Oct 16 14:23:45 2024"
            return datetime.strptime(timestamp_str, "%a %b %d %H:%M:%S %Y")
        except ValueError:
            try:
                # Try alternative format without year
                current_year = datetime.now().year
                dt = datetime.strptime(f"{timestamp_str} {current_year}", "%a %b %d %H:%M:%S %Y")
                return dt
            except ValueError:
                # If parsing fails, assume it's recent
                return datetime.now()
    
    def format_time_description(self, minutes):
        """Format minutes into a human-readable description"""
        if minutes < 60:
            return f"{minutes} minute{'s' if minutes != 1 else ''}"
        elif minutes < 1440:  # less than a day
            hours = minutes // 60
            return f"{hours} hour{'s' if hours != 1 else ''}"
        else:
            days = minutes // 1440
            return f"{days} day{'s' if days != 1 else ''}"
            
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