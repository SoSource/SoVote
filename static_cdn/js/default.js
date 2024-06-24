
// generating the secret key from password and salt
async function deriveKeyFromPassword(password, salt) {
  const encoder = new TextEncoder();
  const passwordBuffer = encoder.encode(password);
  const saltBuffer = new Uint8Array(salt);

  const derivedKeyBuffer = await crypto.subtle.importKey(
    'raw',
    passwordBuffer,
    { name: 'PBKDF2' },
    false,
    ['deriveBits']
  );

  const key = await crypto.subtle.deriveBits(
    {
      name: 'PBKDF2',
      salt: saltBuffer,
      iterations: 100000,
      hash: 'SHA-256',
    },
    derivedKeyBuffer,
    256  // Length of the derived key in bits
  );

  return new Uint8Array(key);
}

async function generateKeyPair(customSecretKey) {
  let private_key;
  
  if (customSecretKey) {
    const keyBuffer = await crypto.subtle.importKey(
      'raw',
      customSecretKey,
      { name: 'ECDH', namedCurve: 'P-256' },
      true,
      []
    );

    private_key = await crypto.subtle.generateKey(
      { name: 'ECDH', namedCurve: 'P-256' },
      true,
      ['deriveBits']
    );

    await crypto.subtle.deriveBits(
      { name: 'ECDH', namedCurve: 'P-256' },
      keyBuffer,
      256  // Length of the derived key in bits
    );
  } else {
    private_key = await crypto.subtle.generateKey(
      { name: 'ECDH', namedCurve: 'P-256' },
      true,
      ['deriveBits']
    );
  }

  const publicKeyBuffer = await crypto.subtle.exportKey('spki', private_key.publicKey);

  return {
    privateKey: private_key,
    publicKey: new Uint8Array(publicKeyBuffer),
  };
}


// signing a transaction
async function signTransaction(privateKey, transactionData) {
  const encoder = new TextEncoder();
  const dataBuffer = encoder.encode(transactionData);

  // Hash the transaction data
  const hashBuffer = await crypto.subtle.digest('SHA-256', dataBuffer);

  // Import the private key
  const importedPrivateKey = await crypto.subtle.importKey(
    'pkcs8',
    privateKey,
    { name: 'ECDSA', namedCurve: 'P-256' },
    true,
    ['sign']
  );

  // Sign the hashed transaction with the private key
  const signatureBuffer = await crypto.subtle.sign(
    { name: 'ECDSA', hash: { name: 'SHA-256' } },
    importedPrivateKey,
    hashBuffer
  );

  // Convert the signature buffer to a hex string
  const signatureArray = new Uint8Array(signatureBuffer);
  const signatureHex = Array.from(signatureArray)
    .map(byte => byte.toString(16).padStart(2, '0'))
    .join('');

  return signatureHex;
}

// Example usage:
const privateKeyBytes = /* Replace with your private key bytes */;
const privateKey = await crypto.subtle.importKey(
  'pkcs8',
  privateKeyBytes,
  { name: 'ECDSA', namedCurve: 'P-256' },
  true,
  ['sign']
);

const transactionData = "Sender: Alice, Recipient: Bob, Amount: 10 BTC";

const signature = await signTransaction(privateKey, transactionData);
console.log(`Signature: ${signature}`);




// Example usage:
const salt = crypto.getRandomValues(new Uint8Array(16));
const password = 'jetson';

deriveKeyFromPassword(password, salt).then(customSecretKey => {
  console.log('Custom Secret Key:', customSecretKey);

  generateKeyPair(customSecretKey).then(({ publicKey }) => {
    console.log(`Public Key: ${publicKey}`);
  });
});














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

// Example usage
const secretKey = 'super-secret-key';
const dataToStore = { username: 'john_doe', password: 'secure_password' };

// Encrypt and store data
encryptAndStore(secretKey, dataToStore);

// Retrieve and decrypt data
const retrievedData = retrieveAndDecrypt(secretKey);
console.log(retrievedData);


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



function react(item, iden){
  // alert('start')
  
  if(item == 'follow2'){
    // alert(iden)
    var navBar = document.getElementById('navBar');
    // alert(navBar)
    follow = item.split('-')[0]
    // alert(follow)
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
    $.get(link, function(data){
      alert(data.replace(/&quot;|&#039;/g, '"'))
      // if (data.includes('Login')){
      //   alert('Please Login')
      // }
    });
  } else {
    // alert('else')
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
        } else if (item == 'share') {
          var popup = document.getElementById('share-' + iden);
          popup.classList.toggle("show");
          li = rs[i].getElementsByClassName(item)[0]
          li.classList.toggle('active');
          li.classList.add('depress');

        } else{
          // alert(item)
          li = rs[i].getElementsByClassName(item)[0]
          li.classList.toggle('active');
          li.classList.add('depress');
          // alert('done')
        }
      }

    }
    // li.classList.remove('depress');     
      // alert('m')
    setTimeout(function (){
      // alert(li.classList)
      li.classList.remove('depress');     
      // alert(li.classList)

    }, 200);
    // alert('n')
    if (convert_to_none){
      item = 'None'
    }
    if (item != 'share') {
      $.get('/utils/reaction/' + iden + '/' + item, function(data){
        // alert(data)
        if (data.includes('Login')){
          alert('Please Login')
        } else if (item == 'follow'){
          alert(data)
        }

      });
    }
  }
  
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
  var rs = document.getElementsByClassName('reactionBar');
  for (i=0;i<rs.length;i++) {
    if (rs[i].id == iden) {
      li = rs[i].getElementsByClassName('share')[0]
      li.classList.toggle('active');
      li.classList.add('depress');
    }
  }
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

$(document).ready(
    function(){
      // alert('start')
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
