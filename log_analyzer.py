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
from typing import Union
from typing import List
from typing import NamedTuple
from typing import Dict

# MASK_REQUEST
# url regular expression pattern MASK_URL = (?<=GET\s)(/\S+)
# request time regular expression pattern MASK_REQUEST_TIME = ((?<=\ )\d+\.\d+?$)

MASK_REQUEST = r'(?<=GET\s)(/\S+).+((?<=\ )\d+\.\d+?$)'

MASK_LOG = r'nginx-access-ui.log-(\d+)((\.gz\b)|(\.log\b))'

DEFAULT_CONFIG_PATH = os.path.dirname(__file__)

DEFAULT_CONFIG_FILE_NAME = "default.cfg"

PATH_TEMPLATE_REPORT = "./report.html"


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


LastLog = collections.namedtuple("LastLog", ['path', 'date'])


def search_last_log(config: dict) -> NamedTuple:
    """
    search function for the last log file in the directory 'LOG_DIR'
    :param config -  dictionary  with the directory log file:
    :return:  last_log  - filename last log file
    """
    date_last_log = None
    for file_name in os.listdir(os.path.join(config["LOG_DIR"])):
        if re.match(MASK_LOG, file_name):
            try:
                date_log = datetime.datetime.strptime(re.match(MASK_LOG,
                                                               file_name).group(1),
                                                      '%Y%m%d').date()
            except:
                continue
            if date_last_log is None or date_log > date_last_log:
                date_last_log = date_log
                last_log = file_name
    if date_last_log:
        return LastLog(path=last_log, date=date_last_log)


def report_processing_check(config: dict, last_log: NamedTuple) -> bool:
    """
    Function processing check reporting the latest log
    :param config: dictionary  with the directory report file 'REPORT_DIR'
    :param last_log: name last log file
    :return: True if the file exists in the directory or
    False if the file is not in the directory
    """
    report_name = 'report-{0}.html'.format(datetime.datetime.strftime(last_log.date,
                                                                      "%Y.%m.%d"))
    if os.path.isdir(config["REPORT_DIR"]):
        files_list = os.listdir(config["REPORT_DIR"])
        return True if report_name in files_list else False
    else:
        try:
            os.mkdir(config["REPORT_DIR"])
        except:
            logging.exception("Create directory% s failed" % config["REPORT_DIR"])
        else:
            logging.info("Successfully created directory %s " % config["REPORT_DIR"])
        return False


def parsed_string(string_pars: str, template: str) -> List[List[str]]:
    """
    Function parsing string 'string' pattern list template
    :param string: any string
    :param template: template [template1, [template2],...[]],
    where [template1], [template2], ... is a regular expression
    :return: list of found strings
    """
    parsed_result = re.search(template, string_pars)
    if parsed_result is not None:
        pars_list = [parsed_result.group(1),
                     parsed_result.group(2)]
        return pars_list


def process_message(total_str: int, processed_str: int, permissible_error: int) -> str:
    """
    The function calculates the parsing error and, on the threshold, issues a message to the log
    :param total_str: total number of parsing operations
    :param processed_str: number of defined values
    :param permissible_error: threshold error
    :return: message string
    """
    error_pars = 100 - 100 * processed_str / total_str
    if error_pars < permissible_error:
        msg = 'Process to parse log complete'
    else:
        msg = 'Unable to parse most of the log Error > %d \% ' \
              'perhaps the logging format has changed' % permissible_error
    return msg


def parsed_string_log(config: dict, log_file_name: NamedTuple) -> List[List[str]]:
    """
    Function-generator read log string from file with filename 'log_file_name'
    :param config: dictionary with structure containing the directory log file 'LOG_DIR'
    :param log_file_name: name processed log file
    :return: structure list [url:str, request_time:str]
    """
    log_file_path = os.path.join(config["LOG_DIR"], log_file_name.path)
    open_log = gzip.open if log_file_path.endswith(".gz") else open
    with open_log(log_file_path, 'rt', encoding='utf-8') as log_file:
        total_str = 0
        processed_str = 0
        for log_string in log_file:
            total_str += 1
            parsed_list = parsed_string(log_string, MASK_REQUEST)
            if parsed_list is None:
                continue
            processed_str += 1
            yield parsed_list
    logging.info(process_message(total_str,
                                 processed_str,
                                 config["THRESHOLD_ERROR_PARS_PERCENT"]))


