import scrapy
from UniversityScraper.items import UniversityItem
import logging, re, traceback
import requests
from lxml import html
import tabula


class MoreheadsuSpider(scrapy.Spider):
    name = 'moreheadsu'
    allowed_domains = ['www.moreheadstate.edu']
    start_urls = ['https://www.moreheadstate.edu/Academics/Find-A-Major']

    def parse(self, response):
        course_links=response.xpath('//*[@id="column-article"]/section[2]/figure/div/figcaption/a/@href').extract()
        logging.warn("moreheadsu; Scraping Started...; url= %s", response.url)
        print(len(course_links))
        fee_url=ipt_url=''
        fee = self._get_fee(fee_url)
        eng_req=self._get_ielts_tofel(ipt_url)
        for course_url in course_links:
            course_url='https://www.moreheadstate.edu'+ course_url

            yield scrapy.Request(course_url,callback=self.course_info,meta={'fee':fee,'eng_req':eng_req})


    def course_info(self,response):
        try:
            item=UniversityItem()

            #course_name
            course_name=response.xpath('//*[@id="banner-content"]/h1/text()').get()
            item['course_name']=course_name

            #course_website
            course_website=response.url
            item['course_website']=course_website

            # fee data
            fee = response.request.meta['fee']

            #domestic_fee
            domestic_fee=fee[0]
            domestic_fee=domestic_fee.replace('$','')
            item['domestic_fee']=domestic_fee

            #international fee
            international_fee=fee[1]
            international_fee=international_fee.replace('$','')
            item['international_fee'] =international_fee

            # domestic_only
            if international_fee:
                domestic_only = False

            item['domestic_only'] = domestic_only

            #fee_year
            fee_year=fee[2]
            fee_year=re.findall("\d+",fee_year)
            fee_year=fee_year[-1]

            item['fee_year']=fee_year

            #fee_term
            fee_term=fee[-1]
            fee_term=fee_term.split(' ')
            fee_term=fee_term[-1]
            item['fee_term']=fee_term

            #currency
            currency='$'
            item['currency']=currency

            #ielts_overall
            english=response.request.meta['eng_req']
            ielts_overall=english[0]
            item['ielts_overall']=ielts_overall

            #tofel_overall
            toefl_overall=english[1]
            item['toefl_overall']=toefl_overall

            #course_descreption
            course_descreption=response.xpath('normalize-space(//*[@id="main-content"]/div/text()[1])').get().translate({ord(i): None for i in '\r\n'})
            if course_descreption=='':
                # course_descreption=None
                # if course_descreption is not None:
                #     course_descreption=course_descreption
                course_descreption=response.xpath('normalize-space(//*[@id="main-content"]/div/p[1]/text())').get().translate({ord(i): None for i in '\r\n'})
            else:
                course_descreption=course_descreption

            item['course_description']=course_descreption


            #carrier
            len_p=len(response.xpath('//*[@id="main-content"]/div/p'))
            len_p=len_p-1
            i=str(len_p)

            career=response.xpath('normalize-space(//*[@id="main-content"]/div/p['+i+']/text())').get().translate({ord(i): None for i in '\r\n\xa0'})

            item['career']=career

            #course_structure
            #course_structure_pdf_link=''
            course_structure=response.xpath('//a[text()="course lists"]/@href').get()
            course_structure_1=response.xpath('//a[text()="Course List"]/@href').get()
            course_structure_2=response.xpath('//a[text()="Curriculum Map"]/@href').get()
            course_structure_3=response.xpath('//a[text()="Bachelor of Fine Arts (BFA) in Creative Writing"]/@href').get()
            course_structure_4=response.xpath('//a[text()="View courses and curriculum for this program"]/@href').get()


            if not course_structure:
                course_structure=course_structure
                if not course_structure:
                    course_structure=course_structure_1
                    if not course_structure:
                        course_structure=course_structure_2
                        if not course_structure:
                            course_structure=course_structure_3
                            if not course_structure:
                                course_structure=course_structure_4
            else:
                course_structure=course_structure





            if course_structure:
                course_structure='https://www.moreheadstate.edu'+course_structure

            #work in extraction of tabular data from pdf
            dfs=''
            try:
                dfs = tabula.read_pdf(course_structure, pages="all", stream=True)

            except Exception as e:
                print('Error {}'.format(e))

            item['course_structure']=dfs



            yield item

        except Exception as e:
            logging.error("moreheadsu; msg=Crawling Failed > %s;url= %s", str(e), response.url)
            logging.error("moreheadsu; msg=Crawling Failed;url= %s;Error=%s", response.url, traceback.format_exc())

    def _get_fee(self, fee_url):
        page2 = requests.get('https://www.moreheadstate.edu/tuition')
        response = html.fromstring(page2.content)
        fee = []
        domestic_fee = response.xpath('//*[@id="main-content"]/div/table[1]/tbody/tr[1]/td[2]/text()')
        international_fee = response.xpath('//*[@id="main-content"]/div/table[1]/tbody/tr[2]/td[2]/text()')
        fee_year=response.xpath('//*[@id="main-content"]/div/h3[1]/text()')
        fee_term=response.xpath('//*[@id="main-content"]/div/table[1]/thead/tr/th[2]/strong/text()')
        fee.append(domestic_fee)
        fee.append(international_fee)
        fee.append(fee_year)
        fee.append(fee_term)

        fee = list(map(''.join, fee))
        return fee

    def _get_ielts_tofel(self, ipt_url):
        page1 = requests.get('https://www.moreheadstate.edu/Admissions/International/English-Proficiency#:~:text=This%20can%20be%20done%20by,undergraduates%20on%20the%20IELTS%20test.')
        response = html.fromstring(page1.content)
        ielts_tofel = response.xpath('//*[@id="main-content"]/div/text()[1]')
        english_req=[]
        ielts_tofel=ielts_tofel[0]#list to string
        ielts=re.findall("\d+\.+\d",ielts_tofel)
        ielts=ielts[0]#list to string data
        tofel=re.findall('\d+',ielts_tofel)
        tofel=tofel[2]
        english_req.append(ielts)
        english_req.append(tofel)

        return english_req


