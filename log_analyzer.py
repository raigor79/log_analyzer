#!/usr/bin/env python
# -*- coding: utf-8 -*-
import sys
import os
import re
import gzip


# url regular expression pattern
MASK_URL = r'(?<=GET\s)(/\S+)'
# request time regular expression pattern
MASK_REQUEST_TIME = r'(?<=\ )\d+\.\d+?$'

error_message_comnd_line = '''Unknown option.
Usage: python %s [--config] [file]
'''

'''log_format ui_short '$remote_addr  $remote_user $http_x_real_ip [$time_local] "$request" '
                       '$status $body_bytes_sent "$http_referer" '
                       '"$http_user_agent" "$http_x_forwarded_for" "$http_X_REQUEST_ID" "$http_X_RB_USER" '
                       '$request_time';
'''

'''REPORT_SIZE - the number of parsing url in the report table
   REPORT_DIR - report save directory
   LOG_DIR - directory storing logfiles 
'''
config = {
    "REPORT_SIZE": 1000,
    "REPORT_DIR": "./reports",
    "LOG_DIR": "./log"
}


def search_last_log(config: dict) -> str:
    """
    search function for the last log file in the directory 'LOG_DIR'
    :param config -  dictionary  with the directory log file:
    :return:  last_log  - filename last log file
    """
    res = []
    mask_log = r'nginx-access-ui.log-\d+((\.gz\b)|(\.log\b))'
    try:
        files = os.listdir(config["LOG_DIR"])
    except Exception as error_message:
        print(error_message)
    finally:
        if files != []:
            for index in range(0, len(files)):
                if re.fullmatch(mask_log, files[index]):
                    res.append(files[index])
            last_log = res[0]
            last = int(re.search(r'\d+', last_log).group(0))
            for index in range(1, len(res)):
                tres = int(re.search(r'\d+', res[index]).group(0))
                if last < tres:
                    last_log = res[index]
                    last = tres
        else:
            last_log = None
    return last_log


def report_processing_check(config: dict, last_log: str) -> bool:
    """
    Function processing check reporting the latest log
    :param config: dictionary  with the directory report file 'REPORT_DIR'
    :param last_log: name last log file
    :return: True if the file exists in the directory or
    False if the file is not in the directory
    """
    mask_rep = r'report-\d\d\d\d\.\d\d\.\d\d((\.html\b))'
    try:
        files = os.listdir(config["REPORT_DIR"])
    except Exception as error_message:
        print(error_message)
    finally:
        res = []
        mask_date = re.findall(r'\d+', last_log)
        mask_rep_last = r'' + mask_date[0][:4] + '.' + mask_date[0][4:6] + '.' + mask_date[0][6:]
        for index in range(0, len(files)):
            if re.fullmatch(mask_rep, files[index]):
                res.append(files[index])
        flag_processing_check = False
        for index in res:
            if re.search(mask_rep_last, index):
                flag_processing_check += True
            else:
                flag_processing_check += False
    return bool(flag_processing_check)


def parsing_string(string: str, template: list) -> list:
    """
    Function parsing string 'string' pattern list template
    :param string: any string
    :param template: template [template1, [template2],...[]],
    where [template1], [template2], ... is a regular expression
    :return: list of found strings
    """
    pars_list = []
    for temp in template:
        parsed_result = re.search(temp, string);
        if parsed_result is not None:
            pars_list.append(parsed_result.group())
        else:
            pars_list.append(None)
    return pars_list


def parsing_string_log(config: config, log_file_name: str) -> list:
    """
    Function-generator read log string from file with filename 'log_file_name'
    :param config: dictionary with structure containing the directory log file 'LOG_DIR'
    :param log_file_name: name processed log file
    :return: structure list [url:str, request_time:str]
    """
    log_file_path = config["LOG_DIR"] + '/' + log_file_name
    if log_file_path.endswith(".gz"):
        log_file = gzip.open(log_file_path, 'rb')
    else:
        log_file = open(log_file_path)
    for log_string in log_file:
        parsed_list = parsing_string(log_string, [MASK_URL, MASK_REQUEST_TIME])
        yield parsed_list
    log_file.close()


def count_list_item(list_item: list) -> int:
    return len(list_item)


def time_sum_url(list_item: list) -> float:
    """
    Amount calculation all item in list for this url, if not calculation gives 'None'
    :param list_item: list of strings of numeric values
    :return: Sum of all numerical values in list for this url
    """
    sum_item = 0
    try:
        for item in list_item:
            sum_item += float(item)
    except:
        sum_item = None
    return sum_item


def time_average(list_item: list) -> float:
    return time_sum_url(list_item)/len(list_item)


def value_percent(value_item: float, value_all: float) -> float:
    """
    Calculates the percentages for a given URL relative to all queries
    :param value_item: value for a given URL
    :param value_all: value for to all URL
    :return: value calculated as a percentage
    """
    return value_item/value_all*100


def main():
    if len(sys.argv) != 1:
        if len(sys.argv) == 3 and sys.argv[1] == '--config':
            config_from_file = {}
            try:
                id_file = open(sys.argv[2])
                try:
                    for string_read in id_file.readlines():
                        if string_read != '\n':
                            key, val = string_read.strip().split('=')
                            key, val = key.strip(), val.strip()
                            if val.isdigit():
                                val = int(val)
                        config_from_file[key] = val
                except Exception as error_work_config:
                    sys.exit(error_work_config)
                finally:
                    id_file.close()
            except Exception as error_open_config:
                sys.exit(error_open_config)
            finally:
                for key in config:
                    if config_from_file.get(key) is not None:
                        if type(config_from_file[key]) == type(config[key]):
                            config[key] = config_from_file[key]
        else:
            sys.exit(error_message_comnd_line % sys.argv[0])
    print('OK')
    print(search_last_log(config))
    parsing_string_log(config, search_last_log(config))


if __name__ == "__main__":
    main()
