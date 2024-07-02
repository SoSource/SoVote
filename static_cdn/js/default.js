


// npm install crypto-js
// Import CryptoJS library (if using npm)
// const CryptoJS = require('crypto-js');

// Function to encrypt and store data in localStorage
function encryptAndStore(key, data) {
  const encryptedData = CryptoJS.AES.encrypt(JSON.stringify(data), key).toString();
  localStorage.setItem('encryptedData', encryptedData);
}

// Function to retrieve and decrypt data from localStorage
function retrieveAndDecrypt(key) {
  const encryptedData = localStorage.getItem('encryptedData');
  if (encryptedData) {
    const decryptedBytes = CryptoJS.AES.decrypt(encryptedData, key);
    const decryptedData = JSON.parse(decryptedBytes.toString(CryptoJS.enc.Utf8));
    return decryptedData;
  }
  return null;
}

// // Example usage
// const secretKey = 'super-secret-key';
// const dataToStore = { username: 'john_doe', password: 'secure_password' };

// // Encrypt and store data
// encryptAndStore(secretKey, dataToStore);

// // Retrieve and decrypt data
// const retrievedData = retrieveAndDecrypt(secretKey);
// console.log(retrievedData);


// $('#result').html("<br />$('form').serialize():<br />"+ $('form').serialize()+"<br /><br />$('form').serializeArray():<br />" + JSON.stringify($('form').serializeArray()));

// <html>
// <head>
// <script src="http://code.jquery.com/jquery-git2.js"></script>
// <meta charset=utf-8 />
// <title>JS Bin</title>
// </head>
// <body>
//   <form>
//     <input type="radio" name="foo" value="1" checked="checked" />
//     <input type="radio" name="foo" value="0" />
//     <input name="bar" value="xxx" />
//     <select name="this">
//       <option value="hi" selected="selected">Hi11</option>
//       <option value="ho">Ho11</option>
//     </select>
//   </form>
//   <div id=result></div>
// </body>
// </html>



async function react(item, iden, button=null){
  console.log('react')
  
  userData = get_stored_userData();
  // // console.log(storedData)
  // var userData = storedData[0];
  // var userArrayData = storedData[1];
  if (userData == null || userData == 'null') {
    modalPopUp('Login / Signup', '/accounts/login-signup')
  } else {
    if(item == 'follow2'){
      // alert(iden)
      var navBar = document.getElementById('navBar');
      // alert(navBar)
      follow = item.split('-')[0]
      // console.log(follow)
      li = navBar.getElementsByClassName('follow')[0]
      // alert(li)
      // SpeechRecognitionAlternative(li)
      li.classList.toggle('active');
      // alert(iden)
      if (iden.includes('?follow=')||iden.includes('&follow=')){
        link = iden
      } else {
        link = '?follow=' + iden
      }
      // console.log(link)
      $.get(link, function(data){
        // console.log('receveid dreturn data')
        // console.log(data)
        // console.log(data.replace(/&quot;|&#039;/g, '"'))
        // if (data.includes('Login')){
        //   alert('Please Login')
        // }
          var parser = new DOMParser();
          var htmlDoc = parser.parseFromString(data, 'text/html');
        // ParsedElements = $.parseHTML(data)
        // console.log(htmlDoc)
        check_instructions(htmlDoc)
      });
    // } else if (item == 'saveButton') {
    //   button = 'saveButton' + '-' + item
    //   li = document.getElementsByClassName(button)[0]
    //   li.innerHTML = 'Saved'

    } else {
      const data = {'item':item, 'post_id':iden}
      var rs = document.getElementsByClassName('reactionBar');
      var convert_to_none = false;
      for(i=0; i<rs.length; i++){
        if (rs[i].id == iden){
          if (item == 'yea'){
            // alert('yea')
            li = rs[i].getElementsByClassName('yea')[0]
            if(String(li.classList).includes('active')){
              convert_to_none = true
            } 
            li.classList.toggle('active');
            li.classList.add('depress');
            // alert(li.classList)
            li2 = rs[i].getElementsByClassName('nay')[0]
            li2.classList.remove('active');
            // li.focus()
            // alert(li.classList)
          }else if (item == 'nay'){
            li = rs[i].getElementsByClassName('nay')[0]
            if(String(li.classList).includes('active')){
              convert_to_none = true
            }
            li.classList.toggle('active');
            li.classList.add('depress');
            li2 = rs[i].getElementsByClassName('yea')[0]
            li2.classList.remove('active');
          } else if (item == 'verify') {
            modalPopUp('Verify Me', '/utils/verify_post_modal/' + iden)
            return
          } else if (item == 'insight') {
            modalPopUp('Insight', '/utils/post_insight_modal/' + iden)
            return
          } else if (item == 'more') {
            modalPopUp('More Options', '/utils/post_more_options_modal/' + iden)
            return
          } else if (item == 'saveButton') {
          } else if (item == 'share') {
            // var popup = document.getElementById('share-' + iden);
            // popup.classList.toggle("show");
            // li = rs[i].getElementsByClassName(item)[0]
            // li.classList.toggle('active');
            // li.classList.add('depress');
            modalPopUp('Share Post', '/utils/share_modal/' + iden)
            return
          } else if (item == 'follow' || item == 'unfollow') {
            console.log('is follow')
            var post_id = iden
          //   // var userData = localStorage.getItem("userData");
          //   storedData = get_stored_userData();
            console.log(userData.follow_post_id_array)
          //   var userData = storedData[0];
          //   var userArrayData = storedData[1];
          //   // // userData = JSON.parse(userData)
            // if (item == 'follow') {
            //   if (userArrayData.follow_post_id_array.length > 980) {
            //     userArrayData.follow_post_id_array.shift()
            //   }
            //   userArrayData.follow_post_id_array.push(post_id);
            // } else if (item == 'unfollow') {
            //   // var follow_post_id_array = JSON.parse(userData.follow_post_id_array.replace(/'/g, '"'));
            //   var index = userArrayData.follow_post_id_array.indexOf(post_id);
            //       if (index !== -1) { 
            //         userArrayData.follow_post_id_array.splice(index, 1);
            //       }
            // }

          //   // localStorage.setItem('userData', JSON.stringify(data));
          //   // var userData = localStorage.getItem("userData");
          //   console.log(JSON.stringify(userData))
          //   console.log(JSON.stringify(userArrayData))
          //   // userData = JSON.parse(userData)
          //   console.log('2')
          //   // console.log(JSON.stringify(userData.interest_array))
          //   // var interest_array = JSON.parse(JSON.stringify(userData.interest_array).replace(/'/g, '"'));
          //   // // console.log(interest_array)
          //   // var follow_topic_array = JSON.parse(JSON.stringify(userData.follow_topic_array).replace(/'/g, '"'));
          //   // userData.interest_array = interest_array
          //   // userData.follow_topic_array = follow_topic_array
            
          //   // var follow_post_id_array = JSON.parse(JSON.stringify(userData.follow_post_id_array).replace(/'/g, '"'));
          //   // follow_post_id_array.push(cmd.post_id);
          //   // userData.follow_post_id_array = follow_post_id_array
          //   // console.log(JSON.stringify(userData))
          //   // console.log('---')
        
          //   // console.log(userArrayData.interest_array)
          //   // var interest_array = JSON.parse(userData.interest_array.replace(/'/g, '"'));
          //   // console.log(interest_array)
          //   // console.log('3')
          //   // var follow_topic_array = JSON.parse(userData.follow_topic_array.replace(/'/g, '"'));
          //   userData.interest_array = userArrayData.interest_array
          //   userData.follow_topic_array = userArrayData.follow_topic_array
            
          //   var follow_post_id_array = JSON.parse(userData.follow_post_id_array.replace(/'/g, '"'));
          //   // follow_post_id_array.push(post_id);
          //   var index = follow_post_id_array.indexOf(post_id);
          //       if (index !== -1) { 
          //         follow_post_id_array.splice(index, 1);
          //       }
          //   userData.follow_post_id_array = follow_post_id_array
          //   console.log(JSON.stringify(userData))
          // //   console.log('---')
          // storedData = get_stored_userData();
          // // // console.log(storedData)
          // var userData = storedData[0];
          // var userArrayData = storedData[1];
          // var userData = localStorage.getItem("userData");
          // // console.log(userData)
          // // userData = JSON.parse(userData)
          // var userArrayData = {}
          // userArrayData.interest_array = JSON.parse(JSON.stringify(userData.interest_array).replace(/'/g, '"'))
          // userArrayData.follow_topic_array = JSON.parse(JSON.stringify(userData.follow_topic_array).replace(/'/g, '"'));
          // userArrayData.follow_post_id_array = JSON.parse(JSON.stringify(userData.follow_post_id_array).replace(/'/g, '"'));
          // console.log('2')
          // console.log(JSON.stringify(userData.interest_array))
          // var interest_array = x;
          // console.log(interest_array)
          // var 
          // interest_array = JSON.parse(interest_array)
          try{
            follow_post_id_array = JSON.parse(userData.follow_post_id_array)
          } catch(err) {
            follow_post_id_array = userData.follow_post_id_array
          }
          if (item == 'follow') {
            if (follow_post_id_array.length > 980) {
              follow_post_id_array.shift()
            }
            follow_post_id_array.push(post_id);
          } else if (item == 'unfollow') {
            // var follow_post_id_array = JSON.parse(userData.follow_post_id_array.replace(/'/g, '"'));
            var index = follow_post_id_array.indexOf(post_id);
                if (index !== -1) { 
                  follow_post_id_array.splice(index, 1);
                }
          }
          userData.follow_post_id_array = JSON.stringify(follow_post_id_array)
          // var follow_post_id_array = 
          // userArrayData.follow_post_id_array.push(cmd.post_id);
          // var index = follow_post_id_array.indexOf(cmd.post_id);
          // // console.log('index', index)
          // if (index !== -1) { 
          //   follow_post_id_array.splice(index, 1);
          // }
          // userData.follow_post_id_array = userArrayData.follow_post_id_array
          console.log(JSON.stringify(userData))
          console.log('---')
        

          //   console.log('show button press', item)
            li = rs[i].getElementsByClassName('follow')[0]
            li.classList.toggle('active');
            li.classList.add('depress');
          //   userData = await sign(userData)
          userData = await sign_userData(userData)
          return_signed_userData(userData)
          //   // sign_and_return_userData(userData, userArrayData);


          //   const postData = {};
          //   postData['objData'] = JSON.stringify(userData);
          //   // postData['localData'] = JSON.stringify(userData);
          //   // console.log('postData',postData)
          //   // console.log('send to receive_interaction_data')
            
          //   $.ajax({
          //     type:'POST',
          //     // url:'/accounts/receive_test_data',
          //     url:'/accounts/receive_interaction_data',
          //     data: postData,
          //     success:function(response){
          //       console.log(response)
          //     }
          //   });

            
          } else {
            li = rs[i].getElementsByClassName(item)[0]
            li.classList.toggle('active');
            li.classList.add('depress');
            // alert('done')
          }
        }

      }
      try {
        setTimeout(function (){
          // alert(li.classList)
          li.classList.remove('depress');     
          // alert(li.classList)
  
        }, 200);
      } catch(err) {console.log(err)}
      // alert('n')
      if (convert_to_none){
        item = 'None'
      }
      if (item != 'share' && item != 'follow' && item != 'unfollow') {
        console.log('makerequest for interaction object')
        // console.log(data)
        makeAjaxRequest({}, '/accounts/reaction/' + iden + '/' + item, data)
          .then(signReturnInteraction)
          .catch(error => {
            console.error('There was a problem with the AJAX request:', error);
        });


        
        // $.get('/accounts/reaction/' + iden + '/' + item, function(data){
        //   // return JsonResponse({'message' : 'Please fill, sign and return', 'data' : get_signing_data(vote)})

        //   // alert(data)
        //   if (data.includes('Login')){
        //     alert('Please Login')
        //   } else if (item == 'follow'){
        //     alert(data)
        //   }

        // });
      }
    }
  }

  
}
async function signReturnInteraction({ response, item }) {
  // console.log('receive signReturnInteraction data')
  // console.log(response);
  data = JSON.parse(response['data']);
  // console.log(data['object_type'])
  // console.log(item)
  cmd = item
  userData = get_stored_userData()
  user_id = userData.id
  data.User_obj = user_id
  if (data['object_type'] == 'UserVote') {
    if (data.vote == 'yea' && cmd.item == 'yea' || data.vote == 'nay' && cmd.item == 'nay') {
      data.vote = 'none'
    } else {
      data.vote = cmd.item
    }
    
  } else if (data['object_type'] == 'SavePost') {
    if (data.saved == false) {
      data.saved = true
      post_save_state = true
    } else {
      data.saved = false
      post_save_state = false
    }
  }



  data = await sign(data)
  // userData = await sign(userData)
  // console.log(JSON.stringify(userData))
  const postData = {};
  postData['objData'] = JSON.stringify(data);
  console.log('---')
  // console.log(postData)
  $.ajax({
    type:'POST',
    // url:'/accounts/receive_test_data',
    url:'/accounts/receive_interaction_data',
    data: postData,
    success:function(response){
      console.log(response)
      if (response['message'] == 'Success') {
        if (item.item == 'saveButton') {
          li = document.getElementsByClassName('saveButton, clickable')[0]
          if (post_save_state == true) {
            li.innerHTML = 'Saved'
          } else {
            li.innerHTML = 'Save'
          }
        }
      //     field3.innerHTML = 'Username does not match password'
      // } else if (response['message'] == 'Valid Username and Password'||response['message'] == 'User Created') {
      //   console.log('proceed to login')
      //   // console.log(JSON.stringify(response['userData']))
      //   localStorage.setItem('passPrivKey', keyPair[0]);
      //   localStorage.setItem('passPubKey', keyPair[1]);
      //   localStorage.setItem('display_name', JSON.parse(response['userData'])['display_name']);
      //   localStorage.setItem('userData', response['userData']);
      //   login()
      //   // modalPopUp('Select Region', '/accounts/get_country_modal')
      } else {
        console.log('else, post-interaction')
        if (data['object_type'] == 'UserVote') {
          // data.vote = item
          if (item == 'yea'){
            // alert('yea')
            li = rs[i].getElementsByClassName('yea')[0]
            // if(String(li.classList).includes('active')){
            //   convert_to_none = true
            // } 
            li.classList.toggle('active');
            li.classList.add('depress');
            // alert(li.classList)
            // li2 = rs[i].getElementsByClassName('nay')[0]
            // li2.classList.remove('active');
            // li.focus()
            // alert(li.classList)
          }else if (item == 'nay'){
            li = rs[i].getElementsByClassName('nay')[0]
            // if(String(li.classList).includes('active')){
            //   convert_to_none = true
            // }
            li.classList.toggle('active');
            li.classList.add('depress');
            // li2 = rs[i].getElementsByClassName('yea')[0]
            // li2.classList.remove('active');
          }

        }
        alert(response['message'])
      }
    },
    error: function (xhr, ajaxOptions, thrownError) {
      console.log('prob2')
      field3.innerHTML = 'Failed to reach server';
    } 
  });
      
}

