var Async = require('async');
const puppeteer = require('puppeteer');

const instagram = {
	browser: null,
	page: null,

	initialize: async () => {
		instagram.browser = await puppeteer.launch({
			//headless: false
			headless: true
		});

		instagram.page = await instagram.browser.newPage();
		instagram.page.setUserAgent("Mozilla/5.0 (Android 7.0; Mobile; rv:54.0) Gecko/54.0 Firefox/54.0");
	},

	login: async (username, password) => {
		await instagram.page.goto('https://instagram.com',{
			waitUntil: 'networkidle2'
		});
		let loginButton = await instagram.page.$x('//button[contains(text(), "Log In")]');
		await loginButton[0].click();

		await instagram.page.waitFor(1000);

		await instagram.page.type('input[name="username"]', username, { delay:50 });
		await instagram.page.type('input[name="password"]', password, { delay:50 });
		loginButton = await instagram.page.$x('//div[contains(text(), "Log In")]');
		await loginButton[0].click();

		await instagram.page.waitFor(5000);

		let dontSaveLoginInfo = await instagram.page.$x('//button[contains(text(), "Not Now")]');
		if(dontSaveLoginInfo.length > 0)
			await dontSaveLoginInfo[0].click();

		await instagram.page.waitFor(5000);

		let dontAddToHomeScreen = await instagram.page.$x('//button[contains(text(), "Cancel")]');
		if(dontAddToHomeScreen.length > 0)
			await dontAddToHomeScreen[0].click();
	},

	postMedia: async (filepath, caption) => {
		let newPost = await instagram.page.$x('//div[contains(@data-testid, "new-post-button")]');

		const [fileChooser] = await Promise.all([
			instagram.page.waitForFileChooser(),
			newPost[0].click()
		]);
		await fileChooser.accept([filepath]);

		await instagram.page.waitFor(5000);
		let next = await instagram.page.$x('//button[contains(text(), "Next")]');
		next[0].click();

		await instagram.page.waitFor(5000);
		await instagram.page.type('textarea', caption, { delay:50 });

		await instagram.page.waitFor(1000);
		let share = await instagram.page.$x('//button[contains(text(), "Share")]');
		share[0].click();

		await instagram.page.waitFor(5000);
		let noNotifications = await instagram.page.$x('//button[contains(text(), "Not Now")]');
		if(noNotifications.length > 0)
			await noNotifications[0].click();

		await instagram.page.waitFor(3000);
		let moreButton = await instagram.page.$x('//*[@id="react-root"]/section/main/section/div[3]/div[1]/div/article[1]/div[1]/button');
		moreButton[0].click();

		await instagram.page.waitFor(3000);
		let goToPost = await instagram.page.$x('//button[contains(text(), "Go to post")]');
		goToPost[0].click();

		await instagram.page.waitFor(3000);
		let link = instagram.page.url();
		//instagram.browser.close();
		return link;
	}
}

async function postToInsta(username, password, filePath, caption) {
	await instagram.initialize();
	await instagram.login(username, password);
	let link = await instagram.postMedia(filePath, caption);
	console.log("Instagram Link: "+link);
}

if(process.argv.length !== 6){
	console.log("Usage: node instagram.js username password filePath caption");
	process.exit(1);
} else {
	postToInsta(process.argv[2], process.argv[3], process.argv[4], process.argv[5]);
}