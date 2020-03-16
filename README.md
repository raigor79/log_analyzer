# Script Log Analyzer

**The script processes the log with the last date in the file name in the LOG_DIR folder at startup, parses fields with URLs 
and time requests, considers the necessary statistics for urls and renders the report report.html.**

log format:
```
'$remote_addr $remote_user $http_x_real_ip [$time_local] "$request" '
'$status $body_bytes_sent "$http_referer" '
'"$http_user_agent" "$http_x_forwarded_for" "$http_X_REQUEST_ID" "$http_X_RB_USER"''$request_time';
```
example log filename: 
```
nginx-access-ui.log-20170630.gz
```
example report:
```
report-2017.06.30.html
```
default: 
* logs in the folder 
```
./log
```
* renders the report in folder:
```
./reports
```
* size report
```
1000
```
## Getting Started

To run the script on your computer, install Python 3.
* for Windows download "https://www.python.org/downloads/release/python-382/" and install.
 
### Installing

Download files: log_analyzer.py, report.html, reports/jquery.tablesorter.min.js

### Running

* run with default parameters from the terminal
```
python3 log_analyzer.py
```
* run with parameters from the config file from the terminal
```
python3 log_analyzer.py --config filename
```

example file config in format json
```
{
 REPORT_SIZE : 8000
 REPORT_DIR : "./reports"
 LOG_DIR : "./log"
 LOG_ANALYZER_PATH : "./loganalyzer.log"
}
```
LOG_ANALYZER_PATH - the variable defines the script log file, the variable defines the file for saving the script operation logsб
by default, the log is written to stdout

example log:
```
[2020.03.10 17:50:50] I Last log has already been processed
```