// function myFunction(iden) {
//   // Get the text field
//   var copyText = document.getElementById(iden);
//   alert(copyText)
//   // Select the text field
//   copyText.select();
//   copyText.setSelectionRange(0, 99999); // For mobile devices

//   // Copy the text inside the text field
//   navigator.clipboard.writeText(copyText.value);
  
//   // Alert the copied text
//   alert("Copied the text: " + copyText.value);
// }
// const copyToClipboard = async (iden) => {
//   alert(iden)
//   // let a = document.getElementsByClassName(iden);
//   // alert(a)
//   // alert(a.id)
//   // let text = 'testcopy'
//   // var copyText = document.getElementById(iden);
//   // alert(copyText)
//   try{
//     /* Get the text field */
//     var copyText = 'testcopy'
      
//      /* Copy the text inside the text field */
//     navigator.clipboard.writeText(copyText);
  
//     /* Alert the copied text */
//     alert("Copied: " + copyText);
//   }catch(err){alert(err)}
// }

function mobileShare(iden) {
  // var rs = document.getElementsByClassName('reactionBar');
  // for (i=0;i<rs.length;i++) {
  //   if (rs[i].id == iden) {
  //     li = rs[i].getElementsByClassName('share')[0]
  //     li.classList.toggle('active');
  //     li.classList.add('depress');
  //   }
  // }
  modalPopUp('Share Post', '/utils/share_modal/' + iden)
    $.get('/utils/mobile_share/' + iden, function(data){
      setTimeout(function (){
        li.classList.remove('active');     
        li.classList.remove('depress'); 
      }, 200);
    });

}

function copyToClipboard(text) {
  if (text[0] == '/') {
    text = 'SoVote.ca' + text
    // alert(text)
  }
  try{
    navigator.clipboard.writeText(text).then(() => {
      alert("copied " + text);
    });
  }catch(err){}

}

function readAloud(iden){
  // alert('start')
  card = document.getElementById(iden);
  let text = $(card).find('.TextContent').text()
  let control = $(card).find('.listen').text()
  var msg = new SpeechSynthesisUtterance(text);
  // alert(control)
  if(control == 'Read Aloud'){
    $(card).find('.listen').text('Pause Player')
    window.speechSynthesis.cancel(msg);
    window.speechSynthesis.speak(msg);
    // alert(window.speechSynthesis.speaking);
    // alert('done')
  }else if (control == 'Pause Player'){
    $(card).find('.listen').text('Resume Player')
    window.speechSynthesis.cancel(msg);
  }else if (control == 'Resume Player'){
    $(card).find('.listen').text('Pause Player')
    window.speechSynthesis.resume(msg);
  } 
}
function removeNotification(iden){
  
  $.get('/utils/remove_notification/' + iden, function(data){});
  n = document.getElementsByClassName('notification')
  for(i=0;i<n.length;i++){
    if(n[i].id == iden){
      // alert('remove')
      n[i].remove()
      // alert('removed')
    }
  }
}
function addNotification(word){
  // alert(word);
  $.get('/utils/test_notification', function(data){});
}
function calendarWidget(){
  c = document.getElementById('calendarForm');
  c.classList.toggle('showForm');
}
// function datePickerWidget(){
//   c = document.getElementById('datePickerForm');
//   c.classList.toggle('showForm');
// }
function subNavWidget(value){
  navBar = document.getElementById('navBar')
  ul = navBar.getElementsByTagName('ul')[0]
  ul.classList.toggle('bottomBorder')
  li = navBar.getElementsByTagName('li')
  forms = ['chamberForm', 'searchForm', 'datePickerForm', 'partyForm', 'sortForm', 'pageForm', 'voteForm']
  if (value == 'chamberForm'){
    x = 'Chamber'
  } else if (value == 'searchForm'){
    x = 'Search'
  } else if (value == 'datePickerForm'){
    x = 'Date'
  } else if (value == 'partyForm'){
    x = 'Party:'
  } else if (value == 'sortForm'){
    x = 'Sort:'
  } else if (value == 'pageForm'){
    x = 'Page:'
  } else if (value == 'voteForm'){
    x = 'Vote:'
  }
  for(i=0;i<li.length;i++){
    // alert(value)
    if (li[i].textContent.includes(x) || li[i].textContent.includes('Current') || li[i].textContent.includes('Upcoming')){
      li[i].classList.toggle('active')
    } else {
      li[i].classList.remove('active')
    }
  }
  // alert(value)
  for(i=0;i<forms.length;i++){
    // alert(i)
    try{
      c = document.getElementById(forms[i]);
      if (value == forms[i]){
        // alert('show')
        c.classList.toggle('showForm');
      } else {
        // alert(forms[i])
        c.classList.remove('showForm');
      }
    }catch(err){
      // alert(err)
    }
  }
  // c = document.getElementById(value);
  // c.classList.toggle('showForm');
}
function sidebarSort_old(head){
  // alert(head)
  if(head.includes('-')){
    var title = head.split('-')[0];
    var task = head.split('-')[1];
    var list = document.getElementById(title).nextElementSibling.firstElementChild;
    var items = list.childNodes;
    var itemsArr = [];
    for (var i in items) {
        if (items[i].nodeType == 1) { // get rid of the whitespace text nodes
          itemsArr.push(items[i]);
        }
    }
    if(task == 'inst'){
      // alert('inst')
      a = document.getElementById(title);
      var b = title + '-alpha'
      $(a).children().first().remove()
      code = `<span onclick="sidebarSort('` + b + `')">sort</span>`
      $(a).append(code) 
      // alert(parseInt(itemsArr[0].firstElementChild.firstElementChild.innerHTML.replace('(', '').replace(')','')))
      // alert(b.innerHTML)
      itemsArr.sort(function(a, b) {
        return a.innerHTML == b.innerHTML
                ? 0
                : (parseInt(b.firstElementChild.firstElementChild.innerHTML.replace('(', '').replace(')','')) > parseInt(a.firstElementChild.firstElementChild.innerHTML.replace('(', '').replace(')','')) ? 1 : -1);
      });
    }else{
      // alert('alpha')
      a = document.getElementById(title);
      var b = title + '-inst'
      $(a).children().first().remove()
      code = `<span onclick="sidebarSort('` + b + `')">sort</span>`
      $(a).append(code) 
      itemsArr.sort(function(a, b) {
        return a.innerHTML == b.innerHTML
                ? 0
                : (a.innerHTML > b.innerHTML ? 1 : -1);
      });
    }
    for (i = 0; i < itemsArr.length; ++i) {
      list.appendChild(itemsArr[i]);
    }
  }else{
    // clear notifications
  }

}

