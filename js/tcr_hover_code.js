var topicColorTable = {};


function GetTopicIDClass(p_className){

    var classList = p_className.split(/\s+/);
    return classList[1];
};

function GetWordIDClass(p_className){

    var classList = p_className.split(/\s+/);
    return classList[2];
};

function TopicIDMatch(p_className1, p_className2){
    
    return GetTopicIDClass(p_className1) == GetTopicIDClass(p_className2);
};


function WordIDMatch(p_className1, p_className2){
    
    return GetWordIDClass(p_className1) == GetWordIDClass(p_className2);
};


function HoverEnter(){

    var myClassName = this.className;
    var tagAndClass = this.tagName + "." + GetTopicIDClass(myClassName);
    var normBackground = $(this).css("color");
    var normColor = "dimgrey";

    $(tagAndClass).each(function(){
        if ( WordIDMatch(myClassName, this.className) ) { 
            $(this).css({"background-color": "white", "color": "black"}); 
        } else {
            //$(this).css({"background-color": normBackground, "color": "white"});
            $(this).css({"background-color": "dimgrey", "color": "white"});
        }
    });

    var topicIDClass = GetTopicIDClass(myClassName);
    var wordIDClass = GetWordIDClass(myClassName);
    $(".topicwordlist").text($(".invisible_topicwordlist." + topicIDClass).text());
    $(".topicwordlist").css({"color": topicColorTable[topicIDClass]});
    $(".meta_topicword").text($(".invisible_topicword." + topicIDClass + "." + wordIDClass).first().text());
    $(".meta_topicword").css({"color": topicColorTable[topicIDClass]});        
    $(".compositerank").text($(".invisible_compositerank." + topicIDClass + "." + wordIDClass).first().text());
    $(".compositerank").css({"color": topicColorTable[topicIDClass]});    
    $(".doctopicrank").text($(".invisible_doctopicrank." + topicIDClass + "." + wordIDClass).first().text());
    $(".doctopicrank").css({"color": topicColorTable[topicIDClass]});
    $(".topicwordrank").text($(".invisible_topicwordrank." + topicIDClass + "." + wordIDClass).first().text());
    $(".topicwordrank").css({"color": topicColorTable[topicIDClass]});    
};

function HoverExit(){

    var tagAndClass = this.tagName + "." + GetTopicIDClass(this.className);
    var bodyBackground = $("body").css("background-color");

    $(tagAndClass).each(function(){
        $(tagAndClass).css({"background-color": bodyBackground,
                            "color": topicColorTable[GetTopicIDClass(this.className)]});
    });
};