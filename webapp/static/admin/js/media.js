/*
* Copyright 2017 the Isard-vdi project authors:
*      Josep Maria Viñolas Auquer
*      Alberto Larraz Dalmases
* License: AGPLv3
*/


$(document).ready(function() {
    
	$('.btn-new').on('click', function () {
            $("#modalAddMediaForm")[0].reset();
			$('#modalAddMedia').modal({
				backdrop: 'static',
				keyboard: false
			}).modal('show');
            $('#modalAddMediaForm').parsley();
            $('#modalAddMediaForm #name').focus(function(){
                console.log(($(this).val()))
                if($(this).val()=='' && $('#modalAddMediaForm #url').val() !=''){
                    console.log($('#modalAddMediaForm #url').val())
                    $(this).val($('#modalAddMediaForm #url').val().split('/').pop(-1));
                }
            });
            setAlloweds_add('#alloweds-add');
	});

    var table=$('#media').DataTable( {
        "ajax": {
                "url": "/admin/table/media/get",
                "dataSrc": ""
				//~ "url": "/admin/tabletest/media/post",
                //~ "contentType": "application/json",
                //~ "type": 'POST',
                //~ "data": function(d){return JSON.stringify({'flatten':false})}            
        },
			"language": {
				"loadingRecords": '<i class="fa fa-spinner fa-pulse fa-3x fa-fw"></i><span class="sr-only">Loading...</span>'
			},
			"rowId": "id",
			"deferRender": true,
        "columns": [
				//~ {
                //~ "className":      'details-control',
                //~ "orderable":      false,
                //~ "data":           null,
                //~ "width": "10px",
                //~ "defaultContent": '<button class="btn btn-xs btn-info" type="button"  data-placement="top" ><i class="fa fa-plus"></i></button>'
				//~ },
            { "data": "icon"},
            { "data": "name"},
            //~ { "data": "status"},
            { "data": null},
                {"data": null,
                 'defaultContent': ''},  
        ],
        "columnDefs": [ 
							{
							"targets": 0,
							"render": function ( data, type, full, meta ) {
							  return renderIcon(full);
							}},
							{
							"targets": 1,
							"render": function ( data, type, full, meta ) {
							  return renderName(full);
							}},
                            {
							"targets": 2,
							"render": function ( data, type, full, meta ) {
                                if(full.status == 'Downloading'){
                                    return renderProgress(full);
                                }
                                if('progress-total' in full){return full['progress-total'];}
                                return ''
							}},
                            {
							"targets": 3,
							"render": function ( data, type, full, meta ) {                                
                                if(full.status == 'Available' || full.status == "FailedDownload"){
                                    return '<button id="btn-download" class="btn btn-xs" type="button"  data-placement="top" ><i class="fa fa-download" style="color:darkblue"></i></button>'
                                }
                                if(full.status == 'Downloading'){
                                    return '<button id="btn-abort" class="btn btn-xs" type="button"  data-placement="top" ><i class="fa fa-stop" style="color:darkred"></i></button>'
                                }
                                if(full.status == 'Downloaded' || full.status == 'Stopped'){
                                    return '<button id="btn-delete" class="btn btn-xs" type="button"  data-placement="top" ><i class="fa fa-times" style="color:darkred"></i></button>'
                                } 
                                return full.status;                                 
                                }}],
        "initComplete": function() {
                                //~ $('.progress .progress-bar').progressbar();
                                //~ $('.progress-bar').progressbar();
                              }
    } );

    $('#media').find(' tbody').on( 'click', 'button', function () {
        var data = table.row( $(this).parents('tr') ).data();
        switch($(this).attr('id')){
            case 'btn-delete':
				new PNotify({
						title: 'Confirmation Needed',
							text: "Are you sure you want to delete this media: "+data.name+"?",
							hide: false,
							opacity: 0.9,
							confirm: {
								confirm: true
							},
							buttons: {
								closer: false,
								sticker: false
							},
							history: {
								history: false
							},
							stack: stack_center
						}).get().on('pnotify.confirm', function() {
                            socket.emit('media_update',{'pk':data.id,'name':'status','value':'Deleting'})
						}).on('pnotify.cancel', function() {
				});
                break;
             case 'btn-abort':
                    //~ var pk=$(this).closest("div").attr("data-pk");
                    //~ console.log('abort:'+pk)
                    //~ var name=$(this).closest("div").attr("data-name");
                    new PNotify({
                            title: 'Confirmation Needed',
                                text: "Are you sure you want to abort this download: "+data.name+"?",
                                hide: false,
                                opacity: 0.9,
                                confirm: {
                                    confirm: true
                                },
                                buttons: {
                                    closer: false,
                                    sticker: false
                                },
                                history: {
                                    history: false
                                },
                                stack: stack_center
                            }).get().on('pnotify.confirm', function() {
                                socket.emit('media_update',{'pk':data.id,'name':'status','value':'DownloadAborting'})
                            }).on('pnotify.cancel', function() {
                    });	             
                break;

        };


        //~ $('btn-abort').on('click', function () {

        //~ });
        
        //~ $('btn-delete').on('click', function () {

        //~ });
    
    });    
    
    $("#modalAddMedia #send").on('click', function(e){
            var form = $('#modalAddMediaForm');

            form.parsley().validate();

            if (form.parsley().isValid()){
                data=$('#modalAddMediaForm').serializeObject();
                data=replaceAlloweds_arrays(data)
                socket.emit('media_add',data)
            }
            

        });

    // SocketIO
    socket = io.connect(location.protocol+'//' + document.domain + ':' + location.port+'/sio_admins');
     
    socket.on('connect', function() {
        connection_done();
        socket.emit('join_rooms',['media'])
        console.log('Listening media namespace');
    });

    socket.on('connect_error', function(data) {
      connection_lost();
    });
    
    socket.on('user_quota', function(data) {
        console.log('Quota update')
        var data = JSON.parse(data);
        drawUserQuota(data);
    });

    socket.on('media_data', function(data){
        //~ console.log('add or update')
        var data = JSON.parse(data);
            //~ $('#pbid_'+data.id).data('transitiongoal',data.percentage);
            //~ $('#pbid_').css('width', data.percentage+'%').attr('aria-valuenow', data.percentage).text(data.percentage); 
            //~ $('#psmid_'+data.id).text(data.percentage);
        dtUpdateInsert(table,data,false);
        //~ $('.progress .progress-bar').progressbar();
    });

    
    socket.on('media_delete', function(data){
        //~ console.log('delete')
        var data = JSON.parse(data);
        var row = table.row('#'+data.id).remove().draw();
        new PNotify({
                title: "Media deleted",
                text: "Media "+data.name+" has been deleted",
                hide: true,
                delay: 4000,
                icon: 'fa fa-success',
                opacity: 1,
                type: 'success'
        });
    });
    
    socket.on('result', function (data) {
        var data = JSON.parse(data);
        new PNotify({
                title: data.title,
                text: data.text,
                hide: true,
                delay: 4000,
                icon: 'fa fa-'+data.icon,
                opacity: 1,
                type: data.type
        });
    });

    socket.on('add_form_result', function (data) {
        var data = JSON.parse(data);
        if(data.result){
            $("#modalAddMediaForm")[0].reset();
            $("#modalAddMedia").modal('hide');
        }
        new PNotify({
                title: data.title,
                text: data.text,
                hide: true,
                delay: 4000,
                icon: 'fa fa-'+data.icon,
                opacity: 1,
                type: data.type
        });
    });

    socket.on('edit_form_result', function (data) {
        var data = JSON.parse(data);
        if(data.result){
            $("#modalEdit")[0].reset();
            $("#modalEditDesktop").modal('hide');
        }
        new PNotify({
                title: data.title,
                text: data.text,
                hide: true,
                delay: 4000,
                icon: 'fa fa-'+data.icon,
                opacity: 1,
                type: data.type
        });
    });

    
 } );


