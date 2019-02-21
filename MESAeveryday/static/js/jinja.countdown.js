$('#clock').countdown($('span#clock').attr('data-date-string'), function(event) {
    $(this).html(event.strftime('%D days %H:%M:%S'));
});

$('#clock2').countdown($('span#clock2').attr('data-date-string-second'), function(event) {
    $(this).html(event.strftime('%D days %H:%M:%S'));
});

$('#clock3').countdown($('span#clock3').attr('data-date-string-third'), function(event) {
    $(this).html(event.strftime('%D days %H:%M:%S'));
});
