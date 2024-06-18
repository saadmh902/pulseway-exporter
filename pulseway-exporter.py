import http.server
import time
import requests
import json
import slumber
from urllib.parse import urlencode

ENDPOINT = "" #api end point htto://api.pulseway.com/ etc or use your own domain
API_KEY = '' #api key
API_SECRET = '' #api secret
GroupName = "" #The PulseWay groupname for the devices you want to monitor



def curl_request_with_auth(url, username, password, params):

    # Construct the authentication tuple
    auth = (username, password)
    
    # Make the request using requests library
    response = requests.get(url, auth=auth,params=params)
    
    # Check if the request was successful
    if response.status_code == 200:
        #print("Request successful!")
        #print("Response:")
        #print(response.text)
        return response.text
    else:
        return 0
        print("Request failed with status code:", response.status_code)

class MyHandler(http.server.BaseHTTPRequestHandler):
    def _set_headers(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/plain; charset=utf-8')
        self.end_headers()

    def _set_headers_404(self):
        self.send_response(404)
        self.send_header('Content-type', 'text/plain; charset=utf-8')
        self.end_headers()
    def do_GET(self):

        if "metrics" not in self.path and "/organizations" not in self.path:
            self._set_headers_404()
            return()

        self._set_headers()
 

        if "/metrics" in self.path:
            start_time = time.monotonic()
            displayedText = "# TYPE pulseway_device_status gauge\n"
            displayedText += "# TYPE pulseway_device_cpuusage gauge\n"
            displayedText += "# TYPE pulseway_device_memoryusage gauge\n"
            exportString = ""
            print("Starting to collect data...")

            data = {"$top":"100",
             "$skip":"0",
             "$filter":"contains(tolower(GroupName), '"+GroupName+"')"}
            encoded_data = urlencode(data)

            print("Collecting Device List...")
            r=curl_request_with_auth(ENDPOINT+"assets", API_KEY, API_SECRET,encoded_data)
            if(r != 0):
                print("Collected Device List Successfully")
            jsonObject = json.loads(r)
            print("Organizing Individual Device Data")
            for count,pulsewayDevice in enumerate(jsonObject["Data"]):
                r2=curl_request_with_auth(ENDPOINT+"devices/"+jsonObject["Data"][count]["Identifier"], API_KEY, API_SECRET,encoded_data)
                specificDevice = json.loads(r2)
                #print(specificDevice)

                if("Offline since" in specificDevice["Data"]["Uptime"]):
                    onlineStatus = "0"
                else:
                    onlineStatus = "1"
                exportString = ('pulseway_device_status{ID="'+str(specificDevice["Data"]['Identifier'])+'",name="'+specificDevice["Data"]['Name']+'",IsOnline="'+str(onlineStatus)+'",uptime="'+str(specificDevice["Data"]['Uptime'])+'",ipAddress="'+str(specificDevice["Data"]['ExternalIpAddress'])+'",CpuUsage="'+str(jsonObject["Data"][count]["CpuUsage"]) +'",MemoryUsage="'+str(jsonObject["Data"][count]["MemoryUsage"])+'"} ' + onlineStatus+"\n")
                displayedText+=exportString

                exportString = ('pulseway_device_cpuusage{ID="'+str(specificDevice["Data"]['Identifier'])+'",name="'+specificDevice["Data"]['Name']+'",IsOnline="'+str(onlineStatus)+'",uptime="'+str(specificDevice["Data"]['Uptime'])+'",ipAddress="'+str(specificDevice["Data"]['ExternalIpAddress'])+'",CpuUsage="'+str(jsonObject["Data"][count]["CpuUsage"]) +'",MemoryUsage="'+str(jsonObject["Data"][count]["MemoryUsage"])+'"} ' + str(jsonObject["Data"][count]["CpuUsage"]) +"\n")
                displayedText+=exportString

                exportString = ('pulseway_device_memoryusage{ID="'+str(specificDevice["Data"]['Identifier'])+'",name="'+specificDevice["Data"]['Name']+'",IsOnline="'+str(onlineStatus)+'",uptime="'+str(specificDevice["Data"]['Uptime'])+'",ipAddress="'+str(specificDevice["Data"]['ExternalIpAddress'])+'",CpuUsage="'+str(jsonObject["Data"][count]["CpuUsage"]) +'",MemoryUsage="'+str(jsonObject["Data"][count]["MemoryUsage"])+'"} ' + str(jsonObject["Data"][count]["MemoryUsage"]) +"\n")
                displayedText+=exportString

            displayedText += "# TYPE request_processing_seconds summary\n" 
            displayedText = displayedText + 'request_processing_seconds ' + str(time.monotonic() - start_time) + '\n'
            #print(displayedText)
            print(("Collected {} values").format(len(jsonObject["Data"])))
            
            self.wfile.write(displayedText.encode('utf-8'))
            self.wfile.write("\n".encode('utf-8'))
            return


HTTP_BIND_IP = "localhost"
HTTP_PORT_NUMBER = 3307

server_class = MyHandler
httpd = http.server.ThreadingHTTPServer((HTTP_BIND_IP, HTTP_PORT_NUMBER), server_class)
print(time.asctime(), "Server Starts - %s:%s" % ("*" if HTTP_BIND_IP == '' else HTTP_BIND_IP, HTTP_PORT_NUMBER))
httpd.serve_forever()
try:
    httpd.serve_forever()
except KeyboardInterrupt:
    pass
httpd.server_close()
print(time.asctime(), "Server Stops - %s:%s" % ("localhost", HTTP_PORT_NUMBER))
