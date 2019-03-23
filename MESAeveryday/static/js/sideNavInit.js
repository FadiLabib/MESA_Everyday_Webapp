/*
MIT License
MESA © 2019
PSU Capstone 2018-2019
*/

// SideNav Initialization
$(".button-collapse").sideNav();

// Data Picker Initialization
$('.datepicker').pickadate({
	format: 'dd/mm/yyyy'
});

// Image Picker Initialization
$("select").imagepicker();

var container = document.querySelector('.custom-scrollbar');
Ps.initialize(container, {
		wheelSpeed: 2,
		wheelPropagation: true,
		minScrollbarLength: 20
});
$(document).ready( function () {
    $('#unearnedTable').DataTable();
    $('#earnedTable').DataTable();
});
            