function sidebarSort(head){
  // alert(head)
  var isMobile = document.getElementById('isMobile').name;

  if(head.includes('-')){
    var title = head.split('-')[0];
    var task = head.split('-')[1];
    if (isMobile == 'True'){
      var pages = document.getElementsByClassName('searchTabContent show block')[0];
      var list = pages.firstElementChild.nextElementSibling;
      a = pages;
      var items = list.childNodes;
      var itemsArr = [];
      for (var i in items) {
          if (items[i].nodeType == 1) { // get rid of the whitespace text nodes
            itemsArr.push(items[i]);
          }
      }
      if(task == 'inst'){
        var b = title + '-alpha'
       $(a).children().first().remove()
       $(a).children().eq(1).remove()
        code = `<div><span onclick="sidebarSort('` + b + `')">sort</span></div>`
        itemsArr.sort(function(a, b) {
          return a.innerHTML == b.innerHTML
                  ? 0
                : (parseInt(b.firstElementChild.firstElementChild.innerHTML.replace('(', '').replace(')','')) > parseInt(a.firstElementChild.firstElementChild.innerHTML.replace('(', '').replace(')','')) ? 1 : -1);
        });
      }else{
        var b = title + '-inst'
        $(a).children().first().remove()
        $(a).children().eq(1).remove()
        code = `<div><span onclick="sidebarSort('` + b + `')">sort</span></div>`
        itemsArr.sort(function(a, b) {
          return a.innerHTML == b.innerHTML
                  ? 0
                  : (a.firstElementChild.innerHTML > b.firstElementChild.innerHTML ? 1 : -1);
        });
      }
      for (i = 0; i < itemsArr.length; ++i) {
        list.appendChild(itemsArr[i]);
      }
      $(a).prepend(code) 
    } else {
      var list = document.getElementById(title).nextElementSibling.firstElementChild;
      var items = list.childNodes;
      var itemsArr = [];
      for (var i in items) {
          if (items[i].nodeType == 1) { // get rid of the whitespace text nodes
            itemsArr.push(items[i]);
          }
      }
      if(task == 'inst'){
      a = document.getElementById(title);
      var b = title + '-alpha'
        $(a).children().first().remove()
        code = `<span onclick="sidebarSort('` + b + `')">sort</span>`
        $(a).append(code) 
        itemsArr.sort(function(a, b) {
          return a.innerHTML == b.innerHTML
                  ? 0
                  : (parseInt(b.firstElementChild.firstElementChild.innerHTML.replace('(', '').replace(')','')) > parseInt(a.firstElementChild.firstElementChild.innerHTML.replace('(', '').replace(')','')) ? 1 : -1);
        });
      }else{
        a = document.getElementById(title);
        var b = title + '-inst'
        $(a).children().first().remove()
        code = `<span onclick="sidebarSort('` + b + `')">sort</span>`
        $(a).append(code) 
        itemsArr.sort(function(x, y) {
          return x.innerHTML == y.innerHTML
                  ? 0
                  : (x.firstElementChild.innerHTML > y.firstElementChild.innerHTML ? 1 : -1);
        });
      }
      for (i = 0; i < itemsArr.length; ++i) {
        list.appendChild(itemsArr[i]);
      }
    }
    
    
  }else{
    // clear notifications
  }

}



function insertEmbed(iden, link){
  var card = document.getElementById(iden);
  var word = $(card).find('.watch').text() 
  if (word == 'Watch'){
    code = '<iframe class="EmbedContent" src="' + link + '" allowfullscreen></iframe>'
    // alert(link)
    $(card).find('.Embed').prepend(code)  
    // alert('1')
    $(card).find('.watch').text('Close Player')
    // alert('2')

  }else{
    $(card).find('.Embed').empty()
    $(card).find('.watch').text('Watch')

  }
}

function tocNav(item){
  // alert(item)
  var hs = document.getElementsByTagName('h2')
  for(i=0; i<hs.length; i++){
    if(hs[i].outerHTML.includes(item)){
      hs[i].scrollIntoView({ behavior: 'smooth', block: 'start' });
      break
    }
  }
  item = item.replaceAll("'", '"')
  var hs = document.querySelectorAll("[style*='text-align:Center']")
  for(i=0; i<hs.length; i++){
    if(hs[i].outerHTML.includes(item)){
      hs[i].scrollIntoView({ behavior: 'smooth', block: 'start' });
      break
    }
  }
  function searchelement(elementhtml){
    try{
      [...document.querySelectorAll("*")].forEach((ele)=>{
        if(ele.outerHTML == elementhtml){
          ele.scrollIntoView({ behavior: 'smooth', block: 'start' });
          // break
        }
      });

    }catch(err){alert(err)}

   }
  searchelement(item)
  var isMobile = document.getElementById('isMobile').name;
  if (isMobile == 'True'){
    mobileSwitch('search')

  }
}
function continue_reading(iden, direction){
  // alert('start')
  console.log('continue reading', iden)
  var card = document.getElementById(iden);
    if (direction == 'more'){
      // alert('more')
      try{
        // $(card).find('.hansardText').attr("style","max-height:none");
        // $(card).find('.hansardTextContent').attr("style","max-height:none");
        $(card).find('.Text').addClass('showFullText');
        $(card).find('.TextContent').addClass('showFullText');
        $(card).find('.fadeOut').remove()
        $(card).find('.TextContent').next().text("Read Less")
        $(card).find('.TextContent').next().attr("onclick","continue_reading('" + iden + "', 'less')");
        // alert('done')
      }catch(err){}
      // try{
      //   // alert('1')
      //   // $(card).find('.billSummary').attr("style","max-height:none");
      //   $(card).find('.billSummary').addClass('showFullText');
      //   $(card).find('.fadeOut').remove()
      //   // alert('2')
      //   // alert( $(card).find('.billSummary').next())
      //   $(card).find('.Details').next().text("Read Less")
      //   $(card).find('.Details').next().attr("onclick","continue_reading('" + iden + "', 'less')");
      //   // alert('done')
      // }catch(err){alert(err)}

    }else if (direction == 'less'){
      try{
        // $(card).find('.hansardText').attr("style","max-height:150px");
        // $(card).find('.hansardTextContent').attr("style","max-height:150px");
        $(card).find('.Text').removeClass('showFullText');
        $(card).find('.TextContent').removeClass('showFullText');
        $(card).find('.TextContent').next().text("Read More")
        $(card).find('.TextContent').next().attr("onclick","continue_reading('" + iden + "', 'more')");
        var text = card.getElementsByClassName('TextContent')[0];
        fade = "<div class='fadeOut'></div>"
        $(text).append(fade) 
        card.scrollIntoView({ behavior: 'smooth', block: 'start' });
      }catch(err){}
      // try{
      //   // $(card).find('.billSummary').attr("style","max-height:150px");
      //   $(card).find('.billSummary').toggleClass('showFullText');
      //   $(card).find('.Details').next().text("Read More")
      //   $(card).find('.Details').next().attr("onclick","continue_reading('" + iden + "', 'more')");
      //   var text = card.getElementsByClassName('billSummary')[0];
      //   fade = "<div class='fadeOut'></div>"
      //   $(text).append(fade) 
      //   card.scrollIntoView({ behavior: 'smooth', block: 'start' });
      // }catch(err){}
    }else{
      $.get('/utils/continue_reading/' + iden + '/?topic=' + direction, function(data){
        $(card).find('.Terms').text("")
        $(card).find('.Terms').append(data)
        $(card).find('.Terms').next().text("")
        $(card).find('.readMoreTerms').text("")
      });

    }
  // }
}
function show_all(iden, item){
  // alert(item)
  try{
      var subscribers = document.getElementsByClassName('showAllCentered');
      for(i=0; i<subscribers.length; i++){
          subscribers[i].outerHTML = "";
      }
  }catch(err){alert(err)}
  if(item != 'function close() { [native code] }'){
      $.get('/utils/show_all/' + iden + '/' + item, function(data) {
          // alert(data)
          if(item == 'terms'){
            title = 'All Topics'
          }else{
            title = "All Speakers"
          }
          code = '<div class="showAllCentered"><div id="showAllClose" onclick="show_all(100, close)">Close</div><div id="title">' + title + '</div>' + data  + '</div>'
          $('#container').prepend(code)
      });
  }
};
function login() {
  // var username = localStorage.getItem("username");
  // var dom = document.getElementById('userName');
  // dom.innerHTML = "<a href='/user/" + username + "'><span style='color:#b78e12'>V</span><span style='color:gray'>/</span>" + username + "</a>"
  // var settingsLink = document.getElementById('settingsLink')
  // settingsLink.innerHTML = "<a href='/user/settings'>Settings</a>"
  // var logoutLink = document.getElementById('logoutLink')
  // logoutLink.innerHTML = "<span style='cursor:pointer' onclick='logout()'>Log Out</span>"
  index = document.getElementById('navigation');
  index.innerHTML = '<div class="lds-dual-ring"></div>';
  closeModal();
  $.ajax({
    // type:'POST',
    url:'/accounts/get_index',
    // data: data,
    success:function(response){
      // console.log('received response')
      // index = document.getElementById('index');
      // index.outerHTML = response;
      location.reload()
      // console.log('done')
    },
    // error: function (xhr, ajaxOptions, thrownError) {
    //   field3.innerHTML = 'Failed to reach server';
    // } 
  });
}
function logout(target) {
  console.log('logout')
  // console.log(target)
  // userData, userArrayData = get_stored_userData()
  // console.log(userData.must_rename)

  $.ajax({
    url: target,
    success: function (data) {
      localStorage.setItem('bioPrivKey', null);
      localStorage.setItem('bioPubKey', null);
      localStorage.setItem('passPrivKey', null);
      localStorage.setItem('passPubKey', null);
      localStorage.setItem('username', null);
      localStorage.setItem('userData', null);
      localStorage.setItem('pass', null);
      localStorage.setItem('display_name', null);
      // localStorage.setItem('userData', null);
      location.reload()
      // index = document.getElementById('index');
      // index.outerHTML = data;
      // console.log('logout2')
      // var dom = document.getElementById('userName');
      // console.log(dom)
      // dom.innerHTML = `<span onclick="modalPopUp('Authenticate', '/accounts/authenticate')">Authenticate</span>`;
      
      // console.log('logout3')
      // var settingsLink = document.getElementById('settingsLink')
      // settingsLink.innerHTML = ""
      // console.log('logout4')
      // var logoutLink = document.getElementById('logoutLink')
      // logoutLink.innerHTML = ""
    },
    error: function (xhr, ajaxOptions, thrownError) {
      alert('Failed to reach server');
    } 
  });
}
function generatePassword() {
  var length = 20,
      charset = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!@#$%&",
      retVal = "";
  for (var i = 0, n = charset.length; i < length; ++i) {
      retVal += charset.charAt(Math.floor(Math.random() * n));
  }
  var form = document.getElementById("modalForm");
  form.elements["password"].value = retVal;
}
function displayPassword() {
    var clicker = document.getElementById("passwordVisibility");
    if (clicker.innerHTML == 'visibility_off') {
        clicker.innerHTML = 'visibility'
        var x = document.getElementById("password");
        x.type = "text";
    } else {
        clicker.innerHTML = 'visibility_off'
        var x = document.getElementById("password");
        x.type = "password";

    }
}
function modalPopUp(title, target){
  closeModal()
  m = document.getElementsByClassName('modalWidget')[0]
  modal = $('.modalWidget');
  code = '<div class="lds-dual-ring"></div>'
  m.querySelector("#modalContent").innerHTML = code;
  m.querySelector("#modalTitle").innerHTML = title;
  modal.addClass('show');
  // console.log(localStorage.getItem('userData'))
  try {
    userData = JSON.parse(localStorage.getItem('userData'))
    target = target + '?userId=' + userData['id']
  } catch(err) {}
  console.log(target)
  $.ajax({
    url: target,
    success: function (data) {
      // var head = document.getElementsByTagName('head')[0],
      //     script = document.createElement('script');
      // script.src = 'https://unpkg.com/@simplewebauthn/browser@9.0.1/dist/bundle/index.umd.min.js';
      // head.appendChild(script);
      // parsedData = $.parseHTML(data);
      // var new_cards =  $(parsedData);
      var html = $('<html>').html(data);
      // var instruct = html.find('instruction');
      // console.log(instruct)
      // var new_title = $('<title>').html(data).text();
      // // new_title = data.getElementByTagName('title').text
      // console.log(new_title)
      var new_title = html.find('title').text();
      m.querySelector("#modalTitle").innerHTML = new_title;
      // new_script = data.getElementByTagName('script')
      
      var instruction = html.find('#instruction').attr('value');
      m.querySelector("#modalContent").innerHTML = data;
      enact_user_instruction(instruction, {})
    },
    error: function (xhr, ajaxOptions, thrownError) {
      m.querySelector("#modalContent").innerHTML = 'Failed to reach server';
    } 
  });
}

