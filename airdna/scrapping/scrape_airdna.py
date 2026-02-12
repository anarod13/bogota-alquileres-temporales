import sys
import subprocess

def main():
    if len(sys.argv) < 3:
        print("Usage: python scrape_airdna.py <localidad> <limit>")
        sys.exit(1)
    
    localidad = sys.argv[1]
    limit = int(sys.argv[2])
    offset = 0
    
    script_path = "airdna/scrapping/get_listings_per_section.py"
    
    while offset < limit:
        print(f"\n{'='*60}")
        print(f"Starting iteration with offset: {offset}")
        print(f"Localidad: {localidad}, Limit: {limit}, Offset: {offset}")
        print(f"{'='*60}\n")
        
        try:
            result = subprocess.run(
                [sys.executable, script_path, localidad, str(limit), str(offset)],
                check=True,
                capture_output=False
            )
            print(f"\nIteration completed successfully for offset {offset}")
        except subprocess.CalledProcessError as e:
            print(f"\nError running script for offset {offset}: {e}")
            break
        except KeyboardInterrupt:
            print(f"\nInterrupted at offset {offset}")
            break
        
        offset += 400
        
        if offset >= limit:
            print(f"\nReached limit. Final offset: {offset}")
            break
    
    print(f"\nAll iterations completed. Final offset: {offset}")

if __name__ == "__main__":
    main()
