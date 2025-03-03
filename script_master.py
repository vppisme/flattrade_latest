import json
import csv
csv_file = "./NSE_Equity.csv"
json_file = "./NSE_Equity.json"

def csv_to_json(csvfile, jsonfile):
    data = {}
    with open(csvfile) as cf:
        cf_data = csv.DictReader(cf)
        for rows in cf_data:
            tmp_data = {}
            key0 = rows['Symbol']
            key1 = rows['Tradingsymbol']
            tmp_data[key1] = rows['Token']
            data[key0] = tmp_data
    with open(jsonfile, 'w', encoding='utf-8') as jf:
        jf.write(json.dumps(data, indent=4))

csv_to_json(csv_file, json_file)