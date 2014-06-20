import re
from networkx import *
import urllib
# An example of how the related nodes can be calculated
def get_betweenness_centrality(local_graph, current_node, endpoints=True):

    # Use weighted "betweenness_centrality" to calculate for each node it's centrality
    central_list = betweenness_centrality(local_graph, weight='weight', endpoints=endpoints)
    
    # Generates a top N to return to the interface 
    return select_highest(central_list, current_node, top = 5)    
 
 
# Builds the global network and stores it for use later on
def build_network():
    # define variables as global
    global CaseG
    global LegislationG
    
    # Read case law edge file
    CaseG = nx.read_weighted_edgelist("/var/www/wettenbart/caselaw.edges") # , create_using=nx.DiGraph() <-- Used for creating directional graphs
        
    # Read legislation edge file
    LegislationG = nx.read_edgelist("/var/www/wettenbart/laws.edges") # , create_using=nx.DiGraph() <-- Used for creating directional graphs

    
# Checks whether a graph contains at N nodes with a BWB thus a law 
def contains_law(G, center, n = 1):
    
    # Init counter
    counter = 0
    
    # check each node
    for node in G.nodes():
        
        # match the node name with a BWB regex
        m = BWB_regexp.search(node)
        
        # if a BWB is found and the node is not the center node
        if m is not None and node != center:
        
            # increase counter
            counter += 1
            
            # when enough laws are found return true
            if counter >= n:
                return True
                
    # if not enough nodes are laws return False
    return False

    
# Extracts work level from a expression level law    
def get_work_level(node_expression_level):
    
    # Check whether the expression contains both a law and a article
    m = BWBarticle_regexp.search(node_expression_level)
    
    # If is matches return the new work level url
    if m is not None:
        return "<http://doc.metalex.eu/id/"+m.group(1)+"/artikel/"+m.group(2)+">"
    
    # If is doesn't match use the BWB extractor
    else:
        
        # Extract the BWB from the expression level
        m = BWB_regexp.search(node_expression_level)
        
        # If it matches return the new work level
        if m is not None:
            return "<http://doc.metalex.eu/id/"+m.group(1)+">"
            
    # If nothing matched return None to indicate that no work level could be extracted
    return None

    
# Return the local Graph for an expression level law    
def get_local_network(current_node_expression):
    # Try to extract a work level law from the expression level law
    if get_work_level(current_node_expression) is not None:
    
        # Store the work level
        current_node = get_work_level(current_node_expression)
    else:
        # Return 0 and print a error message to the console as the node doesn't contain a BWB
        print "FAILED to get work level from {}!".format(current_node_expression)
        return 0
        
    # Init a boolean to indicate whether a graph was generated at any point    
    current_found = False 
    
    # If the current node is in the case law graph, generate a graph for it
    if current_node in CaseG.nodes():
        
        # Can generate a network of at least 1 node (the current node)
        current_found = True
        
        # Look for a local graph at increasing distance from the center, short distance mean that a ref is more common
        rangeArray = [1,3,7,10,15,20]
        for r in rangeArray:
            # Get a local graph with distance r/10 (so r=1 means radius 0.1 or 10 references)
            local_graph = ego_graph(CaseG, current_node, radius = (r/float(10)), center = True, undirected = True, distance='weight')
            
            # Print the graph stats for debugging purposes
            #print "local ({}) -> CASE LAW\t\tNodes: {} Edges: {}".format((r/float(10)), len(local_graph.nodes()), len(local_graph.edges()))
            
            # If the current graph contains at least N law nodes break the loop and thus use the current graph
            if contains_law(local_graph, current_node, n=5):
                break;
            
            # If the loop hasn't be broken the next larger radius is tried (until we are at the max range)
        
        # Print the chosen local graph stats
        # print "local -> CASE LAW\t\tNodes: {} Edges: {}".format(len(local_graph.nodes()), len(local_graph.edges()))
    
    # If the expression level node is in the legislation graph, generate a graph
    if "<"+current_node_expression+">" in LegislationG.nodes():
        
        # Get a local legislation graph from the global graph
        # As the legislation refs are not weighted always use an integer radius lower won't work
        local_leg = ego_graph(LegislationG, "<"+current_node_expression+">", radius = 1, center = True, undirected = True)
        
        # Rename the nodes to the work level (or format them to our work level format)
        for node_expression_level in local_leg.nodes():
            if get_work_level(node_expression_level) is not None:
                renamedict[node_expression_level] = get_work_level(node_expression_level)
        
        # Order the relabeling of the nodes    
        local_leg = nx.relabel_nodes(local_leg,renamedict, copy=False)
        
        # Print the local graph stats
        # print "local -> LEGISLATION\t\tNodes: {} Edges: {}".format(len(local_leg.nodes()), len(local_leg.edges()))    
        
        # If there is already a case law graph merge them
        if current_found:           
            # Add this graph to the case law graph
            local_graph.add_nodes_from(local_leg.nodes(data=True))
            local_graph.add_edges_from(local_leg.edges(data=True), weight=0.1)
        else:
            # Or just use the legislation graph
            local_graph = local_leg
            
        # Indicate we have generated a graph
        current_found = True
    
    # If we generated a graph return it or return None and print a message to the console
    if not current_found:
        # print current_node
        return None
    elif current_found:
        return local_graph

        
