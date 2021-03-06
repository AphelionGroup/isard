/*
* Copyright 2017 the Isard-vdi project authors:
*      Josep Maria Viñolas Auquer
*      Alberto Larraz Dalmases
* License: AGPLv3
*/


$(document).ready(function() {
    var table=$('#groups').DataTable( {
        "ajax": {
            "url": "/admin/table/groups/get",
            "dataSrc": ""
        },
			"language": {
				"loadingRecords": '<i class="fa fa-spinner fa-pulse fa-3x fa-fw"></i><span class="sr-only">Loading...</span>'
			},
        "columns": [
				{
                "className":      'details-control',
                "orderable":      false,
                "data":           null,
                "width": "10px",
                "defaultContent": '<button class="btn btn-xs btn-info" type="button"  data-placement="top" ><i class="fa fa-plus"></i></button>'
				},
            { "data": "name", className: "xe-name" },
            { "data": "description", className: "xe-description"}
        ]
    } );

    $('#groups').find('tbody').on('click', 'td.details-control', function () {
        var tr = $(this).closest('tr');
        var row = table.row( tr );
 
        if ( row.child.isShown() ) {
            // This row is already open - close it
            row.child.hide();
            tr.removeClass('shown');
        }
        else {
            // Open this row
            row.child( formatGroups(row.data()) ).show();
            //~ editGroup();
            tr.addClass('shown');
        }
    });

	$('.btn-new-group').on('click', function () {
        setQuotaOptions('#roles-quota');
			$('#modalAddGroup').modal({
				backdrop: 'static',
				keyboard: false
			}).modal('show');
            $('#modalAddGroupForm')[0].reset();
            //~ setModalAddUser();
	});    

    $("#modalAddGroup #send").on('click', function(e){
            var form = $('#modalAddGroupForm');
            console.log('inside')

            form.parsley().validate();
            if (form.parsley().isValid()){
                data=$('#modalAddGroupForm').serializeObject();
                console.log(data)
                data['table']='groups';
                socket.emit('role_category_group_add',data)  
            }
        });     
    
});

function formatGroups ( d ) {
    // `d` is the original data object for the row
    var cells=''
            //~ '<div class="btn-group"> \
                    //~ <button class="btn btn-sm btn-default btn-edit" id="btn-edit" type="button"  data-placement="top" data-toggle="tooltip" data-original-title="Edit"><i class="fa fa-pencil"></i></button> \
                //~ </div>';
    for(var k in d){
		cells+='<tr>'+
					'<td>'+k+':</td>'+
					'<td>'+d[k]+'</td>'+
				'</tr>'
	}
    return '<table cellpadding="5" cellspacing="0" border="0" style="padding-left:50px;">'+
        cells+
    '</table>';
}
