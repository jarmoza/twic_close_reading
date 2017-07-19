var topicColorTable = {};

function HoverEnter(){

    var topicIDClass = this.classList[1];
    var wordIDClass = this.classList[2];
    var tagAndClass = this.tagName + "." + this.classList[1];

    $(tagAndClass).each(function(){
        if ( wordIDClass == this.classList[2] ) {
            $(this).css({"background-color": "white", "color": "black"});
        } else {
            $(this).css({"background-color": "dimgrey", "color": "white"});
        }
    });

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

    var tagAndClass = this.tagName + "." + this.classList[1];
    var bodyBackground = $("body").css("background-color");

    $(tagAndClass).each(function(){
        $(tagAndClass).css({"background-color": bodyBackground,
                             "color": topicColorTable[this.classList[1]]});
    });
};
