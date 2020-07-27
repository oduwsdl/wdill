var Async = require('async');
const puppeteer = require('puppeteer')

async function headless(uri, w, h, folderName, filename) {
	const browser = await puppeteer.launch({
		headless: true
		//headless: false
	});
	const page = await browser.newPage();
	page.emulate({
		viewport: {
			width: w,
			height: h,
		},
		userAgent: "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/534.30 (KHTML, like Gecko) Ubuntu/11.04 Chromium/12.0.742.112 Chrome/12.0.742.112 Safari/534.30"
	});

	try {

		var regExpForDTStr = /\/\d{14}id_\/|\d{14}\//;
		var matchedString = uri.match(regExpForDTStr);
		if(matchedString != null)
			uri = uri.replace(matchedString[0],(matchedString[0].toString().replace(/id_\/$|\/$/,"if_/")));


		console.log("URL: "+uri)
		await page.goto(uri, {
			waitUntil: 'networkidle2',
			timeout: 60000,
		});

		await page.waitFor(5000);

		await page.screenshot({
			path: './'+folderName+ '/' + filename + '.png',
			//fullPage: true
		});
		console.log("Screenshot captured Sucessfully!");

	} catch (e) {
		console.log(uri,"Failed with error:", e);
		//process.exit(1);
	}
	browser.close();
}

if(process.argv.length !== 7){
	console.log("Usage: node takeScreenshot.js http://example.com 1024 768 folderName filename");
	process.exit(1);
} else {
	headless(process.argv[2], parseInt(process.argv[3]), parseInt(process.argv[4]), process.argv[5], process.argv[6]);
}