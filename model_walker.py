# coding=utf-8

from networkx.readwrite import graphml
from os import listdir
from os.path import isfile, join
import os
from robot.api import TestSuite
from robot.reporting import ResultWriter
import random
import networkx as nx
from WalkerConfig import walker_config
import argparse

__author__ = 'zhangdonghao'


def init_robot(file_path):
    # 初始化robot suite
    test_suite_name = os.path.basename(file_path).split('.')[0]
    suite = TestSuite(test_suite_name)
    suite.resource.imports.library(walker_config.robot_library)
    return suite, test_suite_name


def generate_suite(suite, nodes, edges, exec_path):
    test = suite.tests.create(str(exec_path).strip(' '))
    for i in range(len(exec_path) - 1):
        prev_node = exec_path[i]
        next_node = exec_path[i + 1]
        if str(nodes[prev_node]['label']).lower() == 'start':
            test.keywords.create('Log', args=['测试开始'])
            e_label = edges['n0'][next_node]['label']
            if len(e_label.split('/')) > 1:
                test.keywords.create(e_label.split('/')[0], args=[e_label.split('/')[1]])
            else:
                test.keywords.create(edges['n0'][next_node]['label'])
            test.keywords.create('Log', args=['当前的节点为: {}'.format(next_node)])
            n_label = nodes[next_node]['label']
            if len(n_label.split('/')) > 1:
                test.keywords.create(n_label.split('/')[0], args=[n_label.split('/')[1]])
            else:
                test.keywords.create(n_label)
        else:
            test.keywords.create('Log', args=['当前的向量为: {}'.format(edges[prev_node][next_node]['id'])])
            e_label = edges[prev_node][next_node]['label']
            if len(e_label.split('/')) > 1:
                test.keywords.create(e_label.split('/')[0], args=[e_label.split('/')[1]])
            else:
                test.keywords.create(e_label)
            test.keywords.create('Log', args=['当前的节点为: {}'.format(next_node)])
            n_label = nodes[next_node]['label']
            if len(n_label.split('/')) > 1:
                test.keywords.create(n_label.split('/')[0], args=[n_label.split('/')[1]])
            else:
                test.keywords.create(n_label)


def random_walker(file_path, coverage=100):
    suite = init_robot(file_path)

    g = graphml.read_graphml(file_path)
    e = [e for e in g.edges_iter()]
    n = [n for n in g.node]
    edges = g.edge
    nodes = g.node
    now_coverage = 0
    exec_paths = []

    while now_coverage < coverage:
        curr_path = []
        node = 'n0'
        while g.successors(node):
            if len(g.successors(node)) > 0 and node == 'n0':
                curr_path.append('n0')
                node = g.successors(node)[int(random.uniform(0, len(g.successors(node))))]
                curr_path.append(node)
            elif len(g.successors(node)) > 0 and node != 'n0':
                prev_node = curr_path[-2]
                node = g.successors(node)[int(random.uniform(0, len(g.successors(node))))]
                if node == prev_node:
                    break
                curr_path.append(node)
            elif len(g.successors(node)) == 0:
                break
        exec_paths.append(curr_path)
        if len(exec_paths) > 1:
            exec_paths = sorted(exec_paths)
            exec_paths = [exec_paths[i] for i in range(len(exec_paths)) if i == 0 or exec_paths[i] != exec_paths[i - 1]]
            curr_nodes = list(set([item for sub_list in exec_paths for item in sub_list]))
            now_coverage = float(len(curr_nodes)) / float(len(n)) * 100

    # 整合成robot suite
    for exec_path in exec_paths:
        generate_suite(suite[0], nodes, edges, exec_path)

    # 运行suite并回收报告
    suite[0].run(output='results/{}.xml'.format(suite[1]))
    xml_files = [join('results/', f) for f in os.listdir('results/') if isfile(join('results/', f))]
    ResultWriter(*xml_files) \
        .write_results(log='reports/{}_log.html'.format(suite[1])
                       , report='reports/{}_report.html'.format(suite[1])
                       , output='reports/{}_output.xml'.format(suite[1]))


