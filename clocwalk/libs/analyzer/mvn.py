# coding: utf-8
from clocwalk.libs.core.common import recursive_search_files
import os
import re

# 依赖递归寻找父依赖树
def parse_parent(parent, tree):
    result = ''
    if parent and parent in tree.keys():
        next_parent = tree[parent]
        ret = parse_parent(next_parent, tree)
        return ret + '->' + parent
    else:
        return parent




def start(**kwargs):
    """
    :param kwargs:
    :return:
    """
    code_dir = kwargs.get('code_dir', '')
    pom_file_list = recursive_search_files(code_dir, '*/pom.xml')
    result = []
    tree = {}
    for try_main_pom in pom_file_list:
        os.system('mvn dependency:tree -f ' + try_main_pom + ' -DoutputType=dot -DoutputFile=result > /dev/null')
    for pom_file in pom_file_list:
        pom_path = pom_file.rstrip('pom.xml').replace(';','')
        if not os.path.exists(pom_path + 'result'):
            continue
        with open(pom_path + 'result') as dot_file:
            lines = dot_file.readlines()[1:-1]
            for line in lines:
                ret = re.match(r".*\"(\S+)\" -> \"(\S+)\" ;",line)
                if not ret:
                    continue
                parent, _self = ret.group(1),ret.group(2)
                tree[_self] = parent
                parent_file = parse_parent(parent, tree)
                # print(_self, '|||',parent_file)
                product_info = _self.split(':')
                vendor, product, version, tag = product_info[0], product_info[1], product_info[-2], product_info[-1]
                if tag != 'test':
                    result.append({
                        'vendor':vendor,
                        'product':product,
                        'version':version,
                        'new_version':'',
                        'cve':{},
                        'parent_file':parent_file,
                        'origin_file':'/'.join(pom_file.split('/')[3:])
                    })

    return result