function renderProgress(data){ 
            perc = data.progress.received_percent
            return data.progress.total+' - '+data.progress.speed_download_average+'/s - '+data.progress.time_left+'<div class="progress"> \
                  <div id="pbid_'+data.id+'" class="progress-bar" role="progressbar" aria-valuenow="'+perc+'" \
                  aria-valuemin="0" aria-valuemax="100" style="width:'+perc+'%"> \
                    '+perc+'%  \
                  </div> \
                </<div> '
}

function renderName(data){
		return '<div class="block_content" > \
      			<h2 class="title" style="height: 4px; margin-top: 0px;"> \
                <a>'+data.name+'</a> \
                </h2> \
      			<p class="excerpt" >'+data.description+'</p> \
           		</div>'
}

function renderIcon(data){
		return '<span class="xe-icon" data-pk="'+data.id+'">'+icon(data.icon)+'</span>'
}

function icon(name){
    if(name.startsWith("fa-")){return "<i class='fa "+name+" fa-2x '></i>";}
    if(name.startsWith("fl-")){return "<span class='"+name+" fa-2x'></span>";}
       if(name=='windows' || name=='linux'){
           return "<i class='fa fa-"+name+" fa-2x '></i>";
        }else{
            return "<span class='fl-"+name+" fa-2x'></span>";
		}       
}
