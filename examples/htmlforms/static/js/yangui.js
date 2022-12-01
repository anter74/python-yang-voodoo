
/*

The UI components are controlled in part client side.

- Each node that needs control is given ID's such as 'choice-<base64-id-xpath>'
- Nodes can be blurred - with the 'yangui-disable' class
- Nodes can be collapsed - without the `show` class or shown with the `show` class
- Some nodes have actions (disable/enable a case) which are entirely client side.


*/

function modal_visibility(id, hide_or_show){
  $('#'+id).modal(hide_or_show)
}

function start_yangui-spinner(text){
  $("#yangui-spinner").removeClass("yangui-hidden");
  document.getElementById("yangui-spinnertext").innerHTML=text;
}

function stop_yangui-spinner(text){
  $("#yangui-spinner").addClass("yangui-hidden");
  document.getElementById("yangui-spinnertext").innerHTML="";
}

function addAlert(title, message, theme) {
    $('#alerts').append(
      '<div class="alert alert-' + theme + ' alert-dismissible fade show" role="alert">' +
      '<strong>'+title+'</strong> &nbsp;' + message +
      '<button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>' +
      '</div>');

}

// function onError() {

// }
function leaf_change(d, h){
  console.log("Leaf has changed\n\nData XPATH:" + d + "\nHTMLNode: "+h);
}

function leaf_blur(d, h){
  console.log("Leaf has blurred\n\nData XPATH:" + d + "\nHTMLNode: "+h);
}

function select_change(d, h){
  console.log("Dropdown has changed\n\nData XPATH:" + d + "\nHTMLNode: "+h);
}

function select_blur(d, h){
  console.log("Dropdown has blurred\n\nData XPATH:" + d + "\nHTMLNode: "+h);
}

function check_change(d, h){
  console.log("Checkbox has changed\n\nData XPATH:" + d + "\nHTMLNode: "+h);
}

function check_blur(d, h){
  console.log("Checkbox has blurred\n\nData XPATH:" + d + "\nHTMLNode: "+h);
}

function empty_change(d, h){
  console.log("Empty leaf has changed\n\nData XPATH:" + d + "\nHTMLNode: "+h);
}

function empty_blur(d, h){
  console.log("Empty leaf has blurred\n\nData XPATH:" + d + "\nHTMLNode: "+h);
}

function add_list_element(d, s){
  Mousetrap.bind('escape', function() { close_new_item(); });

  $("#capture-new-item").removeClass("#yangui-hidden");
  $("#capture-new-item-list-contents").innerHTML="Not Implemented - fetch contents from a server specific to list";

  payload={ "action": "add_list_element", "data_xpath": d, "schema_xpath":s}
  alert("NotImplemented - add list element to list\n\nData XPATH: " +d+"\nSchema XPATH: "+s+"\nPayload to send:" +JSON.stringify(payload));

  $.ajax({
      type: "POST",
      url: AJAX_SERVER_URL,
      crossDomain: true,
      data: JSON.stringify(payload),
      cache: false,
      success: function(response) {
          $("#capture-new-item-list-contents").html(response);
      },
      error: function(xhr, options, err) {

        alert("TODO: error on add list_element: "+xhr.status);
      }
  });
}

function close_new_item(){
  Mousetrap.reset();
  $("#capture-new-item").addClass("yangui-hidden");
  $("#capture-new-item-list-contents").innerHTML="Not Implemented - fetch contents from a server specific to list";
}

function remove_list_element(b_path){
  start_yangui-spinner("Removing list item");
  // modal_visibility('mymodal', 'show');

  payload = {'data_xpath_b64': b_path}
  $.ajax({
      type: "POST",
      url: AJAX_SERVER_URL+"/remove-list-element",
      crossDomain: true,
      data: JSON.stringify(payload),
      cache: false,
      success: function(response) {
        $(document.getElementById("list-item-"+b_path)).remove();
        stop_yangui-spinner();
      },
      error: function(xhr, options, err) {
        addAlert("Connectivity Error", handle_ajax_error(xhr), 'danger');
        stop_yangui-spinner();
      }

  });
}

function enable_case(b_path, b_parent_path){
  // Give the base64 path of the choice container (i.e. our case's parent)
  // loop around all span's
  // - hide any enable case buttons
  // - show our remove-case path
  // - remove the opactity disabling of our case
  // - expand the our case (add show)
  choiceDiv = $(document.getElementById(b_parent_path));
  choiceDiv.find("span").each(function(index){
      if(this.id == "remove-case-" + b_path){
        $(this).removeClass("yangui-hidden");
      }
      if(this.id.startsWith("enable-case-")){
        $(this).addClass("yangui-hidden");
      }
  });
  caseDiv=$(document.getElementById("case-" + b_path ));
  caseDiv.removeClass('yangui-disable');
  caseDiv.addClass('show');
  caseDiv.find("input").each(function(index){
    $(this).removeAttr('disabled');
  });
}

function disable_case(b_parent_path){
  // Given the base64 path of the choice container (i.e. our case's parent)
  // - loop around all span's
  // use the button name remove-case-<base64path> to disable the div case-<base64path>
  // hide all the remove-case-<base64path> buttons
  // show all the enable-case-<base64path> buttons
  choiceDiv = $(document.getElementById(b_parent_path));
  choiceDiv.find("span").each(function(index){
      $(document.getElementById(this.id.substring(7)) ).addClass('yangui-disable');
      if(this.id.startsWith("remove-case-")){
        $(this).addClass("yangui-hidden");
      }
      if(this.id.startsWith("enable-case-")){
        $(this).removeClass("yangui-hidden");
      }
  });
}

function add_leaflist_element(b_d_path, b_s_path){
  start_yangui-spinner("");

  payload = {'data_xpath_b64': b_d_path, 'schema_xpath_b64':b_s_path}
  $.ajax({
      type: "POST",
      url: AJAX_SERVER_URL+"/add-leaf-list-element-form",
      crossDomain: true,
      data: JSON.stringify(payload),
      cache: false,
      success: function(response) {
        $(document.getElementById("capture-new-item-list-contents")).innerHTML=response;
        stop_yangui-spinner();
        
        $(document.getElementById("capture-new-item")).removeClass('yangui-hidden');

      },
      error: function(xhr, options, err) {
        addAlert("Connectivity Error", handle_ajax_error(xhr), 'danger');
        stop_yangui-spinner();
      }
  });
}

function remove_leaflist_element(b_path){
  start_yangui-spinner("Removing leaf-list item");

  payload = {'data_xpath_b64': b_path}
  $.ajax({
      type: "POST",
      url: AJAX_SERVER_URL+"/remove-leaf-list-element",
      crossDomain: true,
      data: JSON.stringify(payload),
      cache: false,
      success: function(response) {
        $(document.getElementById("leaflist-item-"+b_path)).remove();
        stop_yangui-spinner();
      },
      error: function(xhr, options, err) {
        addAlert("Connectivity Error", handle_ajax_error(xhr), 'danger');
        stop_yangui-spinner();
      }

  });
}

function handle_ajax_error(xhr){
  if(xhr.status==0){
    return "Connection to server failed - (0)"
  }
  return xhr.responseText + " ("+xhr.status+")"
}

function presence_container_expand(d){
  containerDiv = $(document.getElementById(d));
  if(containerDiv.hasClass("yangui-disable")){
    containerDiv.removeClass("yangui-disable");
    alert("NotImplemented - expand a presence container that was previously empty\n\nData XPATH: "+d + "\nTODO: create data at XPATH with a value of ''");
  }
}
