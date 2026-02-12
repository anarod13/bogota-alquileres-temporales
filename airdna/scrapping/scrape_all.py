import sys
import subprocess
import pandas as pd
from pathlib import Path

def main():
    csv_path = Path("airdna/scrapping/submarkets.csv")
    
    if not csv_path.exists():
        print(f"Error: {csv_path} not found")
        sys.exit(1)
    
    df = pd.read_csv(csv_path)
    
    if len(df.columns) < 2:
        print("Error: CSV file must have at least 2 columns")
        sys.exit(1)
    
    id_col = df.columns[0]
    listing_count_col = df.columns[1]
    
    df[id_col] = df[id_col].astype(str)
    
    script_path = "airdna/scrapping/scrape_airdna.py"
    
    print(f"Found {len(df)} submarkets to process")
    print(f"Using columns: {id_col} (id), {listing_count_col} (limit)\n")
    
    for idx, row in df.iterrows():
        submarket = str(row[id_col])
        limit = int(row[listing_count_col])
        
        print(f"\n{'='*60}")
        print(f"Processing submarket {idx + 1}/{len(df)}")
        print(f"ID: {submarket}, Limit: {limit}")
        print(f"{'='*60}\n")
        
        try:
            result = subprocess.run(
                [sys.executable, script_path, submarket, str(limit)],
                check=True,
                capture_output=False
            )
            print(f"\nCompleted successfully for submarket {submarket}")
        except subprocess.CalledProcessError as e:
            print(f"\nError running script for submarket {submarket}: {e}")
            continue
        except KeyboardInterrupt:
            print(f"\nInterrupted at submarket {submarket}")
            break
        except Exception as e:
            print(f"\nUnexpected error for submarket {submarket}: {e}")
            continue
    
    print(f"\nAll submarkets processed.")

if __name__ == "__main__":
    main()
