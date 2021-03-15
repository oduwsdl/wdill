/*
A script using PhantomJS http://phantomjs.org to create Web page screenshot at
the given browser resolution and save it as a PNG file.

Written by Ramiro Gómez http://ramiro.org/
MIT licensed: http://rg.mit-license.org/
*/
var system = require('system')
var page = require('webpage').create(),
    re_trim = /^https?:\/\/|\/$/g,
    re_conv = /[^\w\.-]/g;

var redirectionFlag = 0;

var globalW = 1024;
var globalH = 768;

//var url2filename = function(url, w, h)
//{
    //return extractYearFromUrl(url) + '.png';
    //return url
        //.replace(re_trim, '')
        //.replace(re_conv, '-')
        //+ '.' + w + 'x' + h + '.png'
//}

function forceClose()
{
    phantom.exit();
}

/*
function extractYearFromUrl(url)
{
    var lasIndexOfHTTPMarker = url.lastIndexOf("/http://");
    var yearExtract = '';
  
    for (var i = lasIndexOfHTTPMarker; i > -1; i--) 
    { 
        if(isNaN(url[i]) === false)
        {
            //yearExtract = url[i] + yearExtract;
        }
        
    }
    yearExtract = yearExtract.substring(0,4);
    return yearExtract;
}
*/

//retrive item all items enclosed by beginMarker and endMarker, with search position at the position of the signatureString
function onClickRedirectionResolver(pageContent, signatureString, beginMarker, endMarker)
{
    if(pageContent.length > 0 && signatureString.length > 0 && beginMarker.length > 0 && endMarker.length > 0)
    {
        var positionOfSignatureString = pageContent.indexOf(signatureString);
        if(positionOfSignatureString > -1)
        {
            var urls = [];
            var count = 0;
            var url = '';
            do
            {
                url = getRedirectUrl(pageContent, beginMarker, endMarker, positionOfSignatureString);

                if(url.length > 0)
                {
                    var offset = pageContent.indexOf(url, positionOfSignatureString);
                    offset = offset + url.length;

                    urls[count] = url;
                    count = count + 1;

                    positionOfSignatureString = offset;
                }
            }
            while(url.length>0);

            return urls;

        }
    }

    return [];
}

/*
function isLetter(c)
{
  c = c.toUpperCase();
  return c >= "A" && c <= "Z";
}
*/

//resorted to this since response.redirectURL always returns null
function getRedirectUrl(pageContent, startStringSignature, endStringSignature, startSearchPosition)
{
    if(pageContent.length > 0 && startStringSignature.length > 0 && endStringSignature.length > 0 && startSearchPosition > -1)
    {
        //var startStringSignature = '<p class="impatient"><a href="';
        //var endStringSignature = '">Impatient?</a></p>';

        var indexOfStartSignature = pageContent.indexOf(startStringSignature, startSearchPosition);

        if(indexOfStartSignature != -1)
        {

            var indexOfEndSignature = pageContent.indexOf(endStringSignature, indexOfStartSignature + startStringSignature.length);
            var redirectUrl = pageContent.substring(indexOfStartSignature + startStringSignature.length, indexOfEndSignature);

            //console.log("*PAGE*");
            //console.log(pageContent);
            //console.log("*PAGE*");
            //console.log("");

            return redirectUrl;
        }
        else
        {
            return "";
        }
    }
    else
    {
        return "";
    }
}

function getHost(url)
{
    if(url.length > 0)
    {
        var a = document.createElement('a');
        a.href = url;
        return a.hostname;
    }
}



