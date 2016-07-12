# coding=utf-8

import argparse
from multiprocessing import Pool
from robot.conf.gatherfailed import GatherFailedTests
from robot.parsing import TestData
from robot.api import TestSuiteBuilder, ResultWriter
from os import listdir
from os.path import isfile, join
import datetime
import shutil
import sys
from robot.result import ExecutionResult
import time

__author__ = 'zhangdonghao'
case_list = []
failed_case_list = []


def get_test_cases(test_data):
    for test in test_data.testcase_table:
        case_list.append(test.name)
    for child in test_data.children:
        get_test_cases(child)
    return case_list


def get_failed_test_cases(xml_path):
    gatherer = GatherFailedTests()
    ExecutionResult(xml_path, include_keywords=False).suite.visit(gatherer)
    for test in gatherer.tests:
        failed_case_list.append(test.split('.')[-1])
    return failed_case_list


def run(suite_path, test_case, results_dir):
    suite = TestSuiteBuilder().build(suite_path)
    suite.configure(include_tests=test_case.decode('utf-8'))
    result = suite.run(output='{0}/{1}.xml'.format(results_dir, test_case)
                       , non_critical_tags='non-critical')
    return {'passed': result.statistics.suite.stat.passed, 'failed': result.statistics.suite.stat.failed}


def main(processes=8, suite_path='.', mode='all'):
    # 判断命令行参数
    parser = argparse.ArgumentParser(description='parallel runner for robot framework')
    parser.add_argument('--suitepath', '-s', nargs=1, type=str, help='robot suite path, default is current path')
    parser.add_argument('--processes', '-p', nargs=1, type=int, help='parallel processes, default is 8')
    parser.add_argument('--mode', '-m', nargs=1, type=str, help='run mode, default will run all'
                                                                ', change it to failed to rerun failed cases from'
                                                                ' xml file generated by last run')
    args = parser.parse_args()
    try:
        suite_path = args.suitepath[0]
    except TypeError:
        pass
    try:
        processes = args.processes[0]
    except TypeError:
        pass
    try:
        mode = args.mode[0]
    except TypeError:
        pass
    passed = 0
    failed = 0
    results_dir = 'parallel_results'  # 输出xml结果的路径
    reports_dir = 'parallel_reports'  # 输出报告的路径，会在此路径输出log.html, report.html, output.xml三个文件

    shutil.rmtree(results_dir, ignore_errors=True)
    if mode == 'failed':
        cases = get_failed_test_cases('{}/output.xml'.format(reports_dir))
    else:
        cases = get_test_cases(TestData(source=suite_path))
    pool = Pool(processes=processes)
    results = []
    start_time = datetime.datetime.now()
    for case in cases:
        results.append(pool.apply_async(run, [suite_path, case, results_dir]))
        time.sleep(1)
    for result in results:
        passed = passed + result.get()['passed']
        failed = failed + result.get()['failed']
    pool.close()
    pool.join()
    end_time = datetime.datetime.now()
    xml_files = [join('{}/'.format(results_dir), f)
                 for f in listdir(results_dir) if isfile(join('{}/'.format(results_dir), f))]
    ResultWriter(*xml_files) \
        .write_results(merge=True
                       , log='{}/log.html'.format(reports_dir)
                       , report='{}/report.html'.format(reports_dir)
                       , output='{}/output.xml'.format(reports_dir))
    print('start_time: ' + str(start_time))
    print('end_time: ' + str(end_time))

if __name__ == '__main__':
    main()
