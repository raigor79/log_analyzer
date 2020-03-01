#!/usr/bin/env python
# -*- coding: utf-8 -*-
import sys, os


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


def save_conf(filename):
    file = open(filename, 'w')
    for key, value in config.items():
        file.write('{} = {}\n'.format(key, value))
    file.close()

def loading_config_values(filename):
    """function loads the config file
    and merges with the default config
    """
    config_from_file = {}
    with open(filename) as inp:
        for i in inp.readlines():
            key1, val1 = i.strip().split(' = ')
            config_from_file[key1] = val1
    print(config_from_file)


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
                    if config_from_file.get(key) != None:
                        if type(config_from_file[key]) == type(config[key]):
                            config[key] = config_from_file[key]
        else:
            sys.exit(error_message_comnd_line % sys.argv[0])

    print('OK')




if __name__ == "__main__":
    main()
