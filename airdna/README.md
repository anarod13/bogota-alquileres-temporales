## Guide to use script to scrap AirDNA data

### Get details per section (submarket)
1. Perform all required requests on listing section
2. Store all requests as .har file. Store at './sources/har/'
3. Run './get_details/parse_har.ipynb' it'll parse responses as .json and sort them out by submarket
4. Once every submarket is sorted as .json, run './get_details/iterate_submarketes.ipynb'. It will update the file './cleaned/submarketes.csv', which will be ready to use as .csv or .xlsx
5. This set of scripts is set to run agains base list of submarketes found at './sources/submarketes.csv'. In case it needs to be updated it can be donde by using './get_details/get_all.ipynb' (It'll require to update the source payload response at './sources/submarketes.json')

### Get listings per section (submarket)
Script: `./scrapping/get_listings_per_section.py`

This script intercepts and modifies API requests to fetch listings data from AirDNA. It automatically logs in, navigates to the listings page, and saves responses as JSON files.

**Usage:**
```bash
python scrapping/get_listings_per_section.py [submarket] [limit] [initial_offset]
```

**Arguments:**
- `submarket` (int, optional): The submarket ID to scrape. Default: 142652
- `limit` (int, optional): Total number of items to fetch. Default: 100
- `initial_offset` (int, optional): Starting offset for pagination. Default: 0

**Examples:**
```bash
# Fetch 100 items starting from offset 0 for submarket 142652
python scrapping/get_listings_per_section.py 142652 100 0

# Fetch 500 items starting from offset 200 for submarket 142649
python scrapping/get_listings_per_section.py 142649 500 200

# Use defaults (submarket=142652, limit=100, offset=0)
python scrapping/get_listings_per_section.py
```

**How it works:**
1. Launches a Firefox browser and automatically logs into AirDNA
2. Navigates to the listings page for the specified submarket
3. Intercepts POST requests to the listings API endpoint
4. Modifies each request to fetch the next batch of items (100 per batch)
5. Saves each response as JSON files in `airdna/sources/listings/`
6. Files are named as: `{submarket}_{offset}.json`

**Notes:**
- The browser will remain open after the script finishes
- Requests are triggered naturally by the browser (scrolling, pagination, etc.)
- You may need to interact with the browser to trigger additional requests
- The script will stop when the limit is reached or after a timeout
