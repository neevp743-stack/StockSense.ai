import os
import sys

# Add project root to sys path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from backend.models.trainer import train_entire_universe

if __name__ == "__main__":
    print("Executing full universe model training...")
    results = train_entire_universe()
    print("Full universe model training completed successfully.")