function closeModal(){
  modal = $('.modalWidget');
  modal.removeClass('show');
}
function removeModalClose(){
  btn = document.getElementsByClassName('modalWidgetClose')[0]
  btn.setAttribute('onclick','')
  btn.innerHTML = '-'
}
function onFormSubmit() {
  event.preventDefault();
}
async function hashMessage(message) {
  const encoder = new TextEncoder();
  const data = encoder.encode(message);

  const buffer = await crypto.subtle.digest('SHA-256', data);
  const hashArray = Array.from(new Uint8Array(buffer));
  const hashHex = hashArray.map(byte => byte.toString(16).padStart(2, '0')).join('');

  return hashHex;
}

async function sign(data, privKey=null, pubKey=null) {
  // receives parsed data
  console.log('signing...')
    // console.log(pubKey)
  if (pubKey == null || privKey == 'null') {
    var pubKey = localStorage.getItem("passPubKey");
    // console.log('pubKey11aaa',pubKey)
  }
  // console.log('privKey11aaa',privKey)
  if (privKey == null || privKey == 'null') {
    var privKey = localStorage.getItem("passPrivKey");
    // console.log('privKey11',privKey)
    if (privKey == null || privKey == 'null') {
      var privKey = localStorage.getItem("bioPrivKey");
      // console.log('privKey1122',privKey)
    if (privKey == null || privKey == 'null') {
        console.log('privKey nuill')
        return null;
      }
    }
  }
  

  data = JSON.stringify(data)
  // console.log('data',data)
  // console.log('privKey',privKey)
  const curve = new elliptic.ec('secp256k1');
  let keyPair = curve.keyFromPrivate(privKey);
  hashed_data = await hashMessage(data)
  const signature = keyPair.sign(hashed_data, { canonical: true });
  const sig = signature.toDER('hex');
  
  parsedData = JSON.parse(data)
  // console.log('next')
  parsedData.publicKey = pubKey
  parsedData.signature = sig
  console.log('sig',sig)
  return parsedData
}
async function verify(data, signature, pubKey) {
  console.log('verifing...')
  const curve = new elliptic.ec('secp256k1');
  let importedPublicKey = curve.keyFromPublic(pubKey, 'hex')
  hashed_data = await hashMessage(data)
  const isVerified = curve.verify(hashed_data, signature, importedPublicKey);   
  console.log('isVerified',isVerified)  
  return isVerified;
}

async function verifyUserData(userData, localData=false) {
  // receives json.stringify(data)
  // x = localStorage.getItem('userData')
  // console.log('x',x)
  console.log('verify userData')
  // if not localData
  // data = expand_received_userData(userData)
  // userData = data[0]
  // userArrayData = data[1]
  // console.log(JSON.stringify(userData))
  // // console.log('userData.publicKey22',userData.publicKey)
  // receivedPubKey = userData.publicKey
  // if (receivedPubKey == null || receivedPubKey == 'null') {
  //   console.log('return1')
  //   return false
  // }
  // var localPubKey = localStorage.getItem("passPubKey");
  // if (receivedPubKey != localPubKey) {
  //   var localPubKey = localStorage.getItem("bioPrivKey");
  //   if (receivedPubKey != localPubKey) {
  //     console.log('return2')
  //     return false;
  //   }
  // }
  // console.log('receivedPubKey',receivedPubKey)
  // console.log('localPubKey',localPubKey)
  // var sig = userData.signature
  // console.log('sig1',sig)
  // // var sig = '304402202bfd309ba9631a608943ff7869332fcbe4ccf7535a0304b2cadf05118505ee7402205005986eeaec6acd14b10af020d2a1d0aec7f49c3562f54633df32e1f8779c57'
  // // console.log('sig2',sig)

  // delete userData['signature']
  // delete userData['publicKey']
  // data = get_userData_for_sign_return(userData, userArrayData)

  // parsedData = JSON.parse(userData)

  // console.log('data-to-verify',JSON.stringify(parsedData))
  // var is_valid = await verify(data, sig, localPubKey)




  // d = expand_received_userData(userData)
  // // d = get_stored_userData()
  // // parsedData = get_userData_for_sign_return(d[0], d[1])
  // userData = d[0]
  // userArrayData = d[1]
  userData = JSON.parse(userData)

  receivedPubKey = userData.publicKey
  if (receivedPubKey == null || receivedPubKey == 'null') {
    console.log('return1')
    return false
  }
  var localPubKey = localStorage.getItem("passPubKey");
  if (receivedPubKey != localPubKey) {
    var localPubKey = localStorage.getItem("bioPrivKey");
    if (receivedPubKey != localPubKey) {
      console.log('return2')
      return false;
    }
  }

  userData.must_rename = false
  var s = userData.signature
  // var pk = parsedData.publicKey
  delete userData.publicKey
  delete userData.signature
  // parsedData = get_userData_for_sign_return(userData, userArrayData)
  // console.log('signed_data1111',JSON.stringify(parsedData))
  json = JSON.stringify(userData)

  is_valid = await verify(json, s, localPubKey)


  
  return is_valid
}
// function get_private_key(seed) {
//   const curve = new elliptic.ec('secp256k1');
//   let keyPair = curve.keyFromPrivate(seed);
//   // let privKey = keyPair.getPrivate("hex");  
//   return keyPair;
// }
async function getKeyPair(seed) {
    console.log('get keypair')
    console.log("seed:", seed);
    const curve = new elliptic.ec('secp256k1');
    let keyPair = curve.keyFromPrivate(seed);
    let privKey = keyPair.getPrivate("hex");    
    console.log('privKey',privKey);
    // localStorage.setItem('privKey', privKey);
    // let keyPair2 = curve.keyFromPrivate(privKey);
    // console.log('privKey2',keyPair2.getPrivate("hex"));
    const publicKey = keyPair.getPublic();
    const publicKeyHex = keyPair.getPublic().encode('hex');
    console.log("Public Key:", publicKeyHex);

  //   const msg = "testmessage1111";
  //   hashed_data = await hashMessage(msg)
  //   console.log('msg',hashed_data);
  //   const signature = keyPair.sign(hashed_data, { canonical: true });
  //   console.log("Signature:", signature.toDER('hex'));
  // let importedPublicKey = curve.keyFromPublic(publicKeyHex, 'hex')

  //   const isVerified = curve.verify(hashed_data, signature, importedPublicKey);     
  //   console.log("is valid:", isVerified);
    
    return [privKey, publicKeyHex];
}
function makeAjaxRequest(data, link, item) {
  console.log('makeAjax request')
  return new Promise((resolve, reject) => {
    $.ajax({
      type: 'POST',
      url: link,
      data: data,
      success: function(response) {
        // console.log(item)
        resolve({ response, item });
      },
      error: function(xhr, status, error) {
        console.lgog('prob1')
        reject(error);
      }
    });
  });
}
async function handleLoginResponse({ response, item }) {
  console.log('handleLoginResponse')
  var password = item
  // console.log(password)
  // console.log(response);
  // console.log(data);
  // console.log(password)
  // $.ajax({
  //   type:'POST',
  //   url:'/accounts/get_user',
  //   data: data,
  //   success: async function(response){
      var field3 = document.getElementById('field3');
      console.log('1')
      message = response['message'];
      console.log(message)
      // receivedUserData = JSON.parse(response['userData']);
      // console.log('11111')
      // d = expand_received_userData(response['userData'])
      // receivedUserData = d[0]
      // receivedUserArrayData = d[1]
      receivedUserData = JSON.parse(response['userData'])
      // console.log('2222')
      seed = password + receivedUserData['id'] + receivedUserData['id']
      console.log(seed)
      keyPair = await getKeyPair(seed)
      privKey = keyPair[0]
      pubKey = keyPair[1]

      console.log('keypair', keyPair)
      const postData = {};
      // data['userData'] = userData;
      if (message == 'User not found') {
        postData['publicKey'] = keyPair[1]
        console.log('sign walletData')
        walletData = JSON.parse(response['walletData']);
        walletData = await sign(walletData, privKey=keyPair[0], pubKey=keyPair[1])
        // walletData.signature = walletSignature
        postData['walletData'] = JSON.stringify(walletData);

        console.log('sign upkData')
        upkData = JSON.parse(response['upkData']);
        upkData = await sign(upkData, privKey=keyPair[0], pubKey=keyPair[1])
        // upkData.signature = upkSignature

        postData['upkData'] = JSON.stringify(upkData);

        userData = receivedUserData
        // userArrayData = receivedUserArrayData
        // if (userData['id'] == 'd704bb87a7444b0ab304fd1566ee7aba') {
        // userData['is_superuser'] = true
        // // userData['is_admin'] = true
        // userData['is_staff'] = true
          // userData['username'] = 'd704bb87a7444b0ab304fd1566ee7aba'
        // }
        console.log('sign sign_userData')
        userData = await sign_userData(userData, privKey=keyPair[0], pubKey=keyPair[1])
      } else if ((message == 'User found')) {
        // get_userData_for_sign_return(userData, userArrayData)
        // verify recevied userData against locally stored userdata
        // processedReceivedUserData = get_userData_for_sign_return(receivedUserData, receivedUserArrayData)
        is_valid = await verifyUserData(response['userData'])
        console.log('userdata verify:', is_valid)
        userData = get_stored_userData();
        console.log('stored data', userData)
        if (userData != null && userData != 'null') {
          if (userData['id'] == receivedUserData['id']) {
            if (Date(userData['last_updated']) < Date(receivedUserData['last_updated'])) {
              if (is_valid) {
                // userData was updated on a different server more recently than this device
                userData = receivedUserData
                // userArrayData = receivedUserArrayData
                console.log('updated userData from server')
              } else {
                // received data is not valid
              }
            } else {
              // device userData is up to date
            }
          } else {
            // receivedUserData does not match local userData
          }
        } else { 
          // local userData not found
          userData = receivedUserData
          // userArrayData = receivedUserArrayData
          console.log('updated userData from server')
        }
        // sign_userData(userData, userArrayData)
        postData['publicKey'] = keyPair[1];
        console.log('sign sign_userData', userData)
        userData = await sign(userData, privKey=privKey, pubKey=pubKey)
      }
      // console.log(postData['publicKey'])
      // console.log('go')
      // console.log(keyPair[0])
      // console.log()
      // console.log('sign sign_userData')
      // userArrayData.interest_array.push("Rex Murphy Lives")
      // userArrayData.interest_array.push("Rex Murphy 2")
      // userArrayData.follow_post_id_array.push("a0abd5ec79ec5247b6a86a82b28c6d31")
      // userArrayData.follow_post_id_array.push("1d1e9be76e5d360af1e26b162b6c8d51")
      // userArrayData.follow_topic_array.push("Rex Murphy 10")
      // userArrayData.follow_topic_array.push('test')
      // userData = await sign_userData(userData, privKey=keyPair[0], pubKey=keyPair[1])
      // userData = await sign(userData, privKey=keyPair[0], pubKey=keyPair[1])
      // console.log('sig')
      // console.log(signature)
      // // console.log(userData)
      // // parsedData = JSON.parse(userData)
      // userData.signature = signature
      // console.log('2')
      // console.log(JSON.stringify(userData))
      postData['userData'] = JSON.stringify(userData);
      console.log('send to receive user')
      $.ajax({
        type:'POST',
        url:'/accounts/receive_user_login',
        data: postData,
        success:function(response){
          console.log(response)
          if (response['message'] == 'Invalid Password') {
              field3.innerHTML = 'Username does not match password'
          } else if (response['message'] == 'Valid Username and Password'||response['message'] == 'User Created') {
            console.log('proceed to login')
            // console.log(JSON.stringify(response['userData']))
            localStorage.setItem('passPrivKey', keyPair[0]);
            localStorage.setItem('passPubKey', keyPair[1]);
            localStorage.setItem('pass', password);
            localStorage.setItem('display_name', JSON.parse(response['userData'])['display_name']);
            localStorage.setItem('userData', JSON.stringify(userData));
            login()
            // modalPopUp('Select Region', '/accounts/get_country_modal')
          } else {
            field3.innerHTML = response['message']
          }
        },
        error: function (xhr, ajaxOptions, thrownError) {
          console.log('prob2')
          field3.innerHTML = 'Failed to reach server';
        } 
      });
      // } else if ((message == 'User found')) {
      //   console.log('else')
      //   // data = JSON.parse(response['userData']);
      //   // data['csrfmiddlewaretoken'] = csrf;
      //   const id = data['id'];
        
      //   seed = password + id + id;
      //   console.log(seed)
      //   keyPair = get_private_key(seed);
      //   // console.log(keyPair)
      //   // const publicKey = keyPair.getPublic();
      //   const publicKeyHex = keyPair.getPublic().encode('hex');
      //   data['registered_public_key'] = publicKeyHex;
      //   console.log(publicKeyHex)
      //   $.ajax({
      //     type:'POST',
      //     url:'/accounts/receive_user',
      //     data: data,
      //     success:function(response){
      //       if (response['message'] == 'Invalid Password') {
      //         field3.innerHTML = 'Username does not match password'
      //       } else if (response['message'] == 'Valid Username and Password') {
      //         console.log('proceed to login')
      //         // console.log(JSON.stringify(response['userData']))
      //         localStorage.setItem('passPrivKey', keyPair.getPrivate("hex"));
      //         localStorage.setItem('passPubKey', publicKeyHex);
      //         localStorage.setItem('username', data['username']);
      //         localStorage.setItem('userData', response['userData']);
      //         login()
      //       }
      //       // localStorage.setItem('passKey', passKey);
      //       // localStorage.setItem('pubKey', pubKey);
      //       // localStorage.setItem('username', username);

      //     },
      //     error: function (xhr, ajaxOptions, thrownError) {
      //       field3.innerHTML = 'Failed to reach server';
      //     } 
      //   });
      // }
      // localStorage.setItem('passKey', passKey);
      // localStorage.setItem('pubKey', pubKey);
      // localStorage.setItem('username', username);

    // },
  // });
}
async function passwordAuthenticate(user_data, wallet_data, upk_data, csrf) {
  // console.log(csrf)
  // logout()
  // const json_data = JSON.stringify(user_data)
  var form = document.getElementById("modalForm");
  var username = form.elements["username"].value;
  var password = form.elements["password"].value;
  // console.log("Username:", username);
  // console.log("Password:", password);
  var field0 = document.getElementById('field0');
  if (username == '') {
      field0.innerHTML = 'Please enter a username'
  }else if (password == '') {
      field0.innerHTML = 'Please enter a password'
  } else if (password.length < 8) {
    field0.innerHTML = 'Please enter a longer password'
  } else {
    const data = user_data;
    data['display_name'] = username
    data['csrfmiddlewaretoken'] = csrf
    // console.log('/accounts/get_user/')
    makeAjaxRequest(data, '/accounts/get_user_login', password)
      .then(handleLoginResponse)
      .catch(error => {
        console.error('There was a problem with the AJAX request:', error);
    });
    
      
  }
}
async function renameUser() {
    
  // const json_data = JSON.stringify(user_data)
  var form = document.getElementById("modalForm");
  var username = form.elements["username"].value;
  // var password = form.elements["password"].value;
  // console.log("Username:", username);
  // console.log("Password:", password);
  var field2 = document.getElementById('field2');
  if (username == '') {
    field2.innerHTML = 'Please enter a username'
  } else {
    // parsedData = JSON.parse(userData)
    d = get_stored_userData()
    userData = d[0]
    userArrayData = d[1]
    userData.display_name = username
    userData.must_rename = false
    userData = get_userData_for_sign_return(userData, userArrayData)
    signedData = await sign(userData)
    const data = {};
    // data['display_name'] = username
    // data['must_rename'] = 'False'
    data['userData'] = JSON.stringify(signedData);
    // data['signature'] = signature
    // data['csrfmiddlewaretoken'] = csrf
    $.ajax({
      type:'POST',
      url:'/accounts/receive_rename',
      data: postData,
      success:function(response){
        console.log(response)
        if (response['message'] == 'Username taken') {
            field2.innerHTML = 'Username not available'
        } else if (response['message'] == 'Success') {
        //     field3.innerHTML = 'Username does not match password'
        // } else if (response['message'] == 'Valid Username and Password'||response['message'] == 'User Created') {
          // console.log('proceed to login')
          // console.log(JSON.stringify(response['userData']))
          // localStorage.setItem('passPrivKey', keyPair[0]);
          // localStorage.setItem('passPubKey', keyPair[1]);
          localStorage.setItem('display_name', username);
          localStorage.setItem('userData', JSON.stringify(signedData));
          // login()
          location.reload()
          // modalPopUp('Select Region', '/accounts/get_country_modal')
        } else {
          field2.innerHTML = response['message']
        }
      },
      error: function (xhr, ajaxOptions, thrownError) {
        console.log('prob2')
        field2.innerHTML = 'Failed to reach server';
      } 
    });
  }
}
// function parseData(data) {
//   console.log('parse data')
//   parsedData = JSON.parse(data)
//   var result = 
//   for (i in parsedData) {
//     var x = " '" + parsedData[i] + "'"
//     result["'" + i + "'"] = x;
//   }
//   console.log(result)
//   return result
// }
async function handleSigningResponse(userData) {
  console.log('handle sign response')
  if (userData) {
    // console.log(userData)
      parsedData = JSON.parse(userData)
      parsedData = await sign(parsedData)
      // console.log('passed sig')
      // parsedData.signature = signature
      result = JSON.stringify(parsedData)
  } else {
    result = null
  }
  return new Promise((resolve, reject) => {
    resolve(result)
  });
}

