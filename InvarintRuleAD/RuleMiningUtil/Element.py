'''
Created on 23 Aug 2017

@author: cf1510
'''

class TreeNode(object):
    '''
    classdocs
    '''


    def __init__(self, item, count, parent_link, child_links, node_link):
        '''
        Constructor
        '''
        self.item = item
        self.count = count
        self.parent_link = parent_link
        self.child_links = child_links
        self.node_link = node_link
        
    
    def updateCount(self, num):
        self.count += num
    
    def __str__(self, level=0):
        ret = "\t"*level+str(self.item)+':'+str(self.count)+"\n"
        for child in self.child_links:
            ret += child.__str__(level+1)
        return ret


class TableEntry(object):
    '''
    classdocs
    '''


    def __init__(self, item, min_freq, node_link):
        '''
        Constructor
        '''
        self.item = item
        self.min_freq = min_freq
        self.node_link = node_link