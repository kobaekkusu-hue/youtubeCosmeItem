const puppeteer = require('puppeteer-extra');
const StealthPlugin = require('puppeteer-extra-plugin-stealth');

puppeteer.use(StealthPlugin());

const videoId = process.argv[2];
if (!videoId) {
    console.error("Please provide a video ID");
    process.exit(1);
}

(async () => {
    console.error("Launching browser...");
    const browser = await puppeteer.launch({ headless: true });
    console.error("Browser launched.");
    const page = await browser.newPage();

    try {
        const url = `https://www.youtube.com/watch?v=${videoId}`;
        console.error(`Navigating to ${url}...`);
        await page.goto(url, { waitUntil: 'domcontentloaded', timeout: 30000 });
        console.error("Navigation complete. Getting content...");

        const content = await page.content();
        console.error("Content retrieved. Searching for captionTracks...");
        const match = content.match(/"captionTracks":(\[.*?\])/);

        if (match) {
            console.error("Match found.");
            const tracks = JSON.parse(match[1]);
            console.error(`Found ${tracks.length} tracks.`);
            const jaTrack = tracks.find(t => t.languageCode === 'ja') || tracks[0];

            if (jaTrack) {
                // Get cookies and User-Agent
                const cookies = await page.cookies();
                const userAgent = await page.browser().userAgent();

                const cookieString = cookies.map(c => `${c.name}=${c.value}`).join('; ');

                console.error("Fetching XML using Node fetch with cookies...");

                // Use dynamic import for node-fetch if needed, or built-in fetch (Node 18+)
                // Assuming Node 18+ which has global fetch
                try {
                    const response = await fetch(jaTrack.baseUrl, {
                        headers: {
                            'User-Agent': userAgent,
                            'Cookie': cookieString,
                            'Referer': `https://www.youtube.com/watch?v=${videoId}`
                        }
                    });

                    if (!response.ok) {
                        console.error(`Fetch failed: ${response.status} ${response.statusText}`);
                        process.exit(1);
                    }

                    const text = await response.text();
                    console.error(`XML Content Length: ${text.length}`);
                    console.log(text);

                } catch (e) {
                    console.error(`Node fetch error: ${e.message}`);
                    process.exit(1);
                }
            } else {
                console.error("No suitable caption track found.");
                process.exit(1);
            }
        } else {
            console.error("No captionTracks found in page source.");
            process.exit(1);
        }

    } catch (e) {
        console.error(`Error: ${e.message}`);
        process.exit(1);
    } finally {
        await browser.close();
    }
})();
