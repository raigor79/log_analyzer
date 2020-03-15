#!/usr/bin/env python
# -*- coding: utf-8 -*-
import sys
import os
import re
import gzip
import collections
import operator
import string
import logging
import argparse
import json
import datetime

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
    "LOG_DIR": "./log",
    "LOG_ANALYZER_PATH": None
}

template_report = "./report.html"


def search_last_log(config: dict) -> str:
    """
    search function for the last log file in the directory 'LOG_DIR'
    :param config -  dictionary  with the directory log file:
    :return:  last_log  - filename last log file
    """
    res = []
    mask_log = r'nginx-access-ui.log-(\d+)((\.gz\b)|(\.log\b))'

    list_files = os.listdir(config["LOG_DIR"])
    if list_files:
        data_last_log = datetime.datetime.strptime('00010101','%Y%m%d').date()
        for file in list_files:
            group_str_namefile = re.match(mask_log, file)
            if group_str_namefile:
                try:
                    data_log = datetime.datetime.strptime(group_str_namefile.group(1), '%Y%m%d').date()
                except:
                    continue
                if data_last_log<data_log:
                    data_last_log = data_log
                    last_log = group_str_namefile.group(0)
            else:
                continue
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
        logging.exception('Module "report_processing_check": %s', error_message)
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
        parsed_result = re.search(temp, string_pars)
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
    global total
    global processed
    try:
        if log_file_path.endswith(".gz"):
            log_file = gzip.open(log_file_path, 'rt')
        else:
            log_file = open(log_file_path, 'rt', encoding='utf-8')
    except Exception as er:
        logging.exception('Error %s', er)
    total_str = 0
    processed_str = 0
    for log_string in log_file:
        total_str += 1
        parsed_list = parsing_string(log_string, [MASK_URL, MASK_REQUEST_TIME])
        if parsed_list[0] != '':
            processed_str += 1
        yield parsed_list
    log_file.close()
    processed = processed_str
    total = total_str


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
    """
    Function of sorting the request time by the same URL
    :param mass_url: list [ "url","time_request"]
    :return: dictionary with elements 'url': [time_request1,time_request2,..]
    """
    mas_sort_url = collections.defaultdict(list)
    for url, value_time in mass_url:
        mas_sort_url[url].append(value_time)
    return mas_sort_url


def count_list_item(list_item: list) -> int:
    """
    Calculate the number of items in the list for this URL
    :param list_item: list of strings of numeric values
    :return: number of items in the list
    """
    return len(list_item)


def time_sum_url(list_item: list) -> float:
    """
    Amount calculation all item in list for this url, if not calculation gives 'None'
    :param list_item: list of strings of numeric values
    :return: sum of all numerical values in list for this url
    """
    sum_item = 0
    try:
        for item in list_item:
            sum_item += float(item)
    except:
        logging.exception('Error conversions in type "float" modul time_sum_url')
        sum_item = 0  # none
    return sum_item


def time_average(list_item: list) -> float:
    """
    The function determines the average values request time in list for a given URL
    :param list_item: list with values request time
    :return: the average request time
    """
    return time_sum_url(list_item) / len(list_item)


def time_max(list_item: list) -> float:
    """
    The function determines the maximum request time in list for a given URL
    :param list_item: list with values request time
    :return: the maximum request time
    """
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
    """
    Function counts the total number of queries in the "data_mas"
    :param data_mas: dictionary {'url1': [time_request1, time_request2, ...], 'url2':...}
    :return: total number of queries
    """
    count_request = 0
    for index in data_mas.keys():
        count_request += len(data_mas[index])
    return count_request


def time_total_request(data_mas: dict) -> float:
    """
    The function counts the total request time in the "data_mas".
    :param data_mas: dictionary {'url': [time_request1, time_request2, ...]}
    :return: total time request
    """
    count_request_time = 0
    for index in data_mas.keys():
        for time_str in data_mas[index]:
            count_request_time += float(time_str)
    return count_request_time


