const { YoutubeTranscript } = require('youtube-transcript');

// 4fRgpzl9R-E: 2025 Best Cosmetics
// -4spt5m9S-Y: 2025 My Best Cosmetics
const VIDEO_IDS = ['4fRgpzl9R-E', '-4spt5m9S-Y', 'epHygxXbZt0'];

async function fetchTranscript(videoId) {
    console.log(`\nFetching transcript for ${videoId}...`);
    try {
        const transcript = await YoutubeTranscript.fetchTranscript(videoId, { lang: 'ja' });
        console.log(`Success! Found ${transcript.length} lines.`);
        console.log(JSON.stringify(transcript.slice(0, 3), null, 2));
        return transcript;
    } catch (e) {
        console.log(`Failed (Direct JA): ${e.message}`);
        
        // Retry with default lang
        try {
            console.log('Retrying with default language...');
            const transcript = await YoutubeTranscript.fetchTranscript(videoId);
            console.log(`Success (Default)! Found ${transcript.length} lines.`);
            console.log(JSON.stringify(transcript.slice(0, 3), null, 2));
            return transcript;
        } catch (e2) {
             console.log(`Failed (Default): ${e2.message}`);
        }
    }
}

async function run() {
    for (const id of VIDEO_IDS) {
        await fetchTranscript(id);
    }
}

run();
