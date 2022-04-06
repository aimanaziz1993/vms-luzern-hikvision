(function($) {
    "use strict"; // Start of use strict
  
    // Handle generate unique code for Tenant
    let generate_code = function (e) {
        e.preventDefault();
        let url = $('.generate-code').attr("href");
        // let id = {{ user.id }}
        let userId = $('#hidden_userId').val();
        // let userId = userId;

        $.ajax({
            headers: { "X-CSRFToken": getCookie('csrftoken') },
            url: url,
            method: 'POST',
            data: {
                // 'user_id':id, //user_id pk
                'user_id':userId, //user_id pk
            }, 
            beforeSend: function(response){
                console.log('before');
            },
            success: function(response){
                // location.reload();
                swal.fire({
                    position: 'top-end',
                    type: 'success',
                    icon: 'success',
                    title: 'New code has been generated',
                    showConfirmButton: false,
                    timer: 1300
                });
                setTimeout(function(){
                    window.location.reload();
                }, 1300);
            },
            error: function(response){
                swal.fire("!Opps ", "Something went wrong, try again later", "error");
                // location.reload();
            }
        });
        return false;
    };
    $("body").on('click', '.generate-code', generate_code);

    // Hanndle clipboard Copy
    
  
  })(jQuery); // End of use strict