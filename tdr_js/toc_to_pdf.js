
const puppeteer = require('puppeteer');

(async() => {
  const browser = await puppeteer.launch();
  const page = await browser.newPage();
  await page.goto('http://localhost:8000/toc.html', {waitUntil: 'networkidle2'});
  await page.pdf({
    displayHeaderFooter: false,
    path:'C:\\Users\\whip\\tdr_published_files\\toc.pdf',
    margin: {
      top: '10px',
      bottom: '10px',
      right: '10px',
      left: '10px',
    },
  });

  await browser.close();
})();

