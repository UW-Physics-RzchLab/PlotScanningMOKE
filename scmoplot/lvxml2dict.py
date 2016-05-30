import xml.etree.ElementTree as ET
from os.path import join
import re

root_path = '/home/jji/Desktop/scanning_moke_test/trial0_5x5_BFO_test_sample'
parameters_path = join(root_path, 'parameters.xml')
tree = ET.parse(parameters_path)
root = tree.getroot()

to_nice_string = lambda x: re.sub(r'[\s\n]+', ' ', str(x).strip())

class Cluster:
    conversions = {
        'DBL': float,
        'U16': int,
        'U32': int,
        'U64': int,
        'I32': int,
        'I64': int,
        'Refnum': to_nice_string
    }

    def __init__(self, root):
        try:
            if root.tag != 'Cluster':
                msg = 'Cannot parse this tree unless root.tag is Cluster'
                raise ValueError(msg)
            self.root = root
        except AttributeError:
            root = ET.parse(root).getroot()
            if root.tag != 'Cluster':
                msg = 'Cannot parse this tree unless root.tag is Cluster'
                raise ValueError(msg)
            self.root = root

    def to_dict(self):
        '''Convert this cluster xml tree to a python dict.
        '''
        res = {}
        for child in self.root:
            # print(child.tag)
            for t, f in Cluster.conversions.items():
                if child.tag == t:
                    # print('\t%s' % t)
                    k = to_nice_string(next(child.iterfind('Name')).text)
                    v = f(next(child.iterfind('Val')).text)
                    # print('\t%s: %s' % (k, v))
                    res[k] = v
                    continue
        return res

    def name(self):
        return next(self.root.iterfind('Name')).text

    def num_elements(self):
        return int(next(self.root.iterfind('NumElts')).text)

c = Cluster(root)
from pprint import pprint as pp
pp(c.to_dict())