// not used
async function handleSetRegionResponse(userData) {
  // console.log(userData)
  const data = {'userData': userData};
  // console.log(data)
  // console.log('sending')
  $.ajax({
    type:'POST',
    url:'/accounts/set_user_data',
    data: data,
    success:function(response){
      if (response['message'] == 'success') {
        // console.log('success')
        // localStorage.setItem('passPrivKey', passKey);
        // localStorage.setItem('passPubKey', pubKey);
        // localStorage.setItem('username', data['username']);
        localStorage.setItem('userData', userData);
        if (window.location.href.indexOf("/region") > -1) {
          // window.location.href = `/region?${queryString}`;
          location.reload()
        } else {
          closeModal();
        }
      } else {
        field3.innerHTML = response['message']
      }
    },
    error: function (xhr, ajaxOptions, thrownError) {
      field3.innerHTML = 'Failed to reach server';
    } 
  });
}
async function setRegionModal(csrf) {
  // console.log(csrf)
  // const json_data = JSON.stringify(user_data)
  var form = document.getElementById("modalForm");
  var address = form.elements["address"].value;
  // var password = form.elements["password"].value;
  // console.log("Username:", username);
  // console.log("Password:", password);
  var field2 = document.getElementById('field2');
  field2.innerHTML = ''
  field3.innerHTML = ''
  if (address == '') {
      field2.innerHTML = 'Please enter an address'
  // }else if (password == '') {
  //     field0.innerHTML = 'Please enter a password'
  // } else if (password.length < 8) {
  //   field0.innerHTML = 'Please enter a longer password'
  } else {
    // user_id = JSON.parse(localStorage.getItem('userData'))['id']
    const data = {};
    country = document.getElementById('field3');
    // console.log(user_id)
    // console.log(country)
    // console.log(country.getAttribute("value"))
    // data['userId'] = user_id;
    data['country'] = country.getAttribute("value");
    data['address'] = address
    data['csrfmiddlewaretoken'] = csrf
    // const utcStr = new Date().toUTCString()
    // Mon, 12 Sep 2022 18:15:18 GMT
    // signature = await sign(utcStr)
    // console.log(signature)
    // data['regionSetDate'] = utcStr
    // data['setDateSig'] = signature
    // console.log('/accounts/set_region_modal')
    $.ajax({
      type: 'POST',
      data: data,
      url: '/accounts/run_region_modal',
      success: function (response) {
        if (response['message'] == 'Failed to set region') {
          field2.innerHTML = response['message']
        } else {
          responseData = response['userData']
          response_json = JSON.parse(responseData)

          userData, userArrayData = get_stored_userData()
          userData.Country_obj = response_json['country_id']
          userData.Federal_District_obj = response_json['federalDistrict_id']
          userData.ProvState_obj = response_json['provState_id']
          userData.ProvState_District_obj = response_json['provStateDistrict_id']
          userData.Greater_Municipality_obj = response_json['greaterMunicipality_id']
          userData.Greater_Municipal_District_obj = response_json['greaterMunicipalityDistrict_id']
          userData.Municipality_obj = response_json['municipality_id']
          userData.Municipal_District_obj = response_json['ward_id']

          const currentDate = new Date();
          const isoString = currentDate.toISOString();
          userData.region_set_date = isoString
          signedUserData = sign_userData(userData, userArrayData)
          return_signed_userData(signedUserData)
          if (window.location.href.indexOf("/region") > -1) {
            // window.location.href = `/region?${queryString}`;
            location.reload()
          } else {
            closeModal();
          }
          // console.log(userData)
          // signature = await sign(JSON.stringify(userData))
          // handleSigningResponse(userData)
          //   .then(handleSetRegionResponse)
          //   .catch(error => {
          //     console.error('There was a problem with the AJAX request:', error);
          // });
          // regionData = response['regionData']
          // localStorage.setItem('regionData', regionData);
          // if (window.location.href.indexOf("/region") > -1) {
          //     const responseData = {
          //       // userId: user_id,
          //       // countryId: regionData['country_id'],
          //       // provStateId: regionData['provState_id'],
          //       // regionalMunicipalId: regionData['regionalMunicipality_id'],
          //       // municipalId: regionData['municipality_id'],
          //       // federalDistrictId: regionData['federalDistrict_id'],
          //       // federalDistrictName: regionData['federalDistrict_name'],
          //       // provStateDistrictId: regionData['provStateDistrict_id'],
          //       // regionalMunicipalityDistrictId: regionData['regionalMunicipalityDistrict_id'],
          //       // wardId: regionData['ward_id'],
          //     };
          //     const queryString = new URLSearchParams(responseData).toString();
          //   window.location.href = `/region?${queryString}`;
          // //   location.reload()
          // } else {
          // //   index = document.getElementById('navigation');
          // //   index.innerHTML = '<div class="lds-dual-ring"></div>';
          // //   index = document.getElementById('index');
          // //   index.outerHTML = response;
          //   closeModal();
          // }
        }
      },
      error: function (xhr, ajaxOptions, thrownError) {
        m.querySelector("#modalContent").innerHTML = 'Failed to reach server';
      } 
    });
    
      
  }
}

