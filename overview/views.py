# coding: utf-8

from django.shortcuts import render
from django import template
from django.http import HttpResponse
from django.shortcuts import redirect
import SparqlHelper as sparql
import CitesParser as cp
import re
import json
import urllib2
import os
import glob
import xml.etree.ElementTree as ET
from collections import defaultdict
import urllib
    
def law(request, bwb = 'BWBR0011823', article = '', expression='', ref=''):
    errors = []
    sparqlHelper = sparql.SparqlHelper()
   
    if ref:
        ref = "http://doc.metalex.eu/id/"+ref
        work = sparqlHelper.getCitedWorkForReference(ref)
        if work is not None:
            return redirect(re.sub('http://doc.metalex.eu/id/', '/', work))
        else:
            errors.append("<span class='glyphicon glyphicon-warning-sign'></span> Referentie kon niet opgelost worden! ")
            bwb = extract_BWB(ref)
            bwb_info = sparqlHelper.getLatestTitleAndExpressionForBWB(bwb)
            document = "http://doc.metalex.eu"+ bwb_info[2]
            bwb_name = bwb_info[1]
            m = re.search('/artikel/([^/]+)(?:/|$)', ref)
            if m:
                article = m.group(1)
    elif expression:
        if request.GET.__contains__("artikel"):
            article = request.GET["artikel"]
        document = "http://doc.metalex.eu/"+expression
        bwb = extract_BWB(expression)
        bwb_info = sparqlHelper.getLatestTitleAndExpressionForBWB(bwb)
        bwb_name = bwb_info[1]
    elif bwb:
        work = 'http://doc.metalex.eu/id/' + bwb
        bwb_info = sparqlHelper.getLatestTitleAndExpressionForBWB(bwb)
        document = "http://doc.metalex.eu"+ bwb_info[2]
        bwb_name = bwb_info[1]
    # else:
        # document = 'http://doc.metalex.eu/id/BWBR0011823/nl/2014-01-01/data.xml'
    # pageTitle = cp.entityDescription(document)
    
    if document:
        bwb_links = []
        for bwbDocument in bwbDocuments:
            bwb_links.append(sparqlHelper.getLatestTitleAndExpressionForBWB(bwbDocument))
        metalexData = urllib2.urlopen(document)
        metalexXML = metalexData.read()
        metalexData.close()
        
        # Get all versions for document
        work = re.sub('(?:/nl)?/\d{4}-\d{2}-\d{2}/data\.xml','', document)
        expressions = sparqlHelper.getExpressionsForWork(work)
        docExpressions = sparqlHelper.wettenDocsForIds(expressions)
        dates = sparqlHelper.datesForExpressions(docExpressions)

        # The date for the currently viewed document
        currentDateTuple = sparqlHelper.dateForExpression(document)
        
        # Make the string showing date information
        # If the current date isn't the most recent one, display message
        mostRecentDate = sparqlHelper.dateForExpression(dates['expressions'][dates['dates'][0]])[0]
        if currentDateTuple[0] < mostRecentDate:
            dateInfo = '<span class="label label-warning">Verouderde versie</span> ' + currentDateTuple[1] + ''
        else:
            dateInfo = '<span class="label label-success">Meest recente versie</span> ' + currentDateTuple[1] + ''
        
        rel_law = '<a href="#" class="list-group-item list-group-item-info">Laden...</a>'
        rel_case = '<a href="#" class="list-group-item list-group-item-info">Laden...</a>'
    
        context = {
               'errors': errors,
               'Content': metalexXML,
               'Header': bwb_name,
               'document': document,
               'rel_law': rel_law,
               'rel_case': rel_case,
               'bwb_links': bwb_links,
               'BWB': bwb,
               'BWB_name': bwb_name,
               'article': article,
               'currentDateSelection': currentDateTuple[1],
               'expressions': dates['expressions'],
               'dates': dates['dates'],
               # 'pageTitle': bwb,
               }
        return render(request, 'overview/index.html', context)
    else:
        context = {'metalexXML': "Wet onbekend!"}
        return render(request, 'overview/index.html', context)
        
def extract_BWB(string):
    return re.search("(BWB[VR]\d{7})", string).group(0)
    
def read_ecli_files():
    filelocation = os.path.normpath('ECLIs/*.xml')
    return glob.glob(filelocation)
    