def median_time_request(list_item: list) -> float:
    """
    Function to find the median value of a list
    :param list_item: given list (int, float) value [7,4,3,2,5,6,1]
    :return: median value of the list [4]
    """
    list_item_float = []
    for item in list_item:
        list_item_float.append(float(item))
    list_item_float.sort()
    return list_item_float[len(list_item_float) // 2]


def write_url_dict(url_str: str, line_time: list, total_count: int, total_time: float) -> dict:
    """
    The function forms a string of of static parameters parameters for a given URL in the form of a dictionary
    :param url_str: name URL
    :param line_time: list values time_request for a given URL
    :param total_count: total number of requests
    :param total_time:  total time of requests
    :return: dictionary of of statistical parameters for a given URL
    """
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
    """
    Create function sorted by "max_time" list of statistics data
    :param data_mas : source dictionary of url and time request
    :return: list dictionary of url and request statistics
    """
    total_count = count_total_request(data_mas)
    total_time = time_total_request(data_mas)
    result_mas = []
    for item_mas in data_mas.keys():
        result_mas.append(write_url_dict(item_mas, data_mas[item_mas], total_count, total_time))
    result_mas_sort = sorted(result_mas, key=operator.itemgetter("time_sum"), reverse=True)
    return result_mas_sort


def create_report(conf: dict, log_file_name: str, result_mas_sort: list):
    """
    The function of creating a report file in the form of a table
    :param conf: dictionary with structure containing 
                   the directory log file 'REPORT_DIR'
                   and report sample size 'REPORT_SIZE'
    :param log_file_name: name of the log file for which
                          the report is generated
    :param result_mas_sort: sorted list of statistics [{},{},..]
    :return: 
    """
    try:
        file_template_report = open(template_report, 'r')
        template_text = file_template_report.read()
    except Exception as er:
        logging.exception('Error load template report: %s', er)
    finally:
        file_template_report.close()
    if conf["REPORT_SIZE"] < len(result_mas_sort):
        size_rep = conf["REPORT_SIZE"]
    else:
        size_rep = len(result_mas_sort)
    report_text = string.Template(template_text)
    report_text_file = report_text.safe_substitute(table_json=result_mas_sort[0:size_rep])
    mask_date = re.findall(r'\d+', log_file_name)
    name_rep_file = conf['REPORT_DIR'] + '/report-' + mask_date[0][:4] + '.' \
                    + mask_date[0][4:6] + '.' + mask_date[0][6:] + '.html'
    try:
        file_report = open(name_rep_file, 'w', encoding='utf-8')
        file_report.write(report_text_file)
    except Exception as er:
        logging.exception('Error create report %s: %s', name_rep_file, er)
    finally:
        file_report.close()


def init_logging(conf: dict):
    """
    Logging module settings function
    :param conf: dictionary with structure containing
                    name log file 'LOG_ANALYZER_PATH',
                    default 'LOG_ANALYZER_PATH' = None
    :return:
    """
    format_log = '[%(asctime)s] %(levelname).1s %(message)s'
    logging.basicConfig(
        filename=conf["LOG_ANALYZER_PATH"],
        format=format_log,
        datefmt='%Y.%m.%d %H:%M:%S',
        level=logging.INFO)


def process_message(total_str: int, proccesed_str: int) -> str:
    err = 100 - 100 * proccesed_str / total_str
    if err < 60:
        return 'Process complete'
    else:
        return 'Unable to parse most of the log Error >60% perhaps the logging format has changed'


def parser_name_config() -> str:
    """
    Command line parsing procedure
    :return: filename config
    """
    parser = argparse.ArgumentParser(description='Log analizer')
    parser.add_argument('--config', type=str, help='Load config')
    args = parser.parse_args()
    return args.config


def main():
    init_logging(config)
    config_name = parser_name_config()
    if config_name:
        try:
            id_file_config = open(config_name)
            config_from_file = json.load(id_file_config, encoding="utf8")
        except Exception as error_work_config:
            sys.exit(error_work_config)
        finally:
            id_file_config.close()
        for key in config:
            if config_from_file.get(key) is not None:
                if type(config_from_file[key]) != type(config[key]):
                    pass
                else:
                    config[key] = config_from_file[key]
    if not os.path.isdir(config["LOG_DIR"]):
        logging.error("Scripts aborted - The directory 'LOG_DIR' is incorrect")
        sys.exit()
    print(config)
    error_flag = False
    # init_logging(config)
    log_name = search_last_log(config)
    if report_processing_check(config, log_name) == False:
        try:
            logging.info('Last raw log found: %s', log_name)
            mass_passed_data = parsing_log(config, log_name)
            mass_passed_data_sort = sort_list_url(mass_passed_data)
            create_report(config, log_name, create_result_mas(mass_passed_data_sort))
        except KeyboardInterrupt:
            message_error = 'Script the script was interrupted by clicking Ctrl+C'
            error_flag = True
        finally:
            if error_flag:
                logging.error(message_error)
            else:
                logging.info(process_message(total, processed))
    else:
        logging.info('Last log has already been processed')


if __name__ == "__main__":
    main()
