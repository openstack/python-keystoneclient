# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

import uuid


from keystoneclient.tests.unit.auth import utils


class TestOtherLoading(utils.TestCase):

    def test_loading_getter(self):

        called_opts = []

        vals = {'a-int': 44,
                'a-bool': False,
                'a-float': 99.99,
                'a-str': 'value'}

        val = uuid.uuid4().hex

        def _getter(opt):
            called_opts.append(opt.name)
            # return str because oslo.config should convert them back
            return str(vals[opt.name])

        p = utils.MockPlugin.load_from_options_getter(_getter, other=val)

        self.assertEqual(set(vals), set(called_opts))

        for k, v in vals.items():
            # replace - to _ because it's the dest used to create kwargs
            self.assertEqual(v, p[k.replace('-', '_')])

        # check that additional kwargs get passed through
        self.assertEqual(val, p['other'])
