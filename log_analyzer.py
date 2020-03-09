#!/usr/bin/env python
# -*- coding: utf-8 -*-
import sys
import os
import re
import gzip
import collections
import operator
import string

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

template_report = "./report.html"


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


def parsing_string(string_pars: str, template: list) -> list:
    """
    Function parsing string 'string' pattern list template
    :param string: any string
    :param template: template [template1, [template2],...[]],
    where [template1], [template2], ... is a regular expression
    :return: list of found strings
    """
    pars_list = []
    for temp in template:
        parsed_result = re.search(temp, string_pars);
        if parsed_result is not None:
            pars_list.append(parsed_result.group())
        else:
            pars_list.append('')
    return pars_list


def parsing_string_log(config: dict, log_file_name: str) -> list:
    """
    Function-generator read log string from file with filename 'log_file_name'
    :param config: dictionary with structure containing the directory log file 'LOG_DIR'
    :param log_file_name: name processed log file
    :return: structure list [url:str, request_time:str]
    """
    log_file_path = config["LOG_DIR"] + '/' + log_file_name
    if log_file_path.endswith(".gz"):
        log_file = gzip.open(log_file_path, 'rt')
    else:
        log_file = open(log_file_path, 'rt', encoding='utf-8')
    for log_string in log_file:
        parsed_list = parsing_string(log_string, [MASK_URL, MASK_REQUEST_TIME])
        yield parsed_list
    log_file.close()


def parsing_log(config: dict, log_file_name: str) -> list:
    """
    The function collects all parsed URLs into a list
    :param config: dictionary with structure containing the directory log file 'LOG_DIR'
    :param log_file_name: name processed log file
    :return: structure list [[url:str, request_time:str],[url:str, request_time:str],...]
    """
    lines_log = parsing_string_log(config, log_file_name)
    parced_lines = []
    for line in lines_log:
        parced_lines.append(line)
    return parced_lines


def sort_list_url(mass_url: list) -> dict:
    mas_sort_url = collections.defaultdict(list)
    for url, value_time in mass_url:
        mas_sort_url[url].append(value_time)
    return mas_sort_url


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
        sum_item = 0#none
    return sum_item


def time_average(list_item: list) -> float:
    return time_sum_url(list_item) / len(list_item)


def time_max(list_item: list) -> float:
    max_value_item = 0
    for item_time in list_item:
        if float(item_time) > max_value_item:
            max_value_item = float(item_time)
    return max_value_item


def value_percent(value_item: float, value_all: float) -> float:
    """
    Calculates the percentages for a given URL relative to all queries
    :param value_item: value for a given URL
    :param value_all: value for to all URL
    :return: value calculated as a percentage
    """
    return value_item / value_all * 100


def count_total_request(data_mas: dict) -> int:
    count_request = 0
    for index in data_mas.keys():
        count_request += len(data_mas[index])
    return count_request


def time_total_request(data_mas: dict) -> float:
    count_request_time = 0
    for index in data_mas.keys():
        for time_str in data_mas[index]:
            count_request_time += float(time_str)
    return count_request_time


def median_time_request(list_item: list) -> float:
    list_item_float = []
    for item in list_item:
        list_item_float.append(float(item))
    list_item_float.sort()
    return list_item_float[len(list_item_float) // 2]


def write_url_dict(url_str: str, line_time: list, total_count: int, total_time: float) -> dict:
    count_r = len(line_time)
    time_sum = time_sum_url(line_time)
    url_dict_stat = {"count": count_r,
                     "time_avg": time_average(line_time),
                     "time_max": time_max(line_time),
                     "time_sum": time_sum,
                     "url": url_str,
                     "time_med": median_time_request(line_time),
                     "time_perc": value_percent(time_sum, total_time),
                     "count_perc": value_percent(count_r, total_count)}
    return url_dict_stat


def create_result_mas(data_mas: dict) -> list:
    total_count = count_total_request(data_mas)
    total_time = time_total_request(data_mas)
    result_mas = []
    for item_mas in data_mas.keys():
        result_mas.append(write_url_dict(item_mas, data_mas[item_mas], total_count, total_time))
    result_mas_sort = sorted(result_mas, key = operator.itemgetter("time_sum"), reverse = True)
    return result_mas_sort


def create_report(config: dict, log_file_name: str , result_mas_sort: list):
    try:
        file_template_report = open(template_report, 'r')
        template_text = file_template_report.read()
    except:
        pass
    finally:
        file_template_report.close()
    if config["REPORT_SIZE"] < len(result_mas_sort):
        size_rep = config["REPORT_SIZE"]
    else:
        size_rep = len(result_mas_sort)


    report_text = string.Template(template_text)
    report_text_file = report_text.safe_substitute(table_json = result_mas_sort[0:size_rep])
    mask_date = re.findall(r'\d+', log_file_name)
    name_rep_file = config['REPORT_DIR']+'/report-' + mask_date[0][:4] + '.' + mask_date[0][4:6] + '.' + mask_date[0][6:] + '.html'
    try:
        file_report = open(name_rep_file,'w', encoding='utf-8')
        file_report.write(report_text_file)
    except:
        pass
    finally:
        file_report.close()


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
    log_name = search_last_log(config)
    if report_processing_check(config, log_name) == False:
        mass_passed_data = parsing_log(config, log_name)
        mass_passed_data_sort = sort_list_url(mass_passed_data)
        create_report(config, log_name, create_result_mas(mass_passed_data_sort))

if __name__ == "__main__":
    main()
