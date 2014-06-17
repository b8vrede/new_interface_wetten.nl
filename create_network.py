import re
from networkx import *
import argparse
import urllib

def build_network():
    global CaseG
    global LegislationG
    
    # Read case law edge file
    CaseG = nx.read_weighted_edgelist("caselaw.edges") # , create_using=nx.DiGraph() <-- Used for creating directional graphs
        
    # Read legislation edge file
    LegislationG = nx.read_edgelist("laws.edges") # , create_using=nx.DiGraph() <-- Used for creating directional graphs

def contains_law(G, center, n = 1):
    counter = 0
    for node in G.nodes():
        m = BWB_regexp.search(node)
        if m is not None and node != center:
            counter += 1
            if counter >= n:
                return True
    return False
    
def get_work_level(node_expression_level):
    m = BWBarticle_regexp.search(node_expression_level)
    if m is not None:
        return "<http://doc.metalex.eu/id/"+m.group(1)+"/artikel/"+m.group(2)+">"
    else:
        m = BWB_regexp.search(node_expression_level)
        if m is not None:
            return "<http://doc.metalex.eu/id/"+m.group(1)+">"
    return None
                    
def get_local_network(current_node_expression):
    if get_work_level(current_node_expression) is not None:
        current_node = get_work_level(current_node_expression)
    else:
        print "FAILED to get work level from {}!".format(current_node_expression)
        return 0
    
        
    current_found = False 
    if current_node in CaseG.nodes():
        current_found = True
        for r in range(1,20,1):
            local_graph = ego_graph(CaseG, current_node, radius = (r/float(10)), center = True, undirected = True, distance='weight')
            print "local ({}) -> CASE LAW\t\tNodes: {} Edges: {}".format((r/float(10)), len(local_graph.nodes()), len(local_graph.edges()))
            if contains_law(local_graph, current_node, n=5):
                break;
        
        print "local -> CASE LAW\t\tNodes: {} Edges: {}".format(len(local_graph.nodes()), len(local_graph.edges()))
    
    if "<"+current_node_expression+">" in LegislationG.nodes():
        local_leg = ego_graph(LegislationG, "<"+current_node_expression+">", radius = 1, center = True, undirected = True)
        
        # Rename the nodes to the work level
        renamedict = {}
        for node_expression_level in local_leg.nodes():
            if get_work_level(node_expression_level) is not None:
                renamedict[node_expression_level] = get_work_level(node_expression_level)
            
        local_leg = nx.relabel_nodes(local_leg,renamedict, copy=False)
        print "local -> LEGISLATION\t\tNodes: {} Edges: {}".format(len(local_leg.nodes()), len(local_leg.edges()))    
        if current_found:           
            # Add this network to the case law network
            local_graph.add_nodes_from(local_leg.nodes(data=True))
            local_graph.add_edges_from(local_leg.edges(data=True), weight=0.1)
        else: 
            local_graph = local_leg
        current_found = True
        
    if not current_found:
        print current_node
        return None
    elif current_found:
        return local_graph

def select_highest(central_list, current_node, top = 5):
    m = law_rewrite.search(current_node)
    if m is not None:
        article = m.group(4)
        bwb = m.group(3)
    else:
        return {}
    top_lists = {}
    top_case = {}
    top_law = {}
    if len(central_list) > 0:
        sorted_central_list = sorted(central_list, reverse=True, key=central_list.get)
        for node in sorted_central_list:
            if law_regex.match(node.encode('ascii','ignore')) is not None and node is not current_node and len(top_law) < top:
                m = law_rewrite.search(node)
                if m is not None:
                    if (article != m.group(4) and bwb == m.group(3)) or bwb != m.group(3):
                        if m.group(4) is not None:
                            clean_article = ", Artikel "+urllib.unquote(m.group(4))
                        else:
                            clean_article = ""
                        top_law[len(top_law)] = {"label" : m.group(3)+clean_article, "link": m.group(2), "article":m.group(4), "bwb" : m.group(3), "node": node}
                        print "L{}. Best match  {}\n\tScore: {:.15f}".format(len(top_law), node, central_list[node])
            if case_law_regex.match(node.encode('ascii','ignore')) is not None and node is not current_node and len(top_case) < top:
                m = case_law_rewrite.search(node)
                if m is not None:
                    top_case[len(top_case)] = {"label" : m.group(2), "link": "/"+m.group(2), "node": node}
                print "C{}. Best match  {}\n\tScore: {:.15f}".format(len(top_case), node, central_list[node])
    
    top_lists["case"] = top_case
    top_lists["law"] = top_law
    return top_lists

def get_betweenness_centrality(local_graph, current_node, endpoints=True):
    central_list = betweenness_centrality(local_graph, weight='weight', endpoints=endpoints)
    print current_node
    top_lists = select_highest(central_list, current_node)    
    return top_lists
    
build_network()

# Compile the regex for finding out which type of document the node is
case_law_regex = re.compile('<http://rechtspraak.nl')
law_regex = re.compile('<http://doc.metalex.eu')
case_law_rewrite = re.compile("<(.*(ECLI:[^:]+:[^:]+:\d{4}:[^/\"\'>]+).*)>")
law_rewrite = re.compile("<?(.*?(/(BWB[VR]\d{7}).*?(?:/artikel/([^/>]+).*?)?))(?:>$|$)")
# Compile the regex for extraction of the work level node from the expression level node
BWBarticle_regexp = re.compile("(BWB[VR]\d{7}).*?/artikel/([^/]+)")
BWB_regexp = re.compile("(BWB[VR]\d{7})")
print "CASE LAW\t\tNodes: {} Edges: {}".format(len(CaseG.nodes()), len(CaseG.edges()))
print "LEGISLATION\t\tNodes: {} Edges: {}".format(len(LegislationG.nodes()), len(LegislationG.edges()))    