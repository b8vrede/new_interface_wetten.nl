function parseJsonLaw(json){
    html = "<div class=\"list-group\">";
    $.each( json, function( index, value ){
        html += '<a href="'+value.link+'" class="list-group-item';
        if(value.link === "#error"){
            html += ' list-group-item-warning';
        }
        html += '">'+value.label+'</a>';
    });
    html+="</div>";
    return html;
}
function loadRelatedLaw(expressie, article){
    $("#relLaw, #relCaselaw").html('<a href="#" class="list-group-item list-group-item-info"><span class="glyphicon glyphicon-info-sign"></span> Referenties aan het doorzoeken...</a>');
    request = $.ajax({
      url: "/ajax/related_law/",
      dataType: "json",
      type: "GET",
      data: { expression: expressie, article: article.trim() },
      cache: true
    })
    request.done(function( data ) {
        $("#relLaw").html(parseJsonLaw(data['law']));
        $("#relCaselaw").html(parseJsonLaw(data['case']));
        });
    request.fail(function() {
        $("#relLaw, #relCaselaw").html('<a href="#" class="list-group-item list-group-item-danger"><span class="glyphicon glyphicon-fire"></span> Er is een fout onstaan tijdens het laden.</a>');
        });
}