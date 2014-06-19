from django.shortcuts import render
from django.http import HttpResponse
import json
import urllib2
import networkx
import re
import create_network as citeNetworks


def default(request):
    return redirect("/")
    
def load_law_text(request):
    metalexData = urllib2.urlopen(request.GET['doc'])
    metalexXML = metalexData.read()
    return HttpResponse(metalexXML)
    
def article_history(request):
    output = "Historie:<BR><BR>"
    mapping = [('januari', '01'), ('februari', '02'), ('maart', '03'), ('april', '04'), ('mei', '05'), ('juni', '06'), ('juli', '07'), ('augustus', '08'), ('september', '09'), ('oktober', '10'), ('november', '11'), ('december', '12') ]
    if request.REQUEST.__contains__("expression"):
        formatURL = request.REQUEST['expression'].replace("metalex.eu/id/","metalex.eu/doc/")+"/data.xml"
        formatURL = re.sub("\d{4}-\d{2}-\d{2}", "{}", formatURL)
        versions = request.REQUEST['versions'].split(", ")
        for version in versions:
            for k, v in mapping:
                version = version.replace(k, v)
            m = re.search("(\d{1,2}) (\d{2}) (\d{4})", version)
            correctVersion = m.group(3)+"-"+m.group(2)+"-"
            if len(m.group(1)) == 1:
                correctVersion += "0"
            correctVersion += m.group(1)
            url = formatURL.format(correctVersion)
            metalexData = urllib2.urlopen(url)
            versionXML = metalexData.read()
            output += versionXML + "<BR><BR>"
        return HttpResponse(output)
        
def related_law(request):
    currentNode = None
    if request.GET.__contains__("expression"):
        currentNode = request.GET["expression"]
        case_law_regex = re.compile('(BWB[VR]\d{7}).*?(\d{4}-\d{2}-\d{2})')
        m = case_law_regex.search(currentNode)
        currentNode = "http://doc.metalex.eu/id/"+m.group(1)
        if request.GET.__contains__("article") and request.GET["article"]:
            currentNode += "/artikel/" + request.GET["article"]
        currentNode += "/"+m.group(2)
        
    if currentNode is not None:
        localGraph = citeNetworks.get_local_network(currentNode)
        if localGraph is not None:
            TopLists = citeNetworks.get_betweenness_centrality(localGraph, currentNode)
            return HttpResponse(json.dumps(TopLists), content_type="application/json")
        messageL = '<span class="glyphicon glyphicon-exclamation-sign"></span> Geen relevante wetgeving gevonden.'
        messageJ = '<span class="glyphicon glyphicon-exclamation-sign"></span> Geen relevante jurisprudentie gevonden.'
    else:
        messageL = '<span class="glyphicon glyphicon-fire"></span> Geen relevante wetgeving gevonden.'
        messageJ = '<span class="glyphicon glyphicon-fire"></span> Geen relevante jurisprudentie gevonden.'
        
    response = {}
    response_data = []
    response_data_entry = {}
    response_data_entry['label'] = messageL
    response_data_entry['link'] = '#error'
    response_data.append(response_data_entry)
    response["law"] = response_data
    response_data = []
    response_data_entry = {}
    response_data_entry['label'] = messageJ
    response_data_entry['link'] = '#error'
    response_data.append(response_data_entry)
    response["case"] = response_data
    return HttpResponse(json.dumps(response), content_type="application/json")
