# for integration testing
# posts a json file as a request body
# to the specified url
import requests
import json
import sys

# first argument is the url
# second argument is the file name

url = sys.argv[1]
file_name = sys.argv[2]

# load json file with test data
with open(file_name) as json_file:
    data = json.load(json_file)

# post the gotten json data to the server
r = requests.post(url, json=data)

# print the response text to console
print(r.text)
