
const puppeteer = require('puppeteer');

(async() => {
  const browser = await puppeteer.launch({headless:true});
  const page = await browser.newPage();
  await page.goto('http://localhost:2000/book_online.html', {waitUntil: 'networkidle2'});
  await page.pdf({
    displayHeaderFooter: true,
    preferCSSPageSize: true,
    printBackground: true,
    headerTemplate: '<div id="header-template"></div>',
    footerTemplate: '<div id="footer-template" style="font-size:11px !important; color:#000000; position:absolute; left:.55in; top:8.65in;"> <span class="pageNumber"></span> </div>',
    path:'/Users/hickory/Books/tdr/pub/content_online.pdf',
  });

  await browser.close();
})();