def full_walker(file_path):
    suite = init_robot(file_path)

    g = graphml.read_graphml(file_path)
    e = [e for e in g.edges_iter()]
    n = [n for n in g.node]
    edges = g.edge
    nodes = g.node

    revers_paths = []
    exec_paths = []

    # 获取所有反向路径
    for edge1 in e:
        for edge2 in e:
            if edge1[0] == edge2[1] and edge1[1] == edge2[0]:
                revers_paths.append(edge1)

    # 遍历反向路径
    if len(revers_paths) > 0:
        for revers_path in revers_paths:
            for path in nx.all_simple_paths(g, 'n0', revers_path[0]):
                if path[-2] == revers_path[1]:
                    exec_paths.append(path + [revers_path[1]])

    # 搜寻所有的末端路径
    for node in n:
        if len(g.successors(node)) == 0:
            for path in nx.all_simple_paths(g, 'n0', node):
                exec_paths.append(path)

    # 整合成robot suite
    for exec_path in exec_paths:
        generate_suite(suite[0], nodes, edges, exec_path)

    # 运行suite并回收报告
    suite[0].run(output='results/{}.xml'.format(suite[1]))
    xml_files = [join('results/', f) for f in listdir('results/') if isfile(join('results/', f))]
    ResultWriter(*xml_files) \
        .write_results(log='reports/{}_log.html'.format(suite[1])
                       , report='reports/{}_report.html'.format(suite[1])
                       , output='reports/{}_output.xml'.format(suite[1]))


def specify_walker(file_path, walk_path):
    suite = init_robot(file_path)

    g = graphml.read_graphml(file_path)
    e = [e for e in g.edges_iter()]
    n = [n for n in g.node]
    edges = g.edge
    nodes = g.node

    sorted_path = []
    walk_path = walk_path.split(',')
    for path in walk_path:
        temp = path.replace('[', '').replace(']', '').replace(',', '').replace("'", '').strip()
        sorted_path.append(temp)
    generate_suite(suite[0], nodes, edges, sorted_path)

    # 运行suite并回收报告
    suite[0].run(output='results/{}.xml'.format(suite[1]))
    xml_files = [join('results/', f) for f in os.listdir('results/') if isfile(join('results/', f))]
    ResultWriter(*xml_files) \
        .write_results(log='reports/{}_log.html'.format(suite[1])
                       , report='reports/{}_report.html'.format(suite[1])
                       , output='reports/{}_output.xml'.format(suite[1]))


def main():
    # 判断命令行参数
    parser = argparse.ArgumentParser(description='Model walker, including random, full and specify mode.')
    parser.add_argument('--mode', '-m', nargs=1, type=str, help='assign a mode: random, full or specify.'
                        , required=True)
    parser.add_argument('--coverage', '-c', nargs=1, type=int, help='test node coverage,'
                                                                    ' optional when mode is random. default=100')
    parser.add_argument('--modelpath', '-mp', nargs=1, type=str, help='model path, can be a file or folder'
                        , required=True)
    parser.add_argument('--walkpath', '-w', nargs='+', help='walk path, specify a fixed path,'
                                                            ' required when mode is specify. Note: use double quote if'
                                                            'spaces exist in argument.')
    args = parser.parse_args()
    mode = args.mode[0]
    try:
        coverage = args.coverage[0]
    except TypeError:
        coverage = None
    model_path = args.modelpath[0]
    try:
        walk_path = args.walkpath[0]
    except TypeError:
        walk_path = None

    if mode == 'random' and coverage is not None:
        if isfile(model_path):
            random_walker(model_path, coverage)
        else:
            model_files = [join(model_path, f)
                           for f in listdir(model_path) if isfile(join(model_path, f))]
            for model_file in model_files:
                random_walker(model_file, coverage)
    elif mode == 'random' and coverage is None:
        if isfile(model_path):
            random_walker(model_path)
        else:
            model_files = [join(model_path, f)
                           for f in listdir(model_path) if isfile(join(model_path, f))]
            for model_file in model_files:
                random_walker(model_file)
    elif mode == 'full':
        if isfile(model_path):
            full_walker(model_path)
        else:
            model_files = [join(model_path, f)
                           for f in listdir(model_path) if isfile(join(model_path, f))]
            for model_file in model_files:
                full_walker(model_file)
    elif mode == 'specify' and walk_path is None:
        parser.error('mode specify need walkpath parameter')
    elif mode == 'specify' and walk_path is not None:
        if isfile(model_path):
            specify_walker(model_path, walk_path)
        else:
            model_files = [join(model_path, f)
                           for f in listdir(model_path) if isfile(join(model_path, f))]
            for model_file in model_files:
                specify_walker(model_file, walk_path)


if __name__ == '__main__':
    main()
