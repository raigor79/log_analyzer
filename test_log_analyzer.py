import unittest
import log_analyzer

MASK_URL = r'(?<=GET\s)(/\S+)'
MASK_REQUEST_TIME = r'(?<=\ )\d+\.\d+?$'

string1 = '1.194.135.240 -  - [29/Jun/2017:03:50:22 +0300] "GET /api/v2/group/7786679/statistic/sites/?date_type=day&date_from=2017-06-28&date_to=2017-06-28 HTTP/1.1" 200 22 "-" "python-requests/2.13.0" "-" "1498697422-3979856266-4708-9752772" "8a7741a54297568b" 0.067'
string2 = '1.169.137.128 -  - [29/Jun/2017:03:50:22 +0300] "GET /api/v2/group/1769230/banners HTTP/1.1" 200 1020 "-" "Configovod" "-" "1498697422-2118016444-4708-9752747" "712e90144abee9" 0.628'
string3 = '1.169.137.128 -  - [29/Jun/2017:03:50:22 +0300] "-" 200 1020 "-" "Configovod" "-" "1498697422-2118016444-4708-9752747" "712e90144abee9" 0.628'
test_dict1 = {'url1': ['1', '2', '3', '4', '5',],'url2' : ['1'],'url3': ['5', '4', '3', '2', '1']}
test_dict2 = {'url1': ['1.1', '2.2', '3.3', '4.4', '5.5'],'url2': ['1.1'],'url3': ['5.5', '4.4', '3.3', '2.2', '1.1']}
test_dict3 = {'url1': ['1.1', '2.2', '3.3', '4.4', '5.5'],'url2': [''],'url3': ['5.5', '4.4', '3.3', '2.2', '1.1']}
test_dict4 = {'url1': ['1.1', '2.2', '3.3', '4.4', '5.5'],'url2': None,'url3': ['5.5', '4.4', '3.3', '2.2', '1.1']}



class MyTestCase(unittest.TestCase):
    def test_parsing_string(self):
        self.assertEqual(log_analyzer.parsing_string(string1,[MASK_URL,MASK_REQUEST_TIME]), [
            "/api/v2/group/7786679/statistic/sites/?date_type=day&date_from=2017-06-28&date_to=2017-06-28","0.067"],
                         False)
        self.assertEqual(log_analyzer.parsing_string(string2, [MASK_URL, MASK_REQUEST_TIME]), [
            "/api/v2/group/1769230/banners", "0.628"],
                         False)
        self.assertEqual(log_analyzer.parsing_string(string3, [MASK_URL, MASK_REQUEST_TIME]), [
            None, "0.628"],
                         False)
    def test_value_percent(self):
        self.assertEqual(log_analyzer.value_percent(1,100), 1)
        self.assertEqual(log_analyzer.value_percent(1100.10, 10000), 11.001)
        self.assertEqual(log_analyzer.value_percent(10, 100), 10)

    def test_count_total_request(self):
        self.assertEqual(log_analyzer.count_total_request(test_dict1),11)
        self.assertEqual(log_analyzer.count_total_request(test_dict2), 11)
        #self.assertEqual(log_analyzer.count_total_request(test_dict3), 10)
        #self.assertEqual(log_analyzer.count_total_request(test_dict4), 11)
    def test_count_total_time_request(self):
        self.assertEqual(log_analyzer.time_total_request(test_dict1),31.0)
        self.assertEqual(log_analyzer.time_total_request(test_dict2), 34.1)
        #self.assertEqual(log_analyzer.count_total_time_request(test_dict3), 33.0)
    def test_median_time_request(self):
        self.assertEqual(log_analyzer.median_time_request(test_dict1['url1']),3)


if __name__ == '__main__':
    unittest.main()