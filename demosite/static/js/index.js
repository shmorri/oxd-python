function edit_enable()
            {
                dis = document.getElementsByClassName("ip_box");
                for(var i = 0; i < dis.length; i++)
                    dis[i].disabled = false;
                document.getElementById("update").disabled = false;
                //added
                var new_up = document.getElementById('edit');
                new_up.value = 'update';
            }
            /*
function control( var oxd_id )
               {   alert(oxd_id);

                    if(  oxd_id  == undefined)
                    {
                        document.getElementById("reg").disabled = false;
                        document.getElementById("edit").disabled = true;
                        document.getElementById("update").disabled = true;
                        document.getElementById("delete").disabled = true;
                    }
                    else
                    {
                        alert('inside else');
                        document.getElementById("reg").disabled = true;
                        document.getElementById("edit").disabled = false;
                        document.getElementById("update").disabled = false;
                        document.getElementById("delete").disabled = false;
                    }

                }

/*
var count_dynamic_reg = 0;
function dynamic_reg()
{
    if(count_dynamic_reg == 1)
        return;
    var new_label = document.createElement("label");
    new_label.innerHTML ="ClientId";
    new_label.setAttribute('class','req');
    var parent = document.getElementById("dy_ip");
    parent.appendChild(new_label);

    var container = document.createElement("input");
    container.setAttribute('type' , 'text');
    container.setAttribute('class' , 'ip_box');
    container.setAttribute('size' , '51');
    container.setAttribute('required','required');
    container.setAttribute('placeholder' , 'Enter ClientId');
    parent.appendChild(container);

    var new_label = document.createElement("label");
    new_label.innerHTML ="ClientSecret";
    new_label.setAttribute('class','req');
    var parent = document.getElementById("dy_ip");
    parent.appendChild(new_label);

    var container = document.createElement("input");
    container.setAttribute('type' , 'text');
    container.setAttribute('class' , 'ip_box');
    container.setAttribute('size' , '51');
    container.setAttribute('required','required');
    container.setAttribute('placeholder' , 'Enter ClientSecret');
    parent.appendChild(container);

    count_dynamic_reg++;

}

function remove_dy_reg()
{
    if(count_dynamic_reg == 0)
        return ;
    var parent = document.getElementById('dy_ip');
    var ele = document.getElementById('dy_ip').children;
    for(i=0; i<4; i++)
        parent.removeChild(ele[0]);
    count_dynamic_reg = 0;
}

var count_for_irp = 0;  //count for input role name in Enrollment And Access Management

function enable_text_box()
{
    document.getElementById("ip_box").disabled = false;
}

function create_ip()
{
    if(document.getElementById("ip_box").disabled)
        return ;
    if(document.getElementsByName("rad").value != "opt_2")
     {

    var container = document.createElement("input");
    container.setAttribute('type' , 'text');
    container.setAttribute('class' , 'ip');
    container.setAttribute('id' , count_for_irp.toString());
    container.setAttribute('placeholder' , 'Input role name');
    container.setAttribute('required' , 'required');

    var parent = document.getElementById("ip_text");
    parent.appendChild(container);
    //image: plus sign after input box
    var image = document.createElement("div");
    image.setAttribute('class' , 'glyphicon glyphicon-plus');
    image.setAttribute('onclick' , 'create_ip()');
    image.setAttribute('id','img'+count_for_irp.toString());
    parent.appendChild(image);
    count_for_irp = count_for_irp + 1;
     }
}

function radio_click(value)
{
    if(value=="opt_1")
        {
            //if any text box present(Generated). remove it
            document.getElementById("ip_box").disabled = true;
            remove_element();
        }
    else if(value=="opt_2")
        {
            enable_text_box();
        }
    else
        {
            //if any text box present(Generated). remove it
            document.getElementById("ip_box").disabled = true;
            remove_element();
        }
}
function remove_element()
{
    //var ele = document.getElementsByClassName('ip_box');
    var parent = document.getElementById('ip_text');
    var i;
    for(i=0;i<count_for_irp;i++)
    {
        var ele = document.getElementById(i.toString());
        var ele_img = document.getElementById('img'+i.toString());
        parent.removeChild(ele);
        parent.removeChild(ele_img);
    }
    count_for_irp = 0;
}
*/