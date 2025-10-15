
const puppeteer = require('puppeteer');

(async() => {
  const browser = await puppeteer.launch();
  const page = await browser.newPage();
  await page.goto('http://localhost:8000/book_phys.html', {waitUntil: 'networkidle2'});
  await page.pdf({
    displayHeaderFooter: true,
    width: '6in',
    height: '9in',
    preferCSSPageSize: true,
    printBackground: true,
    headerTemplate: '<div id="header-template"></div>',
    footerTemplate: '<div id="footer-template" style="font-size:11px !important; color:#000000; position:absolute; left:.55in; top:8.65in;"> <span class="pageNumber"></span> </div>',
    path:'/Users/hickory/Books/tdr/pub/content_phys.pdf',
    margin: {
      top: '0px',
      bottom: '0px',
      right: '0px',
      left: '0px',
    },
  });

  await browser.close();
})();


