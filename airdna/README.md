## Guide to use script to scrap AirDNA data

### Get details per section (localidad)
1. Perform all required requests on listing section
2. Store all requests as .har file. Store at './sources/har/'
3. Run './get_details/parse_har.ipynb' it'll parse responses as .json and sort them out by localidad
4. Once every localidad is sorted as .json, run './get_details/iterate_localidades.ipynb'. It will update the file './cleaned/localidades.csv', which will be ready to use as .csv or .xlsx
5. This set of scripts is set to run agains base list of localidades found at './sources/localidades.csv'. In case it needs to be updated it can be donde by using './get_details/get_all.ipynb' (It'll require to update the source payload response at './sources/localidades.json')