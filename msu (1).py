import scrapy
from UniversityScraper.items import UniversityItem
import logging, re, traceback
import requests
from lxml import html



class MsuSpider(scrapy.Spider):
    name = 'msu'
    #allowed_domains = ['www.reg.msu.edu']
    start_urls = ['https://reg.msu.edu/AcademicPrograms/Programs.aspx?PType=UN']

    def parse(self, response):
        Acadmic_programs_urls=response.xpath('//*[@id="divAPMenu"]/div/a/@href').extract()

        logging.warn("msu; Scraping Started...; url= %s", response.url)
        Acadmic_programs_urls=Acadmic_programs_urls[1:9]
        print(len(Acadmic_programs_urls))
        for Acadmic_programs_url in Acadmic_programs_urls:
            Acadmic_programs_url='https://reg.msu.edu/AcademicPrograms/'+Acadmic_programs_url
            yield scrapy.Request(Acadmic_programs_url,callback=self.course_link)


    def course_link(self,response):
        course_links=response.xpath('//*[@id="MainContent_divData"]/div/a/@href').extract()
        logging.warn("msu; Scraping Courses Started....; url= %s", response.url)
        ielts_url=fee_url=''
        ielts_da = self._get_ielts_pte_tofel(ielts_url)
        fee=self._get_fee(fee_url)
        for course_url in course_links:
            course_url='https://reg.msu.edu/AcademicPrograms/'+course_url
            yield scrapy.Request(course_url,callback=self.course_info,meta={'eng_data':ielts_da,'fee':fee})

    def course_info(self,response):
        try:
            item = UniversityItem()

            # 1 CourseName
            program=response.xpath('//*[@id="MainContent_tdProgram"]/text()').get()
            award=response.xpath('//*[@id="MainContent_tdAward"]/text()').get()
            comma=','
            course_name = award+comma+program
            item['course_name'] = course_name

            #degree_level
            degree_level=response.xpath('//*[@id="MainContent_tdLevel"]/text()').get()
            item['degree_level']=degree_level

            #course_website
            course_website=response.url
            item['course_website']=course_website

            #fee data
            fee=response.request.meta['fee']

            #domestic_fee
            domestic_fee=fee[0]
            domestic_fee=re.findall("\d+", domestic_fee)
            item['domestic_fee']=domestic_fee

            #international fee
            international_fee=fee[1]
            international_fee=re.findall("\d+\,+\d+\d+\d", international_fee)
            item['international_fee'] =international_fee

            #fee term
            fee_term='year'
            item['fee_term']=fee_term

            #Domestic only
            if domestic_fee:
                domestic_only=True
            item['domestic_only']=domestic_only

            #fee_year
            fee_year='2021'
            item['fee_year']=fee_year


            #eng_data
            eng_req_score = response.request.meta['eng_data']


           # item['ielts_reading']=eng_req_score
            ielts_overall=eng_req_score[0]
            ielts_overall=re.findall("\d+\.+\d", ielts_overall)
            ielts_overall=' '.join(map(str, ielts_overall))
            item['ielts_overall']=ielts_overall

            #pte
            pte_data=eng_req_score[1]
            pte_data=re.findall("\d+", pte_data)
            pte_overall=pte_data[0]
            pte_reading=pte_data[1]
            pte_speaking=pte_data[1]
            pte_writing =pte_data[1]
            pte_listening=pte_data[1]

            item['pte_overall']=pte_overall
            item['pte_writing'] = pte_writing
            item['pte_speaking'] = pte_speaking
            item['pte_reading'] = pte_reading
            item['pte_listening'] = pte_listening

            #toeft
            toefl_data=eng_req_score[2]
            toefl_data=re.findall("\d+", toefl_data)
            toefl_overall=toefl_data[0]
            toefl_reading=toefl_data[1]
            toefl_writing =toefl_data[1]
            toefl_speaking =toefl_data[1]
            toefl_listening =toefl_data[1]

            item["toefl_listening"] = toefl_listening
            item["toefl_writing"] = toefl_writing
            item["toefl_reading"] = toefl_reading
            item["toefl_speaking"] = toefl_speaking
            item["toefl_overall"] = toefl_overall

            #course_description
            course_description=response.xpath('//*[@id="MainContent_divDesc"]/div/div[2]/p/text()').extract()
            item['course_description']=course_description

            #course structure
            course_structure=response.xpath('//*[@id="MainContent_divDesc"]/div/div[2]/ol')

            if course_structure==None:
                course_structure=response.xpath('//*[@id="MainContent_divDesc"]/div/div[2]/table')


            item['course_structure']=course_structure






            yield item





        except Exception as e:
            logging.error("msu; msg=Crawling Failed > %s;url= %s", str(e), response.url)
            logging.error("msu; msg=Crawling Failed;url= %s;Error=%s", response.url, traceback.format_exc())


    def _get_ielts_pte_tofel(self,ipt_url):
        page1 = requests.get('https://admissions.msu.edu/apply/international/before-you-apply/english-language-proficiency.aspx')
        response = html.fromstring(page1.content)
        english_req=[]
        ielts=response.xpath('//*[@id="msuDetail"]/p[5]/text()')
        pte=response.xpath('//*[@id="msuDetail"]/p[21]/text()')
        toefl=response.xpath('//*[@id="msuDetail"]/ul[3]/li/text()')
        english_req.append(ielts)
        english_req.append(pte)
        english_req.append(toefl)
        english_req = list(map(''.join, english_req))
        return english_req

    def _get_fee(self,fee_url):
        page2=requests.get('https://admissions.msu.edu/cost-aid/tuition-fees/default.aspx')
        response=html.fromstring(page2.content)
        fee=[]
        domestic_fee=response.xpath('//*[@id="msuDetail"]/p[1]/strong/text()')
        international_fee=response.xpath('//*[@id="msuDetail"]/p[4]/strong/text()')
        fee.append(domestic_fee)
        fee.append(international_fee)
        fee=list(map(''.join, fee))
        return fee

