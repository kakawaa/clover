"""
Chapter 1
The cases may be an interface or a suite.The suite is a collection of multiple interfaces.
Host, path, header, parameter and body support parameterized variables, you can use ${var}
to represent the value of the variable var.The parameters passed between interfaces extracted
by extract are also considered as variables, and the value of extract['varibale'] is the variable name.
    cases: [
        {
            'id': 25,
            'team': 'qa',
            'project': 'testing platform',
            'name': 'alibaba map',
            'method': 'get',
            'host': '${ditu}',
            'path': '/service/regeo',
            'header': [
                {
                    'key': 'clover',
                    'value': '0.3.4'
                }
            ],
            'params': [
                {
                    'key': 'longitude',
                    'value': '121.04925573429551'
                },
                {
                    'key': 'latitude',
                    'value': '31.315590522490712'
                }
            ],
            'body': {
                'data': '',
                'mode': 'raw'
            },
            'verify': [
                {
                    'expected': '1',
                    'convertor': 'int',
                    'extractor': 'delimiter',
                    'comparator': 'equal',
                    'expression': 'status'
                },
                {
                    'expected': '苏州市',
                    'convertor': 'str',
                    'extractor': 'delimiter',
                    'comparator': 'equal',
                    'expression': 'data.city'
                },
                {
                    'expected': '512',
                    'convertor': 'int',
                    'extractor': 'regular',
                    'comparator': 'equal',
                    'expression': '\\"areacode\\":\\"(.+?)\\",'
                }
            ],
            'extract': [
                {
                    'selector': 'delimiter',
                    'variable': 'data',
                    'varibale': '',
                    'expression': 'status'
                }
            ],
            'enable': 0,
            'created': '2020-02-07T13:52:23',
            'updated': '2020-04-19T14:15:19'
        },
        ...
    ]
------------------------------------------- It's a gorgeous divider -------------------------------------------
Chapter 2
Executor uses the result property to record the result of execution.
The structure of the result property is used for data presentation of the report detail page, as follows:
    result: {
        'name1': {
            'status': 'passed',                     # ['passed', 'failed', 'error', 'skiped']
            'start': '2020-04-24 14:59:56',
            'end': '2020-04-24 14:59:57',
            'elapsed': 238568,
            'result': [
                {
                    "actual": 1,
                    "expect": 1,
                    "status": "passed",
                    "operate": "equal"
                }, {
                    "actual": "苏州市",
                    "expect": "苏州市",
                    "status": "passed",
                    "operate": "equal"
                }, {
                    "actual": 512,
                    "expect": 512,
                    "status": "passed",
                    "operate": "equal"
                }
            ]
        },
        'name2': {}
    }
"""

import datetime

from clover.common import friendly_datetime

from clover.core.report import Report
from clover.core.request import Request
from clover.core.variable import Variable
from clover.core.validator import Validator
from clover.core.logger import Logger, LogLevel
from clover.core.exception import ResponseException


class Executor():

    def __init__(self, type='trigger', log='default'):
        self.variables = []
        self.status = 0
        self.message = 'ok'
        self.type = type
        self.start = 0
        self.end = 0
        self.report = Report()

    def execute(self, cases, data=None):
        """
        :param cases:
        :param data:
        :return: 返回值为元组，分别是flag，message和接口请求后的json数据。
        """
        # 注意需要在执行最前端实例化report，report初始化时会记录开始时间点。
        report, execute_detail = Report(), {}
        """
        # 注意，变量对象必须在循环外被实例化，变量声明周期与执行器相同。
        # 使用团队和项目属性查询平台预置的自定义变量，通过触发时传递。
        # trigger参数为触发时用户添加的变量，优先级高于平台预置变量。
        """
        id = data.get("id")
        type = data.get('type', 'interface')
        sub_type = data.get('sub_type', 'suite')

        team = data.get("team")
        project = data.get("project")
        trigger = data.get("trigger", {})

        variable = Variable(team, project, trigger)

        # 因为是类属性存储日志，使用前先清理历史日志数据。
        Logger.clear()
        Logger.log("团队：{}，项目：{}".format(team, project), "开始执行")

        for case in cases:

            name = case.get("name")
            execute_detail.setdefault(name, {})
            execute_detail[name].setdefault('start', friendly_datetime(datetime.datetime.now()))

            # 发送http请求
            method = case.get("method")
            host = case.get("host")
            path = case.get("path")
            header = case.get('header', {})
            params = case.get('params', {})
            body = case.get('body', {})

            request = Request(method, host, path, header, params, body)
            validator = Validator()

            variable.replace_variable(request)
            try:
                response = request.send_request()
                validator.verify(case, response)
                variable.extract_variable_from_response(case, response)

                execute_detail[name].setdefault('elapsed', response.elapsed.microseconds)
            except ResponseException:
                Logger.logs("请求异常，状态码：{}".format(request.status), "发送请求", LogLevel.ERROR)
                Logger.logs(request.message, "发送请求", LogLevel.ERROR)

            execute_detail[name].setdefault('status', validator.status)
            execute_detail[name].setdefault('result', validator.result)
            execute_detail[name].setdefault('end', friendly_datetime(datetime.datetime.now()))

        # Logger.save(type, sub_type, id)
        # 存储运行的测试报告到数据库。
        print(50 * '*')
        print(execute_detail)
        print(50 * '*')
        report.save(data, execute_detail, [])
