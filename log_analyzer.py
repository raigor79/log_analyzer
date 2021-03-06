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
import pathlib
import shutil

# url regular expression pattern
MASK_URL = r'(?<=GET\s)(/\S+)'
# request time regular expression pattern
MASK_REQUEST_TIME = r'(?<=\ )\d+\.\d+?$'

MASK_LOG = r'nginx-access-ui.log-(\d+)((\.gz\b)|(\.log\b))'

DEFAULT_CONFIG_PATH = os.path.dirname(__file__)

DEFAULT_CONFIG_FILE_NAME = "default.cfg"

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
   STATUS_LOGGING - status logging (ERROR, INFO, DEBUG)
   THRESHOLD_ERROR_PARS_PERCENT - error parsing in %
'''
default_config = {
    "REPORT_SIZE": 1000,
    "REPORT_DIR": "./reports",
    "LOG_DIR": "./log",
    "LOG_ANALYZER_PATH": None,
    "STATUS_LOGGING": "INFO",
    "THRESHOLD_ERROR_PARS_PERCENT": 60
}

template_report = "./report.html"


def search_last_log(config: dict) -> str:
    """
    search function for the last log file in the directory 'LOG_DIR'
    :param config -  dictionary  with the directory log file:
    :return:  last_log  - filename last log file
    """
    res = []
    list_files = os.listdir(os.path.join(config["LOG_DIR"]))
    if list_files:
        data_last_log = datetime.datetime.strptime('00010101', '%Y%m%d').date()
        for file in list_files:
            group_str_namefile = re.match(MASK_LOG, file)
            if group_str_namefile:
                try:
                    data_log = datetime.datetime.strptime(group_str_namefile.group(1), '%Y%m%d').date()
                except:
                    continue
                if data_last_log < data_log:
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
    group_str_namefile = re.match(MASK_LOG, last_log)
    date_string = group_str_namefile.group(1)
    date_typedate = datetime.datetime.strptime(date_string, "%Y%m%d").date()
    report_name = 'report-{0}.html'.format(datetime.datetime.strftime(date_typedate, "%Y.%m.%d"))
    if os.path.isdir(config["REPORT_DIR"]):
        files_list = os.listdir(config["REPORT_DIR"])
        if report_name in files_list:
            return True
        else:
            return False
    else:
        try:
            os.mkdir(config["REPORT_DIR"])
        except OSError:
            logging.exception("Create directory% s failed" % config["REPORT_DIR"])
        else:
            logging.info("Successfully created directory %s " % config["REPORT_DIR"])
        return False


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
            if temp != MASK_REQUEST_TIME:
                pars_list.append('')
            else:
                pars_list.append('0')
    return pars_list


def process_message(total_str: int, proccesed_str: int, permissible_error: int) -> str:
    """
    The function calculates the parsing error and, on the threshold, issues a message to the log
    :param total_str: total number of parsing operations
    :param proccesed_str: number of defined values
    :param permissible_error: threshold error
    :return: message string
    """
    err = 100 - 100 * proccesed_str / total_str
    if err < permissible_error:
        msg = 'Process to parse log complete'
    else:
        msg = 'Unable to parse most of the log Error > %d \% ' \
              'perhaps the logging format has changed' % permissible_error
    return msg


def parsing_string_log(config: dict, log_file_name: str) -> list:
    """
    Function-generator read log string from file with filename 'log_file_name'
    :param config: dictionary with structure containing the directory log file 'LOG_DIR'
    :param log_file_name: name processed log file
    :return: structure list [url:str, request_time:str]
    """
    log_file_path = os.path.join(config["LOG_DIR"], log_file_name)
    open_log = gzip.open if log_file_name.endswith(".gz") else open
    with open_log(log_file_path, 'rt', encoding='utf-8') as log_file:
        total_str = 0
        processed_str = 0
        for log_string in log_file:
            total_str += 1
            parsed_list = parsing_string(log_string, [MASK_URL, MASK_REQUEST_TIME])
            if parsed_list[0] != '':
                processed_str += 1
            yield parsed_list
    logging.info(process_message(total_str, processed_str, config["THRESHOLD_ERROR_PARS_PERCENT"]))


def parsing_log(config: dict, log_file_name: str) -> list:
    """
    The function collects all parsed URLs into a list
    :param config: dictionary with structure containing the directory log file 'LOG_DIR'
    :param log_file_name: name processed log file
    :return: structure list [[url:str, request_time:str],[url:str, request_time:str],...]
    """
    parced_lines = parsing_string_log(config, log_file_name)
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
        sum_item = 0
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
            if time_str != "":
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
    with open(template_report, 'r', encoding='utf-8') as file_template_report:
        try:
            template_text = file_template_report.read()
        except Exception as er:
            logging.exception('Error load template report: %s', er)
    if conf["REPORT_SIZE"] < len(result_mas_sort):
        size_rep = conf["REPORT_SIZE"]
    else:
        size_rep = len(result_mas_sort)
    report_text = string.Template(template_text)
    report_text_file = report_text.safe_substitute(table_json=result_mas_sort[0:size_rep])
    group_str_namefile = re.match(MASK_LOG, log_file_name)
    date_string = group_str_namefile.group(1)
    date_typedate = datetime.datetime.strptime(date_string, "%Y%m%d").date()
    report_name_tmp = 'report-{0}.tmp'.format(datetime.datetime.strftime(date_typedate, "%Y.%m.%d"))
    path_rep_file_tmp = os.path.join(conf['REPORT_DIR'], report_name_tmp)
    with open(path_rep_file_tmp, 'w', encoding='utf-8') as file_report:
        try:
            file_report.write(report_text_file)
        except Exception as er:
            logging.exception('Error create report %s: %s', path_rep_file_tmp, er)
    report_name = pathlib.Path(path_rep_file_tmp).stem + ".html"
    new_name_rep_file = os.path.join(conf["REPORT_DIR"], report_name)
    try:
        os.rename(path_rep_file_tmp, new_name_rep_file)
    except:
        logging.exception("Report %s - failed to create", report_name)
    logging.info("Create report file - %s ", report_name)
    if "jquery.tablesorter.min.js" not in os.listdir(conf["REPORT_DIR"]):
        if "jquery.tablesorter.min.js" in os.listdir("./"):
            shutil.copy(r"jquery.tablesorter.min.js",
                        os.path.join(conf["REPORT_DIR"], "jquery.tablesorter.min.js"))


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
        level=conf["STATUS_LOGGING"])


def parser_name_config() -> str:
    """
    Command line parsing procedure
    :return: filename config
    """
    parser = argparse.ArgumentParser(description='Log analizer')
    parser.add_argument('--config', type=str, help='Load config')
    args = parser.parse_args()
    return args.config


def configs_merger(conf: dict, default_conf_path=DEFAULT_CONFIG_PATH,
                   default_conf_f_name=DEFAULT_CONFIG_FILE_NAME) -> dict:
    """
    Config file upload function and merge with default config
    :param conf:
    :param default_conf_path: default config path
    :param default_conf_f_name: namefile default config
    :return: dict config
    """
    config_name = parser_name_config() if parser_name_config() else default_conf_f_name
    try:
        with open(os.path.join(default_conf_path, config_name)) as id_file_config:
            config_from_file = json.load(id_file_config, encoding="utf-8")
    except Exception as error_work_config:
        sys.exit(error_work_config)
    conf.update(config_from_file)
    return conf


def main(config):
    config.update(configs_merger(config))
    init_logging(config)
    if not os.path.isdir(config["LOG_DIR"]):
        logging.error("Scripts aborted - The directory 'LOG_DIR' is incorrect")
        sys.exit()
    logging.info("Start. Load config %s", config)
    log_name = search_last_log(config)
    if not report_processing_check(config, log_name):
        logging.info('Last raw log found: %s', log_name)
        mass_passed_data = parsing_log(config, log_name)
        mass_passed_data_sort = sort_list_url(mass_passed_data)
        create_report(config, log_name, create_result_mas(mass_passed_data_sort))
    else:
        logging.info('Last log has already been processed')


if __name__ == "__main__":
    try:
        main(default_config)
    except KeyboardInterrupt:
        logging.info('Script the script was interrupted by clicking Ctrl+C')
    except Exception as err:
        logging.exception(err)
