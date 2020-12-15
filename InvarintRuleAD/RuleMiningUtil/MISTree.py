'''
Created on 16 Aug 2017

@author: cf1510
'''
from .Element import TreeNode, TableEntry

# the structure of a node (item_name, item_count, child-links, node-link)


def count_items(dataset):
    "count items in the dataset."
    item_count_dict = {}
    for transaction in dataset:
        for item in transaction:
            if item in item_count_dict:
                item_count_dict[item] += 1
            else:
                item_count_dict[item] = 1

    return item_count_dict

def insertTree(item_mis_tuples, root, MIN_freq_item_header_table):
    "insert_tree."
    node = root
    for item_mis_tuple in item_mis_tuples:
        item = item_mis_tuple[0]
        match = False
        for child in node.child_links:
            if item == child.item:
                match = True
                child.updateCount(1)
                node = child
                break
        if match == False:
            new_node = TreeNode(item, 1, node, [], None)
            node.child_links.append(new_node)
            if item not in MIN_freq_item_header_table:
                MIN_freq_item_header_table[item] = TableEntry(item, item_mis_tuple[1], new_node)
            else:
                nodelink = MIN_freq_item_header_table[item].node_link
                while nodelink.node_link != None:
                    nodelink = nodelink.node_link
                nodelink.node_link = new_node
            node = new_node

def printTree(root):
    print(' ')
    print('print tree')
    print(root)

def printTable(MIN_freq_item_header_table, converted=False):
    print( ' ' )
    print( 'print MIN_freq_item_header_table' )
    if converted == False:
        for entry in MIN_freq_item_header_table:
            str_tempt = str(entry) + ':' + str(MIN_freq_item_header_table[entry].min_freq)
            nodelink = MIN_freq_item_header_table[entry].node_link
            while nodelink != None:
                str_tempt += '->' + str(nodelink.item)
                nodelink = nodelink.node_link
            print(str_tempt)
    else:
        for entry in MIN_freq_item_header_table:
            str_tempt = str(entry.item) + ':' + str(entry.min_freq)
            nodelink = entry.node_link
            while nodelink != None:
                str_tempt += '->' + str(nodelink.item)
                nodelink = nodelink.node_link
            print(str_tempt)

def genMIS_tree(dataset, item_count_dict, min_sup):
    root = TreeNode(0,0,None,[],None)
    MIN_freq_item_header_table = {}
    
    "Construct tree"
    for transaction in dataset:
#         print(list(transaction))
        item_mis_tuples = []
        for item in transaction:
#             print(item)
            im_tuple = (item, min_sup[item])
            item_mis_tuples.append(im_tuple)
#         print(item_mis_tuples)
        item_mis_tuples.sort(key=lambda tup: (tup[1],tup[0]),reverse=True)
        insertTree(item_mis_tuples, root, MIN_freq_item_header_table)
#     printTree(root)
#     print(MIN_freq_item_header_table)
#     printTable(MIN_freq_item_header_table)    
    
    "Prune tree"
    min_value = 9999999
    for item in min_sup:
        if min_sup[item] < min_value:
            min_value = min_sup[item]
    
    pruning_items = []
    for item in item_count_dict:
        if item_count_dict[item] < min_value:
            pruning_items.append(item)
    
    for item in pruning_items:
        node = MIN_freq_item_header_table[item].node_link
        while node != None:
            node.parent_link.child_links.remove(node)
            if len(node.child_links) > 0:    
                node.parent_link.child_links.extend(node.child_links)
                for child in node.child_links:
                    child.parent_link = node.parent_link
            node = node.node_link
        del MIN_freq_item_header_table[item]
    
#     printTree(root)
#     printTable(MIN_freq_item_header_table)
#     print(MIN_freq_item_header_table)
    MIN_freq_item_header_dict = MIN_freq_item_header_table
    
    MIN_freq_item_header_table = list(MIN_freq_item_header_table.values())
    MIN_freq_item_header_table.sort(key=lambda x: (x.min_freq, x.item))
#     printTable(MIN_freq_item_header_table, converted = True)
    
    return root, MIN_freq_item_header_table, min_value, MIN_freq_item_header_dict
    
#     print "Merge trees"
#     for entry in MIN_freq_item_header_table:
#         node = MIN_freq_item_header_table[entry].node_link
#         while node.node_link != None:
#             if node.parent_link == node.node_link.parent_link:
#                 node.parent_link.child_links.remove(node.node_link)
#                 if n

