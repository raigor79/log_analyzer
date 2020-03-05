#!/usr/bin/env python
# -*- coding: utf-8 -*-
import sys
import os
import re

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
    search function for the last log file in the directory
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
        else:
            last_log = None
    return last_log


def report_processing_check(config: dict, last_log: str) -> bool:
    mask_rep = r'report-\d\d\d\d\.\d\d\.\d\d((\.html\b))'
    try:
        files = os.listdir(config["REPORT_DIR"])
    except Exception as error_message:
        print(error_message)
    finally:
        res = []
        mask_date = re.findall(r'\d+',last_log)
        mask_rep_last = r''+mask_date[0][:4]+'.'+mask_date[0][4:6]+'.'+mask_date[0][6:]
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
    print(report_processing_check(config, search_last_log(config)))


if __name__ == "__main__":
    main()