$('#firstPane').scroll(function(){
  // alert('topics')
  $('#firstPane').addClass('showFullText');
  $('#secondPane').removeClass('showFullText');
  $('#thirdPane').removeClass('showFullText');
  $('#fourthPane').removeClass('showFullText');
})
$('#secondPane').scroll(function(){
  // alert('second')
  $('#firstPane').removeClass('showFullText');
  $('#secondPane').addClass('showFullText');
  $('#thirdPane').removeClass('showFullText');
  $('#fourthPane').removeClass('showFullText');

})
$('#thirdPane').scroll(function(){
  // alert('speakers3')
  $('#firstPane').removeClass('showFullText');
  $('#secondPane').removeClass('showFullText');
  $('#thirdPane').addClass('showFullText');
  $('#fourthPane').removeClass('showFullText');

})
$('#fourthPane').scroll(function(){
  // alert('speakers3')
  $('#thirdPane').removeClass('showFullText');
  $('#firstPane').removeClass('showFullText');
  $('#secondPane').removeClass('showFullText');
  $('#fourthPane').addClass('showFullText');
})

// function citizenry(){
//   alert('start')
//   $('#citizenry').addClass('showFullText');
//   $('#council').removeClass('showFullText');
//   $('#assembly').removeClass('showFullText');
//   $('#house').removeClass('showFullText');
//   $('#senate').removeClass('showFullText');
// }
// function council(){
//   $('#citizenry').removeClass('showFullText');
//   $('#council').addClass('showFullText');
//   $('#assembly').removeClass('showFullText');
//   $('#house').removeClass('showFullText');
//   $('#senate').removeClass('showFullText');
// }
// function assembly(){
//   $('#citizenry').removeClass('showFullText');
//   $('#council').removeClass('showFullText');
//   $('#assembly').addClass('showFullText');
//   $('#house').removeClass('showFullText');
//   $('#senate').removeClass('showFullText');
// }
// function house(){
//   $('#citizenry').removeClass('showFullText');
//   $('#council').removeClass('showFullText');
//   $('#assembly').removeClass('showFullText');
//   $('#house').addClass('showFullText');
//   $('#senate').removeClass('showFullText');
// }
// function senate(){
//   $('#citizenry').removeClass('showFullText');
//   $('#council').removeClass('showFullText');
//   $('#assembly').removeClass('showFullText');
//   $('#house').removeClass('showFullText');
//   $('#senate').addClass('showFullText');
// }
// $('#citizenry').scroll(function(){
//   alert('1')
//   citizenry()
// })
// $('#council').scroll(function(){
//   council()
// })
// $('#assembly').scroll(function(){
//   assembly()
// })
// $('#house').scroll(function(){
//   house()
// })
// $('#senate').scroll(function(){
//   senate()
// })


function adjustSidebar($el){
  var con = document.getElementById('container');
  var rect = con.getBoundingClientRect();
  var right = rect.left + 1
  right = right.toString()
  right = right + 'px'
$el.css({'position': 'fixed', 'top': '0px', 'right': right }); 
$el.addClass('fixed');
}
function adjustNavBar($navbar){
  var con = document.getElementById('container');
    var rect = con.getBoundingClientRect();
    var right = rect.left + 211
    right = right.toString()
    right = right + 'px'
    $navbar.css({'position': 'fixed',  'top': '-1', 'right': right }); 
    $navbar.addClass('fixed');
}

$(window).scroll(function(){ 
  var topics = $('#topics');
  var speakers = $('#speakers');
  var isMobile = document.getElementById('isMobile').name;
    // alert(isMobile)
  if (isMobile != 'True'){
  let window = innerHeight;

  var $navbar = $('#navBar'); 
  // alert($navbar.css('position'))
  // let window = innerHeight;
  var isPositionFixed = ($navbar.css('position') == 'fixed');
  if ($(this).scrollTop() > 72 && !isPositionFixed){
    adjustNavBar($navbar)
  }else if ($(this).scrollTop() < 72 && isPositionFixed){
    var con = document.getElementById('container');
    var rect = con.getBoundingClientRect();
    var right = rect.left 
    right = right.toString()
    right = right + 'px'
    $navbar.css({'position': 'absolute', 'top':'67.5', 'right': '-0.5' }); 
    $navbar.removeClass('fixed');
  } 
    var $el = $('#sidebar'); 
    // alert($el.html())
    let box = document.querySelector('#sidebar');
    var height = box.offsetHeight;
    // var difference = height - window
    if (height < window){
      // alert('1')
      difference = 100
      var isPositionFixed = ($el.css('position') == 'fixed');
      if ($(this).scrollTop() > 100 && !isPositionFixed){
        adjustSidebar($el)

      }
    }else{
      // alert(difference)
      // difference = height - window + 100
      var isPositionFixed = ($el.css('position') == 'fixed');
      if ($(this).scrollTop() > 100 && !isPositionFixed){
        adjustSidebar($el)
      }
      // alert(difference)
      // difference = height - window + 100
      // var isPositionFixed = ($el.css('position') == 'fixed');
      // if ($(this).scrollTop() > difference && !isPositionFixed){
      //     var con = document.getElementById('container');
      //     var rect = con.getBoundingClientRect();
      //     var right = rect.left - 0
      //     right = right.toString()
      //     right = right + 'px'
      //   $el.css({'position': 'fixed', 'top': window-height-1, 'right': right }); 
      // }
    }
    // alert($(this).scrollTop() )
    // alert(difference)
    if ($(this).scrollTop() < 100 && isPositionFixed){
      $el.css({'position': 'absolute', 'top': '100px', 'right': '1px'}); 
      $el.removeClass('fixed');
    } 
  }
  
  });


//     var isPositionFixed = ($el.css('position') == 'fixed');
//     if ($(this).scrollTop() > 50 && !isPositionFixed){ 
//       $el.css({'position': 'fixed', 'top': '-1px', 'right': '10%'}); 
//     //   alert('sticky')
//     }
//     if ($(this).scrollTop() < 50 && isPositionFixed){
//       $el.css({'position': 'absolute', 'top': '50px', 'right': '0px'}); 
//     //   alert('not sticky')
//     } 
//   });