def sort_list_url(mass_url: List[List[str]]) -> Dict:
    """
    Function of sorting the request time by the same URL
    :param mass_url: list [ "url","time_request"]
    :return: dictionary with elements 'url': [time_request1,time_request2,..]
    """
    mas_sort_url = collections.defaultdict(list)
    for url, value_time in mass_url:
        mas_sort_url[url].append(value_time)
    return mas_sort_url


def time_sum_url(list_item: List[str]) -> float:
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


def time_max(list_item: List[str]) -> float:
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


def median_time_request(list_item: List[str]) -> float:
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


def write_url_dict(url_str: str,
                   line_time: List[str],
                   total_count: int,
                   total_time: float) -> dict:
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
                     "time_avg": time_sum_url(line_time) / len(line_time),
                     "time_max": time_max(line_time),
                     "time_sum": time_sum,
                     "url": url_str,
                     "time_med": median_time_request(line_time),
                     "time_perc": time_sum / total_time * 100,
                     "count_perc": count_r / total_count * 100}
    return url_dict_stat


def _create_result_mas(data_mas: dict) -> List[dict]:
    """
    Create function sorted by "max_time" list of statistics data
    :param data_mas : source dictionary of url and time request
    :return: list dictionary of url and request statistics
    """
    total_count = 0
    total_time = 0
    for index in data_mas.keys():
        total_count += len(data_mas[index])
        for time_str in data_mas[index]:
            total_time += float(time_str)
    result_mas = []
    for item_mas in data_mas.keys():
        result_mas.append(write_url_dict(item_mas,
                                         data_mas[item_mas],
                                         total_count,
                                         total_time))
    return sorted(result_mas,
                  key=operator.itemgetter("time_sum"),
                  reverse=True)


def _insertion_data_in_template(all_path_template_file: str,
                                result_mas: List[dict],
                                num_rep: int) -> str:
    """
    The function of inserting data into a template
    :param all_path_template_file:  path template file
    :param result_mas: mass with data
    :param num_rep: number of urls in saved report
    :return: formatted report text
    """
    with open(all_path_template_file, 'r', encoding='utf-8') as file_template_report:
        template_text = file_template_report.read()
    size_rep = num_rep if num_rep < len(result_mas) else len(result_mas)
    report_text = string.Template(template_text)
    return report_text.safe_substitute(table_json=result_mas[0:size_rep])


def creation_report(conf: dict, log_file: NamedTuple, report_text: str):
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
    report_tmp = 'report-{0}.tmp'.format(datetime.datetime.strftime(log_file.date,
                                                                    "%Y.%m.%d"))
    path_rep_file_tmp = os.path.join(conf['REPORT_DIR'], report_tmp)
    with open(path_rep_file_tmp, 'w', encoding='utf-8') as file_report:
        file_report.write(report_text)
    report_name = pathlib.Path(path_rep_file_tmp).stem + ".html"
    new_name_rep_file = os.path.join(conf["REPORT_DIR"], report_name)
    if os.path.exists(path_rep_file_tmp):
        os.rename(path_rep_file_tmp, new_name_rep_file)


def init_logging(conf: dict):
    """
    Logging module settings function
    :param conf: dictionary with structure containing
                    name log file 'LOG_ANALYZER_PATH',
                    default 'LOG_ANALYZER_PATH' = None
    :return:
    """
    format_log = '[%(asctime)s] %(levelname).1s %(message)s'
    try:
        logging.basicConfig(
            filename=conf["LOG_ANALYZER_PATH"],
            format=format_log,
            datefmt='%Y.%m.%d %H:%M:%S',
            level=conf["STATUS_LOGGING"])
    except Exception as error_log:
        raise EnvironmentError('Error loging: {}'.format(error_log))


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
            config_from_file = json.load(id_file_config,
                                         encoding="utf-8")
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
        logging.info('Last raw log found: %s',
                     log_name)
        mass_passed_data = parsed_string_log(config,
                                             log_name)
        mass_passed_data_sort = sort_list_url(mass_passed_data)

        report_text = _insertion_data_in_template(PATH_TEMPLATE_REPORT,
                                                  _create_result_mas(mass_passed_data_sort),
                                                  config["REPORT_SIZE"])
        creation_report(config,
                        log_name,
                        report_text)
    else:
        logging.info('Last log has already been processed')


if __name__ == "__main__":
    try:
        main(default_config)
    except KeyboardInterrupt:
        logging.info('Script the script was interrupted by clicking Ctrl+C')
    except Exception as err:
        logging.exception(err)
