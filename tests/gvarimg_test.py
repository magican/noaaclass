#!/usr/bin/env python
# -*- coding: utf-8 -*-
import time
import unittest
from datetime import datetime

from noaaclass import noaaclass


class TestGvarimg(unittest.TestCase):
    def remove_all_in_server(self):
        sub_data = self.noaa.subscribe.gvar_img.get()
        ids = [d['id'] for d in sub_data if '[auto]' in d['name']]
        if len(ids):
            self.noaa.get('sub_delete?actionbox=%s' % '&actionbox='.join(ids))

    def init_subscribe_data(self):
        self.sub_data = [
            {
                'id': '+',
                'enabled': True,
                'name': '[auto] sample1',
                'north': -26.72,
                'south': -43.59,
                'west': -71.02,
                'east': -48.52,
                'coverage': ['SH'],
                'schedule': ['R'],
                'satellite': ['G13'],
                'channel': [1],
                'format': 'NetCDF',
            },
            {
                'id': '+',
                'enabled': False,
                'name': '[auto] sample2',
                'north': -26.73,
                'south': -43.52,
                'west': -71.06,
                'east': -48.51,
                'coverage': ['SH'],
                'schedule': ['R'],
                'satellite': ['G13'],
                'channel': [2],
                'format': 'NetCDF',
            },
            {
                'id': '+',
                'enabled': True,
                'name': 'static',
                'north': -26.73,
                'south': -33.52,
                'west': -61.06,
                'east': -48.51,
                'coverage': ['SH'],
                'schedule': ['R'],
                'satellite': ['G13'],
                'channel': [1],
                'format': 'NetCDF',
            },
        ]
        old_data = self.noaa.subscribe.gvar_img.get()
        names = [d['name'] for d in self.sub_data]
        self.sub_data.extend([x for x in old_data if x['name'] not in names])

    def init_request_data(self):
        self.req_data = [
            {
                'id': '+',
                'north': -26.72,
                'south': -43.59,
                'west': -71.02,
                'east': -48.52,
                'coverage': ['SH'],
                'schedule': ['R'],
                'satellite': ['G13'],
                'channel': [1],
                'format': 'NetCDF',
                'start': datetime(2014, 9, 16, 10, 0, 0),
                'end': datetime(2014, 9, 16, 17, 59, 59)
            },
            {
                'id': '+',
                'north': -26.73,
                'south': -43.52,
                'west': -71.06,
                'east': -48.51,
                'coverage': ['SH'],
                'schedule': ['R'],
                'satellite': ['G13'],
                'channel': [2],
                'format': 'NetCDF',
                'start': datetime(2014, 9, 2, 10, 0, 0),
                'end': datetime(2014, 9, 3, 17, 59, 59)
            },
        ]

    def setUp(self):
        self.noaa = noaaclass.connect('noaaclass.t', 'noaaclassadmin')
        self.init_subscribe_data()
        self.init_request_data()
        self.remove_all_in_server()

    def tearDown(self):
        self.remove_all_in_server()

    def test_subscribe_get_empty(self):
        gvar_img = self.noaa.subscribe.gvar_img
        auto = lambda x: '[auto]' in x['name']
        data = list(filter(auto, gvar_img.get()))
        self.assertEqual(data, [])

    def test_subscribe_get(self):
        gvar_img = self.noaa.subscribe.gvar_img
        gvar_img.set(self.sub_data)
        data = gvar_img.get(append_files=True)
        for subscription in data:
            for key in ['id', 'enabled', 'name', 'coverage', 'schedule',
                        'south', 'north', 'west', 'east', 'satellite',
                        'format', 'orders']:
                self.assertIn(key, list(subscription.keys()))
            for order in subscription['orders']:
                for key in ['id', 'last_activity', 'status', 'size', 'files',
                            'datetime']:
                    self.assertIn(key, list(order.keys()))

    def test_subscribe_set_new_elements(self):
        gvar_img = self.noaa.subscribe.gvar_img
        copy = gvar_img.set(self.sub_data)
        self.assertGreaterEqual(len(copy), len(self.sub_data))
        [self.assertIn(k, list(copy[i].keys()))
         for i in range(len(self.sub_data)) for k in list(self.sub_data[i].keys())]
        [self.assertEqual(copy[i][k], v)
         for i in range(len(self.sub_data))
         for k, v in list(self.sub_data[i].items())
         if k is not 'id']

    def test_subscribe_set_edit_elements(self):
        gvar_img = self.noaa.subscribe.gvar_img
        copy = gvar_img.set(self.sub_data)
        self.assertGreaterEqual(len(copy), 2)
        copy[0]['name'] = '[auto] name changed'
        copy[1]['channel'] = [4, 5]
        gvar_img.set(copy)
        edited = gvar_img.get()
        self.assertEqual(edited[0]['name'], copy[0]['name'])
        self.assertEqual(edited[1]['channel'], copy[1]['channel'])

    def test_subscribe_set_remove_element(self):
        gvar_img = self.noaa.subscribe.gvar_img
        copy = gvar_img.set(self.sub_data, async=True)
        self.assertEqual(gvar_img.get(), copy)
        criteria = lambda x: 'sample1' not in x['name']
        copy = list(filter(criteria, copy))
        gvar_img.set(copy)
        self.assertEqual(gvar_img.get(), copy)

    def test_request_get(self):
        gvar_img = self.noaa.request.gvar_img
        for order in gvar_img.get():
            for key in ['status', 'size', 'format', 'last_activity', 'id', 'channel', 'files', 'datetime', 'old']:
                self.assertIn(key, list(order.keys()))

    def assertEqualsRequests(self, obtained, original):
        avoid = ['coverage', 'end', 'start',
                 'satellite', 'schedule', 'id', 'north',
                 'south', 'east', 'west']
        asymetric = lambda x: x not in avoid
        if not obtained['files']['http']:
            avoid.extend(['format', 'channel'])
        for k in filter(asymetric, list(original.keys())):
            self.assertIn(k, list(obtained.keys()))
            if isinstance(original[k], float):
                self.assertEqual(int(obtained[k]), int(original[k]))
            elif isinstance(original[k], datetime):
                self.assertEqual(obtained[k].toordinal(),
                                 original[k].toordinal())
            else:
                self.assertEqual(obtained[k], original[k])

    def test_request_set_new(self):
        time.sleep(40)
        gvar_img = self.noaa.request.gvar_img
        data = gvar_img.get(async=True)
        data.extend(self.req_data)
        copy = gvar_img.set(data, async=True)
        self.assertEqual(len(copy), len(data))
        [self.assertEqualsRequests(copy[i], data[i]) for i in range(len(data))]
        time.sleep(40)

    def test_request_set_without_auto_get(self):
        time.sleep(40)
        gvar_img = self.noaa.request.gvar_img
        data = gvar_img.get(async=True)
        data.extend(self.req_data)
        large_start = datetime.now()
        copy = gvar_img.set(data, async=True, auto_get=True)
        large_end = datetime.now()
        start = datetime.now()
        copy = gvar_img.set(data, async=True, auto_get=False)
        end = datetime.now()
        diff = lambda end, start: (end - start).total_seconds()
        self.assertGreaterEqual(diff(large_end, large_start), diff(end, start))
        time.sleep(40)


if __name__ == '__main__':
    unittest.main()