def ecli(request, ecli):
    sparqlHelper = sparql.SparqlHelper()
    bwb_links = []
    for bwbDocument in bwbDocuments:
            bwb_links.append(sparqlHelper.getLatestTitleAndExpressionForBWB(bwbDocument))
    errors = []
    bwb_counter = defaultdict(int)
    files = read_ecli_files()
    ecli_file_name = os.path.normpath('ECLIs/' + re.sub(":", "-", ecli) + '.xml')
    if ecli_file_name in files:
        nameSpace = {'rdf': 'http://www.w3.org/1999/02/22-rdf-syntax-ns#', 'ecli': 'https://e-justice.europa.eu/ecli',
                 'eu': 'http://publications.europa.eu/celex/', 'dcterms': 'http://purl.org/dc/terms/',
                 'bwb': 'bwb-dl', 'cvdr': 'http://decentrale.regelgeving.overheid.nl/cvdr/',
                 'rdfs': 'http://www.w3.org/2000/01/rdf-schema#',
                 'preserve': 'http://www.rechtspraak.nl/schema/rechtspraak-1.0'}
        
        # Set XML encoding
        parser = ET.XMLParser(encoding="utf-8")

        # Parse the current XML file
        xml = ET.parse(ecli_file_name, parser=parser)
                       
        ECLItext = ET.tostring(xml.find("./preserve:uitspraak", namespaces=nameSpace), encoding='UTF-8', method='html').strip()
        
        # Get meta data
        metadata = []
        description = xml.find("./rdf:RDF/rdf:Description", namespaces=nameSpace)
        
        node = description.find("dcterms:date[@rdfs:label='Uitspraakdatum']", namespaces=nameSpace)
        if node is not None:
            metadata.append("<b>Uitspraakdatum:</b> "+node.text)
            
        node = description.find("dcterms:creator[@rdfs:label='Instantie']", namespaces=nameSpace)
        if node is not None:
            metadata.append("<b>Instantie:</b> "+node.text)
        
        # Find possible related cases
        relations = description.findall("dcterms:relation", namespaces=nameSpace)
        relatedCases = []
        for rel in relations:
            relEcli = rel.get('{https://e-justice.europa.eu/ecli}resourceIdentifier')
            relText = rel.text
            relatedCases.append('<a href="/'+str(relEcli)+'" class="list-group-item">'+relText+'</a>')
        
        # Find all refs
        refs = xml.findall("./rdf:RDF/rdf:Description/dcterms:references[@metaLexResourceIdentifier]", namespaces=nameSpace)
        
        BWBarticle_regexp = re.compile("(BWB[VR]\d{7}).*?/artikel/([^/]+)")
        BWB_regexp = re.compile("(BWB[VR]\d{7})")
        
        for ref in refs:
            refstring = ET.tostring(ref, encoding='UTF-8', method='text').strip()
            link = ref.get("metaLexResourceIdentifier", default="#")
            ECLItext = ECLItext.replace(refstring, '<a href="'+link.replace("http://doc.metalex.eu/id/", "/")+'" class="ref">'+refstring+'</a>')
            m = BWBarticle_regexp.search(link)
            if m is not None:
                bwb = m.group(1)+"/artikel/"+m.group(2)
            else:
                bwb = None
                
            if bwb is not None:
                bwb_counter[bwb] += 1
        bwb_list = []
        for bwb in sorted(bwb_counter, key=bwb_counter.get, reverse=True):
            if len(bwb_list) >= 5:
                break
            bwb_list.append('<a href="/'+bwb+'" class="list-group-item">'+urllib.unquote(bwb).replace("/artikel/", ", Artikel ")+' <span class="badge pull-right">'+str(bwb_counter[bwb])+'x</span></a>')
            
        context = {
                   'errors': errors,
                   'Content': ECLItext,
                   'BWB_list': bwb_list,
                   'bwb_links': bwb_links,
                   'Header': ecli,
                   'ECLI': ecli,
                   'metadata': metadata,
                   'relatedCases': relatedCases,
                   }
        return render(request, 'overview/index.html', context)
    else:
        errors.append("<span class='glyphicon glyphicon-warning-sign'></span> Onbekende uitspraak!<BR>Tekst komt nu direct van rechtspraak.nl en bevat daarom geen referenties.")
        encoded_parameters = urllib.urlencode({'id': ecli})

        # Try to open the file for the ECLI
        feed = urllib2.urlopen("http://data.rechtspraak.nl/uitspraken/content?" + encoded_parameters, timeout=3)
        xml = ET.parse(feed)
        nameSpace = {'rdf': 'http://www.w3.org/1999/02/22-rdf-syntax-ns#', 'ecli': 'https://e-justice.europa.eu/ecli',
                     'eu': 'http://publications.europa.eu/celex/', 'dcterms': 'http://purl.org/dc/terms/',
                     'bwb': 'bwb-dl', 'cvdr': 'http://decentrale.regelgeving.overheid.nl/cvdr/',
                     'rdfs': 'http://www.w3.org/2000/01/rdf-schema#',
                     'preserve': 'http://www.rechtspraak.nl/schema/rechtspraak-1.0'}
                           
        uitspraak = xml.find("./preserve:uitspraak", namespaces=nameSpace)
        if uitspraak is not None:
            ECLItext = ET.tostring(uitspraak, encoding='UTF-8', method='html').strip()
        else:
            ECLItext = "Helaas kon ook op rechtspraak.nl de bijbehorende tekst niet gevonden worden."
        # Get meta data
        metadata = []
        description = xml.find("./rdf:RDF/rdf:Description", namespaces=nameSpace)
        
        node = description.find("dcterms:date[@rdfs:label='Uitspraakdatum']", namespaces=nameSpace)
        if node is not None:
            metadata.append("<b>Uitspraakdatum:</b> "+node.text)
            
        node = description.find("dcterms:creator[@rdfs:label='Instantie']", namespaces=nameSpace)
        if node is not None:
            metadata.append("<b>Instantie:</b> "+node.text)
        
        # Find possible related cases
        relations = description.findall("dcterms:relation", namespaces=nameSpace)
        relatedCases = []
        for rel in relations:
            relEcli = rel.get('{https://e-justice.europa.eu/ecli}resourceIdentifier')
            relText = rel.text
            relatedCases.append('<a href="/'+str(relEcli)+'" class="list-group-item">'+relText+'</a>')
            
        context = {
                   'errors': errors,
                   'Header': ecli,
                   'bwb_links': bwb_links,
                   'ECLI': ecli,
                   'Content': ECLItext,
                   'metadata': metadata,
                   'relatedCases': relatedCases,
                   }
        return render(request, 'overview/index.html', context)
        
 # List of BWB's in the subset
bwbDocuments = ['BWBR0011823',
                'BWBR0005537',
                'BWBV0001000',
                'BWBR0011825',
                'BWBV0001002']
    