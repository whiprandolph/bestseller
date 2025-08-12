
const puppeteer = require('puppeteer');

(async() => {
  const browser = await puppeteer.launch();
  const page = await browser.newPage();
  await page.goto('http://localhost:8000/book_phys.html', {waitUntil: 'networkidle2'});
  await page.pdf({
    displayHeaderFooter: true,
    preferCSSPageSize: true,
    printBackground: true,
    headerTemplate: '<div id="header-template"></div>',
    footerTemplate: '<div id="footer-template" style="font-size:11px !important; color:#000000; position:absolute; left:.55in; top:8.65in;"> <span class="pageNumber"></span> </div>',
    path:'C:\\Users\\whip\\tdr_published_files\\content_phys.pdf',
  });

  await browser.close();
})();


