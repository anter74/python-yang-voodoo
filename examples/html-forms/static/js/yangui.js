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

function add_list_element(d, s){
  alert("NotImplemented - add list element to list\n\nData XPATH: " +d+"\nSchema XPATH: "+s);
}

function remove_list_element(d){
  alert("NotImplemented - remove list element from list\n\nData XPATH: " + d);
}

function remove_case(s){
  alert("NotImplemented - remove case\n\Schema XPATH: " + s);
}

function add_leaflist_element(d, s){
  alert("NotImplemented - add list element to leaf-list\n\nData XPATH: " +d+"\nSchema XPATH: "+s);
}

function remove_leaflist_element(d){
  alert("NotImplemented - remove list element from leaf-list\n\nData XPATH: " + d);
}