def insert_prefix_path(prefix_path, root, MIN_freq_item_header_table, min_sup):
    node = root
    for item_count_tuple in prefix_path:
        item = item_count_tuple[0]
        count = item_count_tuple[1]
        match = False
        for child in node.child_links:
            if item == child.item:
                match = True
                child.updateCount(count)
                node = child
                break
        if match == False:
            new_node = TreeNode(item, count, node, [], None)
            node.child_links.append(new_node)
            if item not in MIN_freq_item_header_table:
                MIN_freq_item_header_table[item] = TableEntry(item, min_sup[item], new_node)
            else:
                nodelink = MIN_freq_item_header_table[item].node_link
                while nodelink.node_link != None:
                    nodelink = nodelink.node_link
                nodelink.node_link = new_node
            node = new_node


def genConditional_MIS_tree(conditional_pattern_base, base_pattern, MIS, min_sup, pattern_count_dict):
    root = TreeNode(0,0,None,[],None)
    MIN_freq_item_header_table = {}
    conditional_frequent_patterns = []
    
#     print "Construct conditional tree for base pattern " + str(base_pattern)
    for prefix_path in conditional_pattern_base:
        insert_prefix_path(prefix_path, root, MIN_freq_item_header_table, min_sup)
    
    pruning_items = []
    for item in MIN_freq_item_header_table:
        count = 0
        node = MIN_freq_item_header_table[item].node_link
        while node != None:
            count += node.count
            node = node.node_link
        if count < MIS:
            pruning_items.append(item)
            new_pattern = list(base_pattern)
            new_pattern.append(item)
            pattern_count_dict[frozenset(new_pattern)] = count
#             print new_pattern
#             print count
        else:
            new_pattern = list(base_pattern)
            new_pattern.append(item)
#             print new_pattern
            conditional_frequent_patterns.append(new_pattern)
            pattern_count_dict[frozenset(new_pattern)] = count
#             print new_pattern
#             print count
    
    for item in pruning_items:
        node = MIN_freq_item_header_table[item].node_link
        while node != None:
            node.parent_link.child_links.remove(node)
            if len(node.child_links) > 0:    
                node.parent_link.child_links.extend(node.child_links)
                for child in node.child_links:
                    child.parent_link = node.parent_link
            node = node.node_link
        del MIN_freq_item_header_table[item]
    
    if len(MIN_freq_item_header_table) > 0:
        MIN_freq_item_header_table = list(MIN_freq_item_header_table.values())
        MIN_freq_item_header_table.sort(key=lambda x: (x.min_freq, x.item))
    
    return root, MIN_freq_item_header_table, conditional_frequent_patterns

def CP_growth(tree, header_table, base_pattern, MIS, min_sup, freq_patterns, pattern_count_dict, max_k):
    for entry in header_table:
        node = entry.node_link
        conditional_pattern_base = []
        while node != None:
            prefix_tree = []
            parent = node.parent_link
            while parent.parent_link != None:
                prefix_tree.append( (parent.item, node.count) )
                parent = parent.parent_link
                
            prefix_tree.reverse()
            conditional_pattern_base.append(prefix_tree)
            node = node.node_link
        
#         print conditional_pattern_base
        new_base_pattern = list(base_pattern)
        new_base_pattern.append(entry.item)
        new_tree, new_header_table, conditional_frequent_patterns = genConditional_MIS_tree(conditional_pattern_base, new_base_pattern, MIS,  min_sup, pattern_count_dict)
#         print 'print tree for base pattern ' + str(new_base_pattern)
#         printTree(new_tree)

        freq_patterns.extend(conditional_frequent_patterns)
        
        if len(new_header_table) > 0 and len(new_base_pattern) < max_k:
            CP_growth(new_tree, new_header_table, new_base_pattern, MIS,min_sup,freq_patterns, pattern_count_dict, max_k)
         
def CFP_growth(root, MIN_freq_item_header_table, min_sup, max_k):
    freq_patterns = []
    pattern_count_dict = {}
    for entry in MIN_freq_item_header_table:
        node = entry.node_link
        conditional_pattern_base = []
        while node != None:
            prefix_tree = []
            parent = node.parent_link
            while parent.parent_link != None:
                prefix_tree.append( (parent.item, node.count) )
                parent = parent.parent_link
                
            prefix_tree.reverse()
            conditional_pattern_base.append(prefix_tree)
            node = node.node_link 
        
#         print conditional_pattern_base
        tree, header_table, conditional_frequent_patterns = genConditional_MIS_tree(conditional_pattern_base, [entry.item], entry.min_freq,  min_sup, pattern_count_dict)
#         print 'print tree for base pattern ' + str(entry.item)
#         printTree(tree)
        freq_patterns.extend(conditional_frequent_patterns)
        
        if len(header_table) > 0 and max_k>1:
            CP_growth(tree, header_table, [entry.item], entry.min_freq, min_sup, freq_patterns, pattern_count_dict,max_k)
            
    return freq_patterns, pattern_count_dict 



    
