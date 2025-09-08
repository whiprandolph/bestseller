
const puppeteer = require('puppeteer');
//function sleep(time) {
//  return new Promise((resolve) => setTimeout(resolve, time));
//}
(async() => {
  const browser = await puppeteer.launch({headless:true});
  //await sleep(5000);
  const page = await browser.newPage();
  await page.goto('http://localhost:8000/book_online.html', {waitUntil: 'networkidle2'});
  await page.pdf({
    displayHeaderFooter: true,
    preferCSSPageSize: true,
    printBackground: true,
    headerTemplate: '<div id="header-template"></div>',
    footerTemplate: '<div id="footer-template" style="font-size:11px !important; color:#000000; position:absolute; left:.55in; top:8.65in;"> <span class="pageNumber"></span> </div>',
    path:'C:\\Users\\whip\\tdr_published_files\\content_online.pdf',
  });

  await browser.close();
})();

