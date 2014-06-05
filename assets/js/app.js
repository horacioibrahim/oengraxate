$(document).foundation();
var $csrfmiddlewaretoken = $("#wrapper_csrf").find('input[name=csrfmiddlewaretoken]').val();


// page::dashboard::post
$('#toggle-post').click( function () {
   $('#form-post').toggle(300);
});

// TODO: objAjaxPostValues

$('.objAjaxGetValues').click(function(e){
    e.preventDefault();
    var objid = $(this).data('oid');
    var url = $(this).attr('href');
    var fields = {}
    var btn_post = $('#post-document #btn_post_update');

    // constructor - pre settings fields values
    fields.oid = $("input[name=oid]");
    fields.title = $("input[name=title]");
    fields.subtitle = $("input[name=subtitle]");
    fields.categories = $("select[name=categories]");
    fields.type_post = $('#type_post'); // wrap container for radio buttons
    fields.content = $("textarea[name=content]");
    fields.tags = $("input[name=tags]");
    fields.published = $("input[name=published]");
    fields.priority_show = $('#priority_show'); // wrap container for radio buttons
    fields.slug = $('#slug');

    $.getJSON(url,
        function(json){
            $('#form-post').show(300);
            fields.oid.val(json._id.$oid);
            fields.title.val(json.title);
            fields.subtitle.val(json.subtitle);
            // remove attr selected of option
            fields.categories.find(':selected').attr('selected', null);
            filter_option = '[value="' + json.categories[0] + '"]';
            if (fields.categories.find(filter_option).length > 0) {
                fields.categories.find(filter_option).attr('selected', true);
            } else {
                alert("Err: Category option is not defined");
            }

            // remove attr checked of radio
            fields.type_post.find(':checked').attr('checked', null);
            filter_radio = '[value="' + json._cls.split('.')[1] + '"]';
            fields.type_post.find(filter_radio).prop('checked', true);

            fields.content.val(json.content);
            fields.tags.val(json.tags);
            fields.slug.text(json.slug);


            if (json.published) {
                fields.published.prop('checked', true);
            } else {
                fields.published.attr('checked', null);
            }

            // remove attr checked of radio
            fields.priority_show.find(':checked').attr('checked', null);
            filter_priority = '[value="' + json.priority_show + '"]';
            fields.priority_show.find(filter_priority).prop('checked', true);

            // change name of button: legibility import
            var update_label = 'Update (id: ...' + json._id.$oid.substr(-6,6) + ')'
            btn_post.text(update_label);

        });
});

$('#post-document input[type=reset]').click(function(){
        var btn_post = $('#post-document #btn_post_update');
        oid = $("input[name=oid]");
        oid.val('');
        // change name of button: legibility import. It's now important is to post!
        btn_post.text('Post');
    }
)

$('#btn_reschedule').click(function(){
    $('#reschedule').toggle(300);
});

$('.content_area').focus(function(){
    $(this).css("height", "200px");
})

/**************************************
* "naive solution"
* Workaround foundation form "crazy" handles.
* To check changes in #followed_by -> $followed_by
***************************************/
var $followed_by = '';
$(document).on('change', '#followed_by', function(){
    $followed_by = $(this).val();
});

function vex_ok_generic(msg) {
    // wrap to call vex easier
    vex.dialog.confirm({
        message:  msg,
        buttons: [
            $.extend({}, vex.dialog.buttons.YES, {
                text: 'Ok'
            }),
        ]
    });
}

$('.btn-categories').on('click', function(e){
    e.preventDefault();
    form = $(this).closest('form');
    var url = '/get/categories/';
    var email = $followed_by;
    window.my_category_message = '';

    if (email && email.indexOf('@') > 0) {
        post_dict = {'email':email, 'csrfmiddlewaretoken':$csrfmiddlewaretoken};
        $.post('/follower/', post_dict, function(data) {
            form.find('#followed_by').val("");

                if (data == 'false') {
                     vex_ok_generic('Email já cadastrado. Procure pela mensagem de confirmação de oengraxate.com ' +
                        'em sua caixa de entrada e em casos especiais na caixa spam.');
                } else {
                     vex_ok_generic('Obrigado pelo interesse! ' +
                            'Você receberá ' +
                            'um link para confirmação deste registro.');
                }

        })
        .fail(function() {
            vex_ok_generic('Uma falha não esperada ocorreu. Tente Novamente.');
        });

    }
});

$(document).on('click', '.btn-subjects-flag',  function(e) {
    e.preventDefault();
    category_slug = $(this).data("category");
    checkbox = $('#' + category_slug);

    if (checkbox.attr('checked'))
        checkbox.attr('checked', false);
    else
        checkbox.attr('checked', true);

    $(this).toggleClass('selected');

});

// MOBILE SUPPORT
function to_activeMenu() {
    var r = $('#return');
    var menuFocused = r.data("page");
    var all_active = $('.off-canvas-list')
        .find('a').each(function(i, elem) {
                    $(elem).removeClass('active');
                    $(elem).parent().removeClass('active');
        });

    target = $('.' + menuFocused);
    target.addClass('active');
    target.parent().addClass('active');

}

$(document).on('click', '.left-bar-menu',  function(e) {
   e.preventDefault();
   action = $(this).data("action"); // container-content
   is_large = $(this).find('.control');
   if (is_large.filter(':visible').length > 0) {
        place = '#container-content'
   } else {
       place = '#container-content-small'
   }
   to_place = $(place);
   to_place.load("/services/" + action + " #return", function() {to_activeMenu()});


});