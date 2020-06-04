# coding: utf-8
from clocwalk.libs.core.common import recursive_search_files
import os
import re


__product__ = 'Java'
__version__ = '1.0'

class Tree:
	def __init__(self, root):
		self.root = root

	def parse(self,node):
		result = {}
		if node.children:
			for child in node.children:
				if node.handled_data in result:
					result[node.handled_data].append(self.parse(child))
				else:
					result[node.handled_data] = [self.parse(child)]
		else:
			return {node.handled_data:[]}
		return result

	def toList(self):
		return self.root.build_list_with_child()

	def toJson(self,node):
		return json.dumps(self.parse(node))


class Node:
	def __init__(self, data):
		self.parent = None
		self.level = 0
		self.data = data
		self.handled_data = re.match('^[\\\ \+\-\|]*(\w+.*)',data).group(1)
		self.parent_tree = None
		self.children = []
		self.vendor, self.product, self.version, self.tag = self.parse_detail()


	def getData(self):
		return self.data
	def getChildren(self):
		return self.children
	def getLevel(self):
		return self.level
	def getParent(self):
		return self.parent

	def joint_parent_tree(self):
		result = self.handled_data
		_parent = self.parent
		# print(_parent.handled_data)
		while(_parent):
			result += '->' + _parent.handled_data 
			_parent = _parent.parent
		return result
			
	def parse_detail(self):
		product_info = self.handled_data.split(':')
		vendor, product, version, tag = product_info[0], product_info[1], product_info[-2], product_info[-1]
		return vendor, product, version, tag

	def build_list_with_child(self):
		result = []
		for child in self.children:
			result.append(child)
			if child.children:
				result += child.build_list_with_child()
		return result
	def addChild(self, node):
		if(self.__class__ == node.__class__):
			node.parent = self
			node.level = self.level + 1
			node.parent_tree = node.joint_parent_tree()
			self.children.append(node)

class TreeBuilder:
	def __init__(self, data):
		self.data = data
		self.tree = None

	def computeLevel(self, rawNode):
		level = 1
		for c in rawNode:
			if(c == '|'):
				level = level + 1
			elif(c == '+' or c == '\\'):
				break
		# fix some special issue	
		space = re.search(r'\|\s+',rawNode)
		if space:
			space_count = len(space.group(0))
			# print(space_count)
			level = level + (space_count - 3) / 3
		return level

	def build(self):
		with open(self.data) as f:
			mvn_result = f.read()
			nodeList = mvn_result.split('\n')
		parent = Node(nodeList[0])
		
		self.tree = Tree(parent)
		for rawNode in nodeList[1:]:
			if not rawNode:
				continue
			level = self.computeLevel(rawNode)
			child = Node(rawNode)

			while(parent.getLevel() >= level):
				parent = parent.getParent()

			parent.addChild(child)
			parent = child
		
		return self.tree




# 依赖递归寻找父依赖树
# def parse_parent(parent, tree):
#     result = ''
#     if parent and parent in tree.keys():
#         next_parent = tree[parent]
#         ret = parse_parent(next_parent, tree)
#         return ret + '->' + parent
#     else:
#         return parent




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
        os.system('mvn dependency:tree -f ' + try_main_pom + ' -DoutputFile=result > /dev/null')
    for pom_file in pom_file_list:
        pom_path = pom_file.rstrip('pom.xml').replace(';','')
        if not os.path.exists(pom_path + 'result'):
            continue
        # with open() as dot_file:
        tree = TreeBuilder(pom_path + 'result').build()
        for i in tree.toList():
        # print(i.vendor, i.product, i.version, i.tag)
            if i.tag != 'test':
                result.append({
                    'vendor':i.vendor,
                    'product':i.product,
                    'version':i.version,
                    'new_version':'',
                    'cve':{},
                    'parent_file':i.parent_tree,
                    'origin_file':'/'.join(pom_file.split('/')[3:])
                })

    return result
