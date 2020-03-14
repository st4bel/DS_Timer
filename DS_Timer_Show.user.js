// ==UserScript==
// @name        DS_Timer_SHOW
// @namespace   de.die-staemme
// @version     0.1
// @description Export your Attack-Details for DS_Timer
// @grant       GM_getValue
// @grant       GM_setValue
// @grant       unsafeWindow
// @match       https://*.die-staemme.de/game.php?*screen=info_village*
// @copyright   2016+, Raznarek, stabel
// ==/UserScript==

var $ = typeof unsafeWindow != 'undefined' ? unsafeWindow.$ : window.$;

$(function(){

    var storage = localStorage;
    var storagePrefix="Timer_show_";

    //Speicherfunktionen
    function storageGet(key,defaultValue) {
        var value= storage.getItem(storagePrefix+key);
        return (value === undefined || value === null) ? defaultValue : value;
        //return GM_getValue(key,defaultValue);
    }
    function storageSet(key,val) {
        storage.setItem(storagePrefix+key,val);
        //GM_setValue(key,val);
    }

    function get_actions() {
      var target_id = getPageAttribute("id");
      console.log('127.0.0.1:5000/show/target_id/'+target_id)
      setTimeout(function(){
        $.ajax({ url: 'http://127.0.0.1:5000/show/target_id/'+target_id,
          success: function(response){
            console.log("succes jay")
            console.log(JSON.stringify(response));
          }, error: function(response){
            console.log('server error');
          }
        })
      },1000);
    }
    get_actions();
    console.log("hey")
    init_UI();
    function init_UI(){
        var content_table = $("#content_value");
        var frame = $("<iframe>").attr("src","http://127.0.0.1:5000/show/target_id/"+getPageAttribute("id")).attr("id","iframe1");
        content_table.append(frame);
        var button_test = $("<button>").appendTo($("#linkContainer"))
        .click(function(){
            alert($("#abcabc").text())
        }).text("DSTIMER")
        .attr("class","btn")
        .attr("id","undso")
    }
    function getPageAttribute(attribute){
        var params = document.location.search;
        var value = params.substring(params.indexOf(attribute+"=")+attribute.length+1,params.indexOf("&",params.indexOf(attribute+"=")) != -1 ? params.indexOf("&",params.indexOf(attribute+"=")) : params.length);
        return params.indexOf(attribute+"=")!=-1 ? value : "0";
    }
});