function shorten_text(cards){
  // alert(cards.length)
  var isMobile = document.getElementById('isMobile').name;
  // var isXRequest = document.getElementById('isXRequest').name;
  // alert('shorten text')
  try{
    for(i=0; i<cards.length; i++){
      var text = cards[i].getElementsByClassName('Text')[0];
      try{
        let child = text.parentNode.querySelector('.fadeOut');
        var height = text.offsetHeight;
        // alert(height)
        if (isMobile == 'True' && height >= 300 && child == null || isMobile == 'False' && height >= 150 && child == null){
          iden = cards[i].id
          // alert(iden)
          code = `<div class='readMore' onclick='continue_reading("` + iden + `", "more")'>Read More</div>`
          $(text).parent().after(code) 
          fade = `<div class='fadeOut' onclick='continue_reading("` + iden + `", "more")'></div>`
          $(text).parent().append(fade) 
          // alert('done')
        
        }
      }catch(err){}
    }
  }catch(err){}
}
// not used
function get_userData_for_sign_return(userData, userArrayData) {
  // userdata must be processed before sign and before return to server because some fields contain arrays which do not parse properly
  console.log('get_userData_for_sign_return')
  // console.log(userData)
  // console.log(userArrayData.interest_array)
  // userData.interest_array = userArrayData.interest_array
  // userData.follow_post_id_array = userArrayData.follow_post_id_array
  // userData.follow_topic_array = userArrayData.follow_topic_array

  Object.keys(userData).forEach(field => {
    if (field.endsWith('_array')) {
      // console.log('array')
      // console.log(userArrayData[field])
      // console.log(userArrayData[field].replace(/"/g, "'"))
      // userData[field] = userArrayData[field];
        userArrayData[field] = userData[field];
        // userData[field] = JSON.stringify(userArrayData[field]).replace(/"/g, "'");
    }
  });
  // console.log('done1')
  // Object.keys(userArrayData).forEach(field => {
  //   // userData[field] = "['" + userArrayData[field].map(item => item.replace(/'/g, "\\'")).join("', '") + "']";
  //   userData[field] = userArrayData[field];
  // });
  // const arrayString = "['" + userArrayData[field].map(item => item.replace(/'/g, "\\'")).join("', '") + "']";
  // console.log(JSON.stringify(userData))
  return userData

}
async function sign_userData(userData, privKey=null, pubKey=null) {
  console.log('sign and return userdata')
  // console.log(userData)
  // console.log(userArrayData)
  // Object.keys(userArrayData).forEach(field => {
  //   // userData[field] = "['" + userArrayData[field].map(item => item.replace(/'/g, "\\'")).join("', '") + "']";
  //   userData[field] = userArrayData[field];
  // });
  // // const arrayString = "['" + userArrayData[field].map(item => item.replace(/'/g, "\\'")).join("', '") + "']";
  // console.log(userData)
  // if (parsedData['object_type'] == 'User') {
  const currentDate = new Date();
  const isoString = currentDate.toISOString();
  userData.last_updated = formatDateToDjango(isoString)
  delete userData['signature']
  delete userData['publicKey']

  // parsedData = JSON.parse(userData)
    // parsedData.must_rename = false
    // console.log('must_rename',parsedData.must_rename)
    // delete parsedData.publicKey
    // delete parsedData.signature
    // signed_data = await sign(parsedData)

  // console.log('next11')
    // localStorage.setItem('userData', JSON.stringify(parsedData));
    // get_userData_for_sign_return(userData, userArrayData)
  // }
  // userData = get_userData_for_sign_return(userData, userArrayData)

  // json_data = JSON.parse(userData)
  // console.log('2222', userData)
  if (privKey && pubKey) {
    userData = await sign(userData, privKey=privKey, pubKey=pubKey)
  } else {
    userData = await sign(userData)
  }
  
  // return_signed_userData(userData)
  // console.log('userData222',JSON.stringify(userData))
  return userData
}
function return_signed_userData(userData) {
  // console.log('return signed data')
  if (userData) {
    // console.log(JSON.stringify(userData))
    const data = {'userData': JSON.stringify(userData)};
    // console.log(data)
    // console.log('sending')
    $.ajax({
      type:'POST',
      url:'/accounts/set_user_data',
      data: data,
      success:function(response){
        console.log(response)
        if (response['message'] == 'success') {
          console.log('success')
          // delete userData['signature']
          // delete userData['publicKey']
          // localStorage.setItem('passPrivKey', passKey);
          // localStorage.setItem('passPubKey', pubKey);
          // localStorage.setItem('username', data['username']);
          localStorage.setItem('userData', JSON.stringify(userData));
          // if (window.location.href.indexOf("/region") > -1) {
          //   // window.location.href = `/region?${queryString}`;
          //   location.reload()
          // } else {
          //   closeModal();
          // }
        // } else {
        //   field3.innerHTML = response['message']
        } else {
          alert(response['message'])
        }
      },
      error: function (xhr, ajaxOptions, thrownError) {
        alert('Failed to reach server');
      } 
    });
  }
  
}
function get_stored_userData() {
  console.log('get stored userdata')
  var userData = JSON.parse(localStorage.getItem("userData"));
  return userData
  // console.log(localStorage.getItem("userData"))
  // console.log(JSON.stringify(userData))
  var userArrayData = {};
  // console.log('next')
  try {
    Object.keys(userData).forEach(field => {
      if (field.endsWith('_array')) {
        // console.log(userData[field])
          // userArrayData[field] = userData[field];
        // x.follow_post_id_array = JSON.parse(JSON.stringify(userData.follow_post_id_array).replace(/'/g, '"'));
        userArrayData[field] = JSON.parse(JSON.stringify(userData[field]).replace(/'/g, '"'));
      }
    });
  } catch(err) {}
  // console.log('done get stored data',userArrayData)
  return [userData, userArrayData]
}
// not used
function expand_received_userData(userData) {
  // userData must be processed before local modification becasuse of array fields not parsing properly
  console.log('expand_received_userData')
  var userData = JSON.parse(userData);
  // console.log(userData)
  var userArrayData = {};
  // console.log('next')
  Object.keys(userData).forEach(field => {
    if (field.endsWith('_array')) {
      // console.log(userData[field])
        userArrayData[field] = userData[field];
        // userArrayData[field] = JSON.parse(userData[field].replace(/'/g, '"'));
    }
  });
  Object.keys(userArrayData).forEach(field => {
    // userData[field] = "['" + userArrayData[field].map(item => item.replace(/'/g, "\\'")).join("', '") + "']";
    userData[field] = userArrayData[field];
  });
  
  // const currentDate = new Date();
  // const isoString = currentDate.toISOString();
  
  // console.log('isoString',formatDateToDjango(isoString))
  // console.log('userData.last_updated',userData.last_updated)
  
  // const currentDate2 = new Date(userData.last_updated);
  // const isoString2 = currentDate2.toISOString();
  // console.log('Date(userData.last_updated)',formatDateToDjango(isoString2))
  // userData.last_updated = formatDateToDjango(isoString2)
  // localStorage.setItem('userData', JSON.stringify(userData));
  // console.log('userData11',userData)
  // console.log('userArrayData11',userArrayData)
  return [userData, userArrayData]

}
async function update_userData(userData) {
  console.log('update_userData')
  receivedUserData = JSON.parse(userData)
  if (receivedUserData.must_rename == true || receivedUserData.must_rename == 'true') {
    receivedUserData.must_rename = false
    engage_rename = true
  } else {
    engage_rename = false
  }
  // is_valid = verifyUserData(userData)
  is_valid = await verifyUserData(userData)
  if (is_valid) {
    // receivedUserData, receivedUserArrayData = expand_received_userData(userData)
    // r = expand_received_userData(userData)
    // receivedUserData = d[0]
    // receivedUserArrayData = d[1]
    // userData, userArrayData = get_stored_userData()
    userData = get_stored_userData()
    // userData = d[0]
    // userArrayData = d[1]
    if (Date(userData.last_updated) < Date(receivedUserData.last_updated)) {
      // userData = get_userData_for_sign_return(receivedUserData, receivedUserArrayData)
      localStorage.setItem('userData', JSON.stringify(userData));   
      console.log('userData updated from server') 
      if (engage_rename) {
        modalPopUp('Mandatory User Rename', '/accounts/rename_setup')
      }
    }
  }
  
}
async function enact_user_instruction(instruction){
  // console.log(instruction)
  // console.log(userData)
  // var pattern = /keyword\s+"([^"]+)"/;
  try {
    var pattern = /^(\w+)\s+(\w+)\s+"([^"]+)"$/;
    var match = pattern.exec(instruction);
    var command = match[1]
    var direction = match[2]
    var target = match[3]
  } catch(err) {
    var command = instruction
  }
  if (command.includes('_array') || command.includes('_json')) {
      // var wordInQuotes = match[1];
      // var direction = instruction.split(' ')[0];
      // console.log(wordInQuotes);
      userData = edit_user_array(command, target, direction)
      userData = sign_userData(userData)
      return_signed_userData(userData)
    //     .then(handleSigningResponse)
    //     .then(return_signed_userData)
    //     .catch(error => {
    //     console.error('There was a problem with the AJAX request:', error);
    // });

      // handleSigningResponse(userData)
      //   .then(handleSetRegionResponse)
      //   .catch(error => {
      //     console.error('There was a problem with the AJAX request:', error);
      // });
  } else if (command == 'get_stored_user_login_data') {
    // console.log('enact get_stored_user_login_data')
    try {
      display_name = localStorage.getItem("display_name")
      pass = localStorage.getItem("pass")
      var form = document.getElementById("modalForm");
      if (display_name != 'null' && display_name != null) {
        form.elements["username"].value = display_name;
      }
      if (pass != 'null' && pass != null) {
        form.elements["password"].value = pass;
      }
      
    } catch(err){}

  }


  // if (instruction.contains('keyword')) {
  //   console.log('yes')
  // }
  // handleSigningResponse(userData)
  //     .then(handleSetRegionResponse)
  //     .catch(error => {
  //       console.error('There was a problem with the AJAX request:', error);
  //   });
}

function edit_user_array(array_type, new_keyword, direction){
  console.log('edit user array')
  // console.log(array_type)
  // console.log(direction)
  // console.log(new_keyword)
  // console.log(userData)
  // parsedData = JSON.parse(userData)
  // console.log(parsedData)
  // if (array_type == 'keyword_array'){
  //   array = parsedData.keyword_array
  // } else if (array_type == 'follow_topic_json'){
  //   array = parsedData[array_type]
  // }

  userData = get_stored_userData()
  
  // // parsedData = JSON.parse(userData)
  // // if (array_type == 'keyword_array'){
    interest_array = JSON.parse(userData.interest_array)
  // // } else if (array_type == 'follow_topic_json'){
  //   // follow_topic_json = parsedData.follow_topic_json
    follow_topic_array = JSON.parse(userData.follow_topic_array)
  //   // json_array = 
  // // }
  // console.log(keyword_array)
  // var interest_array = JSON.parse(interest_array.replace(/'/g, '"'));
  // // var follow_topic_json = JSON.parse(follow_topic_json.replace(/'/g, '"'));
  // var follow_topic_array = JSON.parse(follow_topic_array.replace(/'/g, '"'));

  // console.log(follow_topic_json)
  try {
    if (array_type.includes('interest_array')) {
      last_keyword = interest_array[interest_array.length - 1];
      // last_keyword = interest_array[interest_array.length - 1].replace(/^'|'$/g, '');
    } else if (array_type.includes('follow_topic_array')) {
      last_keyword = follow_topic_array[follow_topic_array.length - 1];
      // last_keyword = follow_topic_array[follow_topic_array.length - 1].replace(/^'|'$/g, '');
    }
  }catch(err){
    console.log(err)
    last_keyword = null
  }
  // console.log(last_keyword)
  // console.log(new_keyword)
  if (direction == 'add'){
    if (last_keyword != new_keyword){
      if (array_type.includes('interest_array')) {
        if (interest_array.length > 990) {
          interest_array.shift()
        }
        interest_array.push(new_keyword);
      } else if (array_type.includes('follow_topic_array')) {
        if (follow_topic_array.length > 90) {
          follow_topic_array.shift()
        }
        follow_topic_array.push(new_keyword);
      }
      // console.log('continue')
      // console.log(json_array)
      // // console.log(JSON.stringify(json_array))
      // userData.follow_topic_array = follow_topic_array
      // // parsedData.follow_topic_json = follow_topic_json
      // userData.interest_array = interest_array
      // result = JSON.stringify(parsedData)
    // } else {
    //   // console.log('do not continue')
    //   result = null
    }

  } else if (direction == 'remove'){
    // console.log('remove element')
      if (array_type.includes('interest_array')) {
        var index = interest_array.indexOf(new_keyword);
        if (index !== -1) { 
          interest_array.splice(index, 1);
        }
      } else if (array_type.includes('follow_topic_array')) {
        var index = follow_topic_array.indexOf(new_keyword);
        if (index !== -1) { 
          follow_topic_array.splice(index, 1);
        }
      }

    
      userArrayData.follow_topic_array = follow_topic_array
    // parsedData.follow_topic_json = follow_topic_json
    userArrayData.interest_array = interest_array
    // result = JSON.stringify(parsedData)
    // console.log(JSON.stringify(json_array))
  // } else {
  //   result = null
  }
  userData.follow_topic_array = JSON.stringify(follow_topic_array)
  // parsedData.follow_topic_json = follow_topic_json
  userData.interest_array = JSON.stringify(interest_array)
  return userData
  // console.log('result')
  // console.log(result)
  // return new Promise((resolve, reject) => {
  //   resolve(result)
  // });
}
function formatDateToDjango(isoString) {
  const date = new Date(isoString);

  function pad(number, length = 2) {
    return String(number).padStart(length, '0');
  }

  const year = date.getUTCFullYear();
  const month = pad(date.getUTCMonth() + 1);
  const day = pad(date.getUTCDate());
  const hours = pad(date.getUTCHours());
  const minutes = pad(date.getUTCMinutes());
  const seconds = pad(date.getUTCSeconds());
  const milliseconds = pad(date.getUTCMilliseconds(), 3) + '000'; // Add three zeros to match six digits format

  return `${year}-${month}-${day}T${hours}:${minutes}:${seconds}.${milliseconds}+00:00`;
}

