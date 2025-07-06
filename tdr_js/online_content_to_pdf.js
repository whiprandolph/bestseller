
const puppeteer = require('puppeteer');

(async() => {
  const browser = await puppeteer.launch();
  const page = await browser.newPage();
  await page.goto('http://localhost:8000/book_online.html', {waitUntil: 'networkidle2'});
  await page.pdf({
    displayHeaderFooter: true,
    paperWidth: 8.5,
    paperHeight: 11,
    headerTemplate: '<div id="header-template"></div>',
    footerTemplate: '<div id="footer-template" style="font-size:11px !important; color:#000000; padding-left:20px"> <span class="pageNumber"></span> </div>',
    path:'C:\\Users\\whip\\tdr_published_files\\content_online.pdf',
    margin: {
      top: '100px',
      bottom: '100px',
      right: '26px',
      left: '26px',
    },
  });

  await browser.close();
})();

