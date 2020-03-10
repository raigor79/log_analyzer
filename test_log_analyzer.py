import unittest
import log_analyzer

MASK_URL = r'(?<=GET\s)(/\S+)'
MASK_REQUEST_TIME = r'(?<=\ )\d+\.\d+?$'

string1 = '1.194.135.240 -  - [29/Jun/2017:03:50:22 +0300] "GET /api/v2/group/7786679/statistic/sites/?date_type=day&date_from=2017-06-28&date_to=2017-06-28 HTTP/1.1" 200 22 "-" "python-requests/2.13.0" "-" "1498697422-3979856266-4708-9752772" "8a7741a54297568b" 0.067'
string2 = '1.169.137.128 -  - [29/Jun/2017:03:50:22 +0300] "GET /api/v2/group/1769230/banners HTTP/1.1" 200 1020 "-" "Configovod" "-" "1498697422-2118016444-4708-9752747" "712e90144abee9" 0.628'
string3 = '1.169.137.128 -  - [29/Jun/2017:03:50:22 +0300] "-" 200 1020 "-" "Configovod" "-" "1498697422-2118016444-4708-9752747" "712e90144abee9" 0.628'
test_dict1 = {'url1': ['1', '2', '3', '4', '5',],'url2' : ['1'],'url3': ['5', '4', '3', '2', '1']}
test_dict2 = {'url1': ['1.1', '2.2', '3.3', '4.4', '5.5'],'url2': ['1.1'],'url3': ['5.5', '4.4', '3.3', '2.2', '1.1']}
test_dict3 = {'url1': ['1.1', '2.2', '3.3', '4.4', '5.5'],'url2': [''],'url3': [ '3.3', '2.2', '1.1','5.5', '4.4',]}
test_dict4 = {'url1': ['1.1', '2.2', '3.3', '4.4', '5.5'],'url2': ['1'],'url3': ['5.5', '4.4', '3.3', '2.2', '1.1']}
test_dict5 = {'url1': ['1', '1', '1', '1', '1',],'url3': ['1', '1', '1', '1', '1']}

test_dict_rep1 = {"count": 5, "time_avg": 1.0, "time_max": 1.0,
                 "time_sum": 5.0, "url": 'url1',
                 "time_med": 1, "time_perc": 50.0, "count_perc": 50.0}
test_dict_rep2 = {"count": 5, "time_avg": 1, "time_max": 1.0,
                 "time_sum": 5.0, "url": 'url3',
                 "time_med": 1, "time_perc": 50.0, "count_perc": 50.0}

test_dict_stat_urlt = [test_dict_rep1, test_dict_rep2]

test_list_url_time1 = [['url1', '1'],['url1', '1'],['url3', '1'],['url1', '1'],['url3', '1'],
                      ['url3', '1'],['url3', '1'],['url1', '1'],['url3', '1'],['url1', '1'],]
test_list_url_time2 = [['url1', '1.1'],['url1', '2.2'],['url2', '1.1'],['url3', '5.5'],['url1', '3.3'],['url3', '4.4'],
                      ['url3', '3.3'],['url3', '2.2'],['url1', '4.4'],['url3', '1.1'],['url1', '5.5']]

class MyTestCase(unittest.TestCase):
    def test_parsing_string(self):
        self.assertEqual(log_analyzer.parsing_string(string1,[MASK_URL,MASK_REQUEST_TIME]), [
            "/api/v2/group/7786679/statistic/sites/?date_type=day&date_from=2017-06-28&date_to=2017-06-28","0.067"],
                         False)
        self.assertEqual(log_analyzer.parsing_string(string2, [MASK_URL, MASK_REQUEST_TIME]), [
            "/api/v2/group/1769230/banners", "0.628"],
                         False)
        self.assertEqual(log_analyzer.parsing_string(string3, [MASK_URL, MASK_REQUEST_TIME]), [
            '', "0.628"],
                         False)
    def test_value_percent(self):
        self.assertEqual(log_analyzer.value_percent(1,100), 1)
        self.assertEqual(log_analyzer.value_percent(1100.10, 10000), 11.001)
        self.assertEqual(log_analyzer.value_percent(10, 100), 10)

    def test_count_total_request(self):
        self.assertEqual(log_analyzer.count_total_request(test_dict1),11)
        self.assertEqual(log_analyzer.count_total_request(test_dict2), 11)

    def test_count_total_time_request(self):
        self.assertEqual(log_analyzer.time_total_request(test_dict1),31.0)
        self.assertEqual(log_analyzer.time_total_request(test_dict2), 34.1)

    def test_median_time_request(self):
        self.assertEqual(log_analyzer.median_time_request(test_dict1['url1']),3)
        self.assertEqual(log_analyzer.median_time_request(test_dict2['url3']), 3.3)
        self.assertEqual(log_analyzer.median_time_request(test_dict3['url3']), 3.3)

    def test_process_message(self):
        self.assertEqual(log_analyzer.process_message(100, 60),'Process complete')
        self.assertEqual(log_analyzer.process_message(10000, 100), 'Unable to parse most of the log Error >60% perhaps the logging format has changed')

    def test_create_report(self):
        self.assertEqual(log_analyzer.create_report(log_analyzer.config,'test20200302.log',test_dict_stat_urlt ),None)

    def test_create_result_mas(self):
        self.assertEqual(log_analyzer.create_result_mas(test_dict5), test_dict_stat_urlt)

    def test_time_max(self):
        self.assertEqual(log_analyzer.time_max([1,2,3,4,5,6,7]),7)
        self.assertEqual(log_analyzer.time_max([1, 21, 3, 4, 5, 6, 7]), 21)
        self.assertEqual(log_analyzer.time_max(['1', '21', '3','4', '5', '6', '7']), 21)
        self.assertEqual(log_analyzer.time_max(['1.8', '13.7', '3.7', '4.6', '5.4', '6.9', '7.8']), 13.7)

    def test_time_sum_url(self):
        self.assertEqual(log_analyzer.time_sum_url([1,2,3,4,5,6,7]),28)
        self.assertEqual(log_analyzer.time_sum_url([1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0]), 28)
        self.assertEqual(log_analyzer.time_sum_url(['1', '2', '3', '4', '5', '6', '7']), 28)
        self.assertEqual(log_analyzer.time_sum_url(['1.2', '2.9', '3.9', '4.9', '5.9', '68.8', '79']), 166.6)

    def test_time_average(self):
        self.assertEqual(log_analyzer.time_average([1,2,3,4,5,6,7]),28/7)
        self.assertEqual(log_analyzer.time_average(['1.2', '2.9', '3.9', '4.9', '5.9', '68.8', '79']), 166.6/7)

    def test_sort_list_url(self):
        self.assertEqual(log_analyzer.sort_list_url(test_list_url_time1),test_dict5)
        self.assertEqual(log_analyzer.sort_list_url(test_list_url_time2), test_dict2)


if __name__ == '__main__':
    unittest.main()