async function check_instructions(page) {
  console.log('check instructions')
  // console.log(page)
  try {
    
    var userData = page.getElementById("userData").getAttribute("value")
    await update_userData(userData)
    // console.log('received_data11',userData)
    // userData = get_stored_userData()

    // // is_valid = await verifyUserData(userData)

    // var userData = localStorage.getItem('userData')
    // // d = expand_received_userData(userData)
    // // // parsedData = get_userData_for_sign_return(d[0], d[1])
    // // // // pk = '04a074c0fb97372a462f9e1e840204da9dfcdf9b8cc0a94169b34a1035eb7a82e076350e7108a552adb19c3aad35e42123ab495cb6a1228e83cab55bd582405cf4'
    // // // // sig = '3044022054a17588f60fea91f55c22894b18daee5ce444443eaecb5528132fe45488ec2602202b4ee4ec5ad791360520875312a0dc656b2f95cdd295dd6e06361231f4736596'
    // // // // // pk = parsedData.publicKey
    // // // // // s = parsedData.signature
    // // // // // delete parsedData.publicKey
    // // // // // delete parsedData.signature
    // // // // // console.log('parsedDataa22',JSON.stringify(parsedData))
    // // // // // json = JSON.stringify(parsedData)

    // // // // // is_val = verify(userData, sig, pk)

    // // // // // console.log('2222222')

    // // parsedData = get_userData_for_sign_return(d[0], d[1])
    // // // parsedData.first_name = 'Sozed'
    // // // var s = parsedData.signature
    // // // var pk = parsedData.publicKey
    // // // delete parsedData.publicKey
    // // // delete parsedData.signature
    // // // console.log('signed_data22',JSON.stringify(parsedData))
    // // // json = JSON.stringify(parsedData)

    // // // is_val = await verify(json, s, pk)

    // // userData = d[0]
    // test_data = userData.interest_array
    // parsedTestdata = JSON.parse(test_data)
    // parsedTestdata.push('test1')
    // userData.interest_array = JSON.stringify(parsedTestdata)
    // console.log('test_data',JSON.stringify(parsedTestdata))
    // signed_data = await sign_userData(userData)

    // // // // parsedData = JSON.parse(userData)
    // // // // parsedData.must_rename = false
    // // // // console.log('must_rename',parsedData.must_rename)
    // // // console.log('last_updated', parsedData.last_updated)
    // // // const currentDate = new Date();
    // // // const isoString = currentDate.toISOString();
    // // // // console.log('isoString', isoString)
    // // // parsedData.last_updated = formatDateToDjango(isoString)
    // // // r_lastUpdated = d[0].last_updated
    // // // s_lastUpdated = signed_data.last_updated
    // // // if (Date(r_lastUpdated) > Date(s_lastUpdated)) {
    // // //   console.log('greater')
    // // // } else {
    // // //   console.log('leser')
    // // // }
    // // // delete parsedData.publicKey
    // // // delete parsedData.signature
    // // // signed_data = await sign(parsedData)
    // // // signed_data = await sign_userData(d[0], d[1])
    // // // // // is_valid = await verifyUserData(userData)
    // // console.log('333')
    // // // // localStorage.setItem('userData', JSON.stringify(signed_data))
    // // // // localStorage.setItem('userData', JSON.stringify(signed_data));
    // // // parsedData = JSON.parse(signed_data)
    
    // is_valid = await verifyUserData(JSON.stringify(signed_data))
    // console.log('new valid', is_valid)
    // // // // var modified_data = signed_data
    // // // // // console.log('signed_data11',JSON.stringify(signed_data))
    // // // // pk = signed_data.publicKey
    // // // // s = signed_data.signature
    // // // // delete signed_data.publicKey
    // // // // delete signed_data.signature
    // // // // // console.log('signed_data22',JSON.stringify(signed_data))
    // // // // json = JSON.stringify(signed_data)

    // // // // is_val = verify(json, s, pk)

    // const data = {'userData': JSON.stringify(signed_data)};
    // // console.log('signed_data333',JSON.stringify(signed_data))
    // $.ajax({
    //   type:'POST',
    //   url:'/accounts/set_user_data',
    //   data: data,
    //   success:function(response){
    //     console.log(response)
    //     if (response['message'] == 'success') {
    //       console.log('success')
    //       // delete userData['signature']
    //       // delete userData['publicKey']
    //       // localStorage.setItem('passPrivKey', passKey);
    //       // localStorage.setItem('passPubKey', pubKey);
    //       // localStorage.setItem('username', data['username']);
    //       localStorage.setItem('userData', JSON.stringify(signed_data));
    //       // if (window.location.href.indexOf("/region") > -1) {
    //       //   // window.location.href = `/region?${queryString}`;
    //       //   location.reload()
    //       // } else {
    //       //   closeModal();
    //       // }
    //     // } else {
    //     //   field3.innerHTML = response['message']
    //     } else {
    //       alert(response['message'])
    //     }
    //   },
    //   error: function (xhr, ajaxOptions, thrownError) {
    //     alert('Failed to reach server');
    //   } 
    // });
    
    

    // verifyUserData(userData)
    // console.log('userData:',userData)
    // update_userData(userData)
  }catch(err){console.log('checkinstructions1',err)}
  try{
    var instruction = page.getElementById("instruction").getAttribute("value");

  // Get the value attribute of the div element
  // var value = divElement
    // var instruction = document.getElementById('instruction');
    // console.log(instruction)
    // console.log(userData)
    enact_user_instruction(instruction)
  }catch(err){
    // console.log(err)
  }
}

$(document).ready(
    function(){
      // alert('document ready start')
      try{
        isLoading = document.getElementsByClassName('lds-dual-ring')[0];
        // alert(isLoading)
        if (isLoading){
          current = window.location.href
          if (current.includes('?')){
            addition = '&style=feed'
          } else {
            addition = '?style=feed'
          }
          url = current + addition
          // alert(url)
          $.ajax({
            url: url,
            success: function (data) {
              // alert(data)
                  var new_cards =  $($.parseHTML(data));
                  // alert(new_cards[1])
                  var newList = new Array();
                  for (f = 0; f < new_cards.length; f++){
                      newList.push(new_cards[f])
                  }
              document.getElementById("bottomCard").outerHTML='';
              $('#feed').append(newList);
              page_picker = document.getElementsByClassName('pagePicker');
              page_form = document.getElementById("pageForm");
              try{
                page_form.innerHTML = page_picker[page_picker.length - 1].outerHTML;
              }catch(err){}
              var cards = document.getElementsByClassName('card');
              shorten_text(cards)
              // alert('done')
              },
            dataType: 'html'
        });
        }
        
      }catch(err){}
      try{
        var rePosition = document.getElementsByClassName('moveToHere')[0];
        // alert(rePosition)
        rePosition.scrollIntoView({ behavior: 'smooth', block: 'start' });
        
      }catch(err){}
      
      var cards = document.getElementsByClassName('card');
      shorten_text(cards)
      var feed = document.getElementById('feed');
      // var feedTop = document.getElementsByClassName('feedTop')[0];
      var feedHeight = feed.offsetHeight;
      var bottomCard = document.getElementById('bottomCard');
      var bottomCardHeight = bottomCard.offsetHeight;
      var sidebar = document.getElementById('sidebar');
      var sidebarHeight = sidebar.offsetHeight;
      let setHeight = sidebarHeight - (feedHeight - bottomCardHeight) + 50;
      let windowHeight = (innerHeight);
      // alert(minHeight)
      if (feedHeight > windowHeight){
        // alert('yes')
        // feed.css({'min-height': '110px'}); 
        $('#bottomCard').attr("style","min-height:" + setHeight + "; max-height:" + setHeight + ";");
        
      }
      // check returned userData, check if more recently updated than local userData, if so check if valid, then save to localStorage
      // check if userData.must_rename == true, rewrite must_rename to false for verification, perform appropriate action to rename
      // update_userData(document);
      check_instructions(document);
      // alert('done')
    var $el = $('#sidebar'); 
    var isPositionFixed = ($el.css('position') == 'fixed');
    if ($(this).scrollTop() > 100 && !isPositionFixed){
        adjustSidebar($el)
    }
    var $navbar = $('#navBar'); 
    var isPositionFixed = ($navbar.css('position') == 'fixed');
      if ($(this).scrollTop() > 70 && !isPositionFixed){
        adjustNavBar($navbar)
      }
  }

  
)
$(document).on('submit', '#post-form',function(e){
  // alert($('#input-date').val())
  // alert($('#input-date').serialize())
  e.preventDefault();
  $.ajax({
      type:'POST',
      url:'/utils/calendar_widget',
      data: $('#post-form').serialize(),
      // data:{
      //     date:$('#post-form').serialize(),
      //     csrfmiddlewaretoken:$('input[name=csrfmiddlewaretoken]').val(),
      //     action: 'post'
      // },
      success:function(data){
        a = document.getElementById('agenda')
        // alert(a)
        // alert(data)
        a.nextElementSibling.remove()
        a.outerHTML = data
        // alert('done')
        // alert(data)
          // document.getElementById("post-form").reset();
          // $(".posts").prepend('<div class="col-md-6">'+
          //     '<div class="row no-gutters border rounded overflow-hidden flex-md-row mb-4 shadow-sm h-md-250 position-relative">' +
          //         '<div class="col p-4 d-flex flex-column position-static">' +
          //             '<h3 class="mb-0">' + json.title + '</h3>' +
          //             '<p class="mb-auto">' + json.description + '</p>' +
          //         '</div>' +
          //     '</div>' +
          // '</div>' 
          // )
        $('#secondPane').scroll(function(){
          // alert('second')
          $('#secondPane').addClass('showFullText');
          $('#firstPane').removeClass('showFullText');
          $('#thirdPane').removeClass('showFullText');

        })
      },
      error : function(xhr,errmsg,err) {
      console.log(xhr.status + ": " + xhr.responseText); // provide a bit more info about the error to the console
  }
  });
});



function mobileSwitch(screen){
  // alert(screen)
    labels = document.getElementsByClassName('label');
    for(i=0;i<labels.length;i++){
      if (labels[i].innerHTML == 'menu'){
        var menu_label = labels[i]
      } else if (labels[i].innerHTML == 'notifications'){
        var notifications_label = labels[i]
      } else if (labels[i].innerHTML == 'mail'){
        var mail_label = labels[i]
      } else if (labels[i].innerHTML == 'search'){
        var search_label = labels[i]
      } 
    }
    var menu = $('.indexMobile');
    var search = $('.searchMobile');
    var notifications = $('.notificationsMobile');
    if (screen == 'menu'){
      if (menu.attr('class').includes('display')){
        menu.removeClass('display');
        menu_label.classList.remove("display_label");
      } else {
        menu.addClass('display');
        menu_label.classList.add("display_label");
        search.removeClass('display');
        search_label.classList.remove("display_label");
        notifications.removeClass('display');
        notifications_label.classList.remove("display_label");
        // $('.feedContainer').removeClass('display');
      }
    } else if (screen == 'search'){
      // alert(search.attr('class'))
      if (search.attr('class').includes('display')){
        search.removeClass('display');
        search_label.classList.remove("display_label");
      } else {
        search.addClass('display');
        search_label.classList.add("display_label");
        menu.removeClass('display');
        menu_label.classList.remove("display_label");
        notifications.removeClass('display');
        notifications_label.classList.remove("display_label");
      }
    }else if (screen == 'feed'){      
      if (menu.attr('class').includes('display') || search.attr('class').includes('display') || notifications.attr('class').includes('display')){
        menu.removeClass('display');
        menu_label.classList.remove("display_label");
        search.removeClass('display');
        search_label.classList.remove("display_label");
        notifications.removeClass('display');
        notifications_label.classList.remove("display_label");
      } else {
        window.location.href = '/';
      }
    } else if (screen == 'notifications'){
      // alert(notifications.attr('class'))
      if (notifications.attr('class').includes('display')){
        notifications.removeClass('display');
        notifications_label.classList.remove("display_label");
      } else {
        notifications.addClass('display');
        notifications_label.classList.add("display_label");
        menu.removeClass('display');
        menu_label.classList.remove("display_label");
        search.removeClass('display');
        search_label.classList.remove("display_label");
      }
    }
}

function searchMobileSwitch(tab){
  var tabs = document.getElementsByClassName('searchTab');
  var pages = document.getElementsByClassName('searchTabContent');
  for(i=0; i<pages.length; i++){
    if (pages[i].classList.contains('show')) {
      pages[i].classList.remove('show');
      removePage = pages[i]
        setTimeout(function (){
        removePage.classList.remove('block');
      }, 200);
    }
    if (pages[i].id == tab) {
      pages[i].classList.add('block');
        pages[i].classList.add('show');
    }
  }
  for(i=0; i<tabs.length; i++){
      tabs[i].classList.remove('blue');
    if (tabs[i].id == tab) {
      tabs[i].classList.add('blue');
    }
  }

}
