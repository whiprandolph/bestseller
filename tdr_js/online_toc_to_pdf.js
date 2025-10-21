
const puppeteer = require('puppeteer');

(async() => {
  const browser = await puppeteer.launch();
  const page = await browser.newPage();
  await page.goto('http://localhost:2000/toc_online.html', {waitUntil: 'networkidle2'});
  await page.pdf({
    displayHeaderFooter: false,
    preferCSSPageSize: true,
    path:'/Users/hickory/Books/tdr/pub/toc_online.pdf',
    margin: {
      top: '0px',
      bottom: '0px',
      right: '0px',
      left: '0px',
    },
  });

  await browser.close();
})();

