import sys
from pathlib import Path

# Add project root to sys.path
root_dir = Path(__file__).resolve().parent
sys.path.insert(0, str(root_dir))

# Run Streamlit main app
from src.dashboard.app import main

if __name__ == "__main__":
    main()
