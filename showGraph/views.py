from django.shortcuts import render
from django import template
from django.http import HttpResponse
from django.shortcuts import redirect
import create_network as citeNetworks
from networkx import *
import re
import urllib

def showGraph(request):
    currentNode = None
    if request.GET.__contains__("expression"):
        currentNode = request.GET["expression"]
        law_regex = re.compile('(BWB[VR]\d{7}).*?(\d{4}-\d{2}-\d{2})')
        m = law_regex.search(currentNode)
        currentNode = "http://doc.metalex.eu/id/"+m.group(1)
        if request.GET.__contains__("article") and request.GET["article"]:
            currentNode += "/artikel/" + request.GET["article"]
        currentNodeWithoutDate = currentNode
        currentNode += "/"+m.group(2)
    if currentNode is not None:
        localGraph = citeNetworks.get_local_network(currentNode)
        if localGraph is not None:
            layout = networkx.spring_layout(localGraph, scale=10.0)
            positionsHtml = ""
            for node in layout.keys():
                positionsHtml += " '"+node+"': { x: "+str(layout[node][0]*100)+", y: "+str(layout[node][1]*100)+" },"
            nodeHtml = ""
            for node in localGraph.nodes():
                if node == "<"+currentNodeWithoutDate+">":
                    type = "current"
                    label = "Huidige positie"
                    link = request.META['HTTP_REFERER']
                elif re.search('(BWB[VR]\d{7})', node) is None:
                    type = "case"
                    label = node
                    m = citeNetworks.case_law_rewrite.search(node)
                    if m is not None:
                        label = m.group(2)
                        link = "/"+m.group(2)
                else:
                    type = "law"
                    label = node
                    m = citeNetworks.law_rewrite.search(node)
                    if m.group(4) is not None:
                        label = m.group(3)+", Artikel "+urllib.unquote(m.group(4))
                        link = "/"+m.group(3)+"/artikel/"+m.group(4)
                    else:
                        label = m.group(3)
                        link = "/"+m.group(3)
                if nodeHtml:
                    nodeHtml += ",{ data: { id: '"+node+"', type:'"+type+"', label:'"+label+"', href:'"+link+"'} }"
                else:
                    nodeHtml = "{ data: { id: '"+node+"', type:'"+type+"', label:'"+label+"', href:'"+link+"'} }"
            edgeHtml = ""        
            for edge in localGraph.edges(data=True):
                if len(edge[2]) > 0:
                    weight = 1 / edge[2]["weight"]
                else:
                    weight = 1
                if edgeHtml:
                    edgeHtml += ",{ data: { id: '"+edge[0]+"-"+edge[1]+"', weight: "+str(weight)+", source: '"+edge[0]+"', target: '"+edge[1]+"' } }"
                else:
                    edgeHtml = "{ data: { id: '"+edge[0]+"-"+edge[1]+"', weight: "+str(weight)+", source: '"+edge[0]+"', target: '"+edge[1]+"' } }"
                    
            context = {
               'returnURL': request.META['HTTP_REFERER'],
               'edgeHtml': edgeHtml,
               'nodeHtml': nodeHtml,
               'positionsHtml': positionsHtml,
               }
            return render(request, 'showGraph/frame.html', context)
    context = {
               'returnURL': request.META['HTTP_REFERER'],
               'edgeHtml': "",
               'nodeHtml': "{ data: { id: 'current', type:'current', label:'Huidige positie', href:'"+request.META['HTTP_REFERER']+"'} }",
               'positionsHtml': "'current': {x:0, y:0}",
               }
    return render(request, 'showGraph/frame.html', context)