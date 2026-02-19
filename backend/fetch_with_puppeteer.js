const puppeteer = require('puppeteer-extra');
const StealthPlugin = require('puppeteer-extra-plugin-stealth');

puppeteer.use(StealthPlugin());

const VIDEO_ID = '4fRgpzl9R-E';
const URL = `https://www.youtube.com/watch?v=${VIDEO_ID}`;

(async () => {
    console.log(`Launching browser for ${URL}...`);
    const browser = await puppeteer.launch({ headless: true }); // headless: "new"
    const page = await browser.newPage();

    try {
        await page.goto(URL, { waitUntil: 'networkidle2' });
        console.log('Page loaded.');

        // Initial check for title
        const title = await page.title();
        console.log(`Title: ${title}`);

        // Wait for description to load (basic check)
        await page.waitForSelector('#description', { timeout: 10000 });
        console.log('Description found.');

        // In a real scenario, we would need to interact with the UI to open the transcript
        // But for now, let's just see if we can get the initial HTML without being blocked

        // Try to find the "Show transcript" button (this is complex as it requires clicking "More" usually)
        // For this test, just verification of access is enough.

        // However, youtube-transcript logic relies on static HTML or inner API calls.
        // If we can get the page source, maybe we can extract the caption tracks manually?

        const content = await page.content();
        if (content.includes('captionTracks')) {
            console.log('SUCCESS: Found captionTracks in page content!');
            const match = content.match(/"captionTracks":\[(.*?)\]/);
            if (match) {
                console.log('Caption Tracks JSON found.');
                console.log(match[0].substring(0, 100) + '...');
            }
        } else {
            console.log('FAILURE: captionTracks not found in page content.');
        }

    } catch (e) {
        console.error(`Error: ${e.message}`);
    } finally {
        await browser.close();
    }
})();