# Generates the top N list for the interface        
def select_highest(central_list, current_node, top = 5):
    # Extract the BWB and article from the current_node
    m = law_rewrite.search(current_node)
    
    # When a group matched get the info (an empty matched group = None)
    if m is not None:
        article = m.group(4)
        bwb = m.group(3)
    else:
        return {}
    
    # init the dictonaries
    top_lists = {}
    top_case = {}
    top_law = {}
    
    # If there are elements in the provided list do:
    if len(central_list) > 0:
        
        # Sort the element highest first
        sorted_central_list = sorted(central_list, reverse=True, key=central_list.get)
        
        # Loop through the list 
        for node in sorted_central_list:
        
            # If it is a law node, not the current node and we still need a law for our top N
            if law_regex.match(node.encode('ascii','ignore')) is not None and node is not current_node and len(top_law) < top:
                
                # Extract BWB (and Article) for use in the label
                m = law_rewrite.search(node)
                if m is not None:
                
                    # Extra check if we don't have the current node again
                    if (article != m.group(4) and bwb == m.group(3)) or bwb != m.group(3):
                        
                        # Prepare article label suffix
                        if m.group(4) is not None:
                            clean_article = ", Artikel "+urllib.unquote(m.group(4))
                        else:
                            clean_article = ""
                            
                        # Add the law to the top list at it's position 
                        # As lists in python start at 0 the current list length is always empty this way
                        top_law[len(top_law)] = {"label" : m.group(3)+clean_article, "link": m.group(2), "article":m.group(4), "bwb" : m.group(3), "node": node}
                        
                        # Print to console for debugging
                        # print "L{}. Best match  {}\n\tScore: {:.15f}".format(len(top_law), node, central_list[node])
                        
            # If it is a case law node, not the current node and we still need a case law for our top N
            if case_law_regex.match(node.encode('ascii','ignore')) is not None and node is not current_node and len(top_case) < top:
            
                # Extract the ECLI from the node for use in the label
                m = case_law_rewrite.search(node)
                
                # If there is a ECLI add it to the top N list
                if m is not None:
                    
                    # Add the case law node to the top list at it's position 
                    # As lists in python start at 0 the current list length is always empty this way
                    top_case[len(top_case)] = {"label" : m.group(2), "link": "/"+m.group(2), "node": node}
                
                # Print to console for debugging
                # print "C{}. Best match  {}\n\tScore: {:.15f}".format(len(top_case), node, central_list[node])
    
    # Add the 2 dictionaries to a parent dict
    top_lists["case"] = top_case
    top_lists["law"] = top_law
    
    # return the parent dict
    return top_lists


# Causes the network to be build the first time the module is imported    
build_network()

# Compile the regex for finding out which type of document the node is
case_law_regex = re.compile('<http://rechtspraak.nl')
law_regex = re.compile('<http://doc.metalex.eu')
case_law_rewrite = re.compile("<(.*(ECLI:[^:]+:[^:]+:\d{4}:[^/\"\'>]+).*)>")
law_rewrite = re.compile("<?(.*?(/(BWB[VR]\d{7})[^>]*?(?:/artikel/([^/>]+)[^>]*?)?))")

# Compile the regex for extraction of the work level node from the expression level node
BWBarticle_regexp = re.compile("(BWB[VR]\d{7}).*?/artikel/([^/]+)")
BWB_regexp = re.compile("(BWB[VR]\d{7})")

# Print the global graph stats
# print "CASE LAW\t\tNodes: {} Edges: {}".format(len(CaseG.nodes()), len(CaseG.edges()))
# print "LEGISLATION\t\tNodes: {} Edges: {}".format(len(LegislationG.nodes()), len(LegislationG.edges()))
print "Edges loaded"    