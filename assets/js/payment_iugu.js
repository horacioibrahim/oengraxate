/**
 * Created by horacioibrahim on 30/05/14.
 */

Iugu.setAccountID("25dfe5de-f86a-4507-89ed-922796bc05a8");
Iugu.setTestMode(true);

// payment = {"number":"4111111111111111", "verification_value":"123", "expiration": "12/14", "full_name": "Joao Da Silva"}

function update_expires() {
    bs_date = $('.change_dt');
    month = bs_date[0].value;
    year = bs_date[1].value;
    expires = month + "/" + year;
    $("input#expiration").val(expires);
};

$(document).ready(function() {
    update_expires();
});

$('.change_dt').change(function(){
    update_expires();
});

jQuery(function($) {
  $('#payment-form').submit(function(evt) {
      evt.preventDefault();
      var form = $(this);
      var tokenResponseHandler = function(data) {

          if (data.errors) {
              // console.log(data.errors);
              alert("Erro salvando cartão: " + JSON.stringify(data.errors));
          } else {
              $("#token").val( data.id );
              // form.get(0).submit();
          }

          // Seu código para continuar a submissão
          // Ex: form.submit();
      }

      Iugu.createPaymentToken(this, tokenResponseHandler);
      return false;
  });
});
