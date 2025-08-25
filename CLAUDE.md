# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is an EverQuest `/who` Tracker - a Python-based desktop application that monitors EverQuest log files in real-time to capture `/who` command results during raids and gameplay. The application is designed for distribution as both a standalone executable and Python script.

## Development Commands

### Running the Application
```bash
python3 eq_who_tracker.py
```

### Testing OpenDKP Conversion
```bash
python3 test_opendkp_conversion.py
```

### Building Executable (PyInstaller)
```bash
# Install PyInstaller
pip install pyinstaller

# Build standalone executable
pyinstaller --onefile --windowed --name "EQ_Who_Tracker" eq_who_tracker.py

# Output will be in dist/EQ_Who_Tracker.exe
```

### Testing the Executable
```bash
# On Windows/WSL
./EQ_Who_Tracker.exe
```

## Architecture Overview

### Core Application (`eq_who_tracker.py`)
- **Main Class**: `EQWhoTracker` - Tkinter-based GUI application
- **File Monitoring**: Real-time log file monitoring using threading and file size tracking
- **Data Parsing**: Regex-based parsing of EverQuest `/who` command output
- **User Interface**: Split-panel design with results list and detail view
- **Settings Persistence**: JSON-based settings storage (`eq_tracker_settings.json`)

### Key Features
1. **Real-time Monitoring**: Monitors log files for new content only (avoids duplicate captures)
2. **Historical Data Loading**: Can load `/who` results from past time periods (5 min, 15 min, 1 hour, 1 day)
3. **OpenDKP Integration**: Converts `/who` results to OpenDKP tab-separated format for DKP management
4. **Result Management**: Copy, save, and clear functionality for captured results
5. **UI Prevention**: Read-only text areas with copy functionality

### Data Flow
1. User selects EverQuest log file
2. Application monitors file size changes
3. New content is read and parsed for `/who` results
4. Results are displayed in chronological order (newest first)
5. Users can select, view, copy, and save individual results

### File Structure
- `eq_who_tracker.py` - Main application code
- `EQ_Who_Tracker.exe` - Compiled executable (via PyInstaller)
- `EQ_Who_Tracker.spec` - PyInstaller build specification
- `eq_tracker_settings.json` - User settings (last used log file)
- `test_opendkp_conversion.py` - Testing utility for OpenDKP conversion
- `test_eq_log.txt` - Sample log data for testing
- `README` - Build and distribution instructions
- `index.html` - Web-based download page with instructions
- `customHttp.yml` - Web server configuration for executable downloads

### Key Technical Details

#### Log File Monitoring
- Uses file size tracking to detect new content
- Reads only new bytes added since last check
- Handles EverQuest's file locking gracefully
- Runs monitoring in separate daemon thread

#### `/who` Result Parsing
- Looks for "Players on EverQuest:" as start marker
- Captures all lines until "There are X players in LOCATION" end marker
- Extracts player names, levels, classes, and locations
- Handles both regular players and ANONYMOUS entries

#### OpenDKP Conversion
- Converts EverQuest class titles to standardized class names
- Outputs in tab-separated format: `0\tPlayerName\tLevel\tClass`
- Includes comprehensive class mapping for various EQ class titles and abbreviations

#### UI Design Patterns
- Split-panel layout (list view + detail view)
- Real-time status updates via tkinter's `after()` method
- Thread-safe UI updates from background monitoring thread
- Styled buttons with color coding (Success, Danger, Primary, Action)

## Distribution Strategy

The project supports two distribution methods:

1. **Executable Distribution**: PyInstaller-created standalone .exe for end users
2. **Script Distribution**: Raw Python file for technical users
3. **Web Interface**: HTML page with download buttons and instructions

## Common Development Patterns

- **Error Handling**: Graceful error handling with user-friendly messages
- **Threading**: Background file monitoring with proper cleanup
- **State Management**: Application state tracking for monitoring status
- **Data Validation**: Input validation for file paths and data parsing
- **Cross-Platform**: Designed to work on Windows (primary target) and Linux

## Dependencies

- Python 3.6+
- tkinter (included with Python)
- Standard library modules: os, time, threading, datetime, re, json

No external pip packages required for basic functionality (PyInstaller only needed for building executables).