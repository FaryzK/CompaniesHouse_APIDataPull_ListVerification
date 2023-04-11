import requests
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry
import csv
import base64
import json

api_key = "d8c293e6-2245-40bd-b23f-d9fa3f000e16"
# Set up retries
retry_strategy = Retry(
    total=None,  # number of retries
    status_forcelist=[429],  # retry on 429 status code
    backoff_factor=1  # wait 1 second, then 2 seconds, then 4 seconds, etc.
)

#keep track of company
countCompany = 1

#for jobs that req continuation
startAtRow = 1
stopAtRow = 99

#with open('company_numbers.csv', 'r') as file, open('output.csv', 'w', newline='') as output_file:
#with open('company_numbers_test.csv', 'r') as file, open('output.csv', 'w', newline='') as output_file:
#with open('allIncorporatedClients_test.csv', 'r') as file, open('output_test.csv', 'w', newline='') as output_file:
with open('allIncorporatedClients.csv', 'r') as file, open('output.csv', 'w', newline='') as output_file:
    reader = csv.reader(file)
    writer = csv.writer(output_file)

    # write header row to output CSV
    writer.writerow(['Company Name', 'Company Number', 'Incorporation Date', 'Company Status', 'Last Filing Overdue', 'Last filing date', "Agent Name", "Agent Country", "Company Email", "Company Phone Number"])

    # loop over each row in the input CSV
    for row in reader:
        if startAtRow <= countCompany <= stopAtRow:
            companyNumber = row[1]
            agentName = row[3]
            agentCountry = row[9] if row[9] != "Other" else row[10]
            companyEmail = row[19]
            companyPhonenumber = row[18]
            print(countCompany)
            countCompany += 1

            #basicauth is req
            url = f"https://api.company-information.service.gov.uk/company/{companyNumber}"
            auth_string = f"{api_key}:".encode("ascii")
            auth_string_b64 = base64.b64encode(auth_string).decode("ascii")
            headers = {"Authorization": f"Basic {auth_string_b64}"}
            # Set up session with headers and retries
            session = requests.Session()
            session.headers.update(headers)
            session.mount('https://', HTTPAdapter(max_retries=retry_strategy))
            response = session.get(url, headers=headers)

            if response.status_code == 200:
                companyData = json.loads(response.content)
                formattedData = json.dumps(companyData, sort_keys=True, indent=4)
                print(formattedData)
                companyName = companyData["company_name"]
                print(companyName)
                companyNumber = companyData["company_number"]
                companyIncorporationDate = companyData["date_of_creation"]
                companyStatus = companyData["company_status"]
                #//check if status if active / inactive / dissolved / liquidation
                if companyStatus == "active":
                    #//check if overdue
                    isOverDue = companyData["accounts"]["overdue"]
                    if companyData["accounts"]["last_accounts"]["type"] == "null" and not isOverDue: #//within 21month of incorp
                        lastFilingDate = "-"
                    elif companyData["accounts"]["last_accounts"]["type"] == "null" and isOverDue: #//past 21month of incorp and overdue
                        lastFilingDate = "Passed first filing date AND not filed!"
                    else:
                        lastFilingDate = companyData["accounts"]["last_accounts"]["made_up_to"] #//not overdue and after 21month of incorp
                elif companyStatus == "dissolved" or companyStatus == "liquidation":
                    isOverDue = "-"
                    lastFilingDate = "-"
                writer.writerow([companyName, companyNumber, companyIncorporationDate, companyStatus, isOverDue, lastFilingDate, agentName, agentCountry, companyEmail, companyPhonenumber])
            else:
                print(f"Error: {response.status_code}")
        else:
            countCompany += 1
