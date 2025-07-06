
const puppeteer = require('puppeteer');

(async() => {
  const browser = await puppeteer.launch();
  const page = await browser.newPage();
  await page.goto('http://localhost:8000/toc_phys.html', {waitUntil: 'networkidle2'});
  await page.pdf({
    displayHeaderFooter: false,
    paperWidth: 5,
    paperHeight: 9,
    path:'C:\\Users\\whip\\tdr_published_files\\toc_phys.pdf',
    margin: {
      top: '100px',
      bottom: '100px',
      right: '90px',
      left: '90px',
    },
  });

  await browser.close();
})();