var webshot = function(url, w, h, timeout, folderName, filename) 
{
    console.log('');
    console.log('===> webshot url: ' + url);
    page.viewportSize = { width: w, height: h };
   
    //page.onError = function(msg, trace) 
    //{
        
        //console.log('=onPageError');
        //console.log(msg);

        //var msgStack = ['ERROR: ' + msg];

        //if (trace && trace.length) 
        //{
        //    msgStack.push('TRACE:');
        //    trace.forEach(function(t)
        //    {
        //       msgStack.push(' -> ' + t.file + ': ' + t.line + (t.function ? ' (in function "' + t.function +'")' : ''));
        //    });
        //}

        //console.error(msgStack.join('\n'));

    //};

    page.open(url, function(status)
    {
         
        if (status !== 'success') 
        {
            console.log('Unable to load url: ' + url + ', status: ' + status + ', timeout: ' + timeout);
            //phantom.exit(); prematurely kills the redirection of phantomjs therefore delay exit

            setTimeout(forceClose, 10000);
            //phantom.exit();
        
        } 
        else 
        {

            //redirection solution 1 - start: timed redirection
            var pageContent = page.content;
            var redirectUrlValue = getRedirectUrl(pageContent, '<p class="impatient"><a href="', '">Impatient?</a></p>', 0);

            if(redirectUrlValue.length > 0)
            {
                //console.log('redirectUrlValue.length > 0');
                //temp = 'abc'

                //ATTEMPT 1 - redirection
                var hostname = getHost(url);
                var indexOfHostname = url.indexOf(hostname);
                
                var fullHostName = url.substring(0,indexOfHostname + hostname.length);
                fullHostName = fullHostName.trim();

                if(fullHostName.length > 0)
                {
                    var newUrl = fullHostName + redirectUrlValue;
                    //console.log('redirectUrl: ' + newUrl);
                    
                    console.log('...type 1 redirect detected');
                    redirectionFlag = 10000;
                    //parameters don't matter since redirectionFlag sets correct values
                    webshot(newUrl, 1024, 768, 10000);
                }

            }
            //redirection solution 1 - end

            //redirection solution 2 - start: static onClick redirection
            var staticRedirectionMarker = "<h1>Site redirect requested (302)</h1>";
            var beginMarker = 'href="';
            var endMarker = '"';
          
            //gotoUrlsArray contains all links following staticRedirectionMarker
            var gotoUrlsArray = onClickRedirectionResolver(pageContent, staticRedirectionMarker, beginMarker, endMarker);
           
            if(gotoUrlsArray.length > 0)
            {
                console.log('...type 2 redirect detected');
                redirectionFlag = 10000;
                //redirect to the first link
                //parameters don't matter since redirectionFlag sets correct values
                webshot(gotoUrlsArray[0], 1024, 768, 10000);
            }


            //redirection solution 2 - end

            if(redirectionFlag !== 0)
            {
                console.log('redirectUrl: ' + url);
                timeout = redirectionFlag;

                w = globalW;
                h = globalH;

                redirectionFlag = 0;
            }

            
            

            window.setTimeout(function() 
            {

                page.clipRect = { top: 0, left: 0, width: w, height: h};
                //filename = url2filename(url, w, h)

                //var indexOfHTTP = url.lastIndexOf(".");

                //var folderName = '';
                //i = indexOfHTTP - 1;

                //console.log('fName: ' + foldName)
            
                //review this block, folder name should be passed as argument, not recalculated
                //while(i > -1)
                //{
                //    if(isLetter(url[i]))
                //    {
                //        folderName = url[i] + folderName;
                //    }
                //    else
                //    {
                //        break;
                //    }
                //    i = i - 1;
                //}
                filename = './'+folderName+ '/' + filename + '.png';
                

              
                page.evaluate(function() 
                {
                    //annotate file before taking screenshot
                    //var frag = document.createDocumentFragment(),
                    //element = document.createElement('div');
                    //element.innerHTML = '<center><h1> TITLE GOES HERE </h1></center>';
                    //while (element.firstChild) 
                    //{
                    //    frag.appendChild(element.firstChild);
                    //}
                    ////Native DOM method can also be used to insert frag
                    //document.body.insertBefore(frag, document.body.childNodes[0]);

                    if ('transparent' === document.defaultView.getComputedStyle(document.body).getPropertyValue('background-color')) 
                    {
                        document.body.style.backgroundColor = '#fff';
                    }

                   
                });

                
                page.render(filename);
                //console.log('rendered ' + filename + ',timeout: ' + timeout);
            
                

                phantom.exit();
            },  timeout);
        }

    });



    
};

// phantom.args is deprecated in favor of system.args, but version 1.4.0 does
// not seem to support the system module.
if (6 !== system.args.length) 
{
    console.log('Usage: phantomjs webshots.js http://example.com 1024 768 folderName filename');
    phantom.exit();
} 
else 
{
    //setTimeout(forceClose, 10000);
    //pass folder name as argument
    
    
    webshot(system.args[1], system.args[2], system.args[3], 1000, system.args[4], system.args[5]);
}
