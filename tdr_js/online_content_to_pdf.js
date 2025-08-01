
const puppeteer = require('puppeteer');

(async() => {
  const browser = await puppeteer.launch();
  const page = await browser.newPage();
  await page.goto('http://localhost:8000/book_online.html', {waitUntil: 'networkidle2'});
  await page.pdf({
    displayHeaderFooter: true,
    paperWidth: 6,
    paperHeight: 9,
    printBackground: true,
    headerTemplate: '<div id="header-template"></div>',
    footerTemplate: '<div id="footer-template" style="font-size:11px !important; color:#000000; position:absolute; left:1.2in; top:8.9in;"> <span class="pageNumber"></span> </div>',
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

