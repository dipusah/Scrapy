import scrapy
from urllib.parse import urlparse,parse_qs
from UniversityScraper.items import UniversityItem
import logging, re, traceback
import requests
from lxml import html
import math

class UlsterSpider(scrapy.Spider):
    name = 'ulster'
    #allowed_domains = ['https://www.ulster.ac.uk/']
    start_urls = ['https://www.ulster.ac.uk/courses?query=&f.Level_u|Y=Undergraduate&f.Level_u|Y=Postgraduate']


    def parse(self, response):

        #from course we see there is 762 course and in per page there are 40 page.

        course_count = response.xpath('//*[@id="course_list"]/div[1]/div/div[1]/header/h2/b/text()').get()
        per_page = 40
        total_page = math.ceil(int(course_count) / per_page)
        for i in range(0, total_page):
            if (i == 0):
                url = 'https://www.ulster.ac.uk/courses?query=Master%27s%20with%20Advanced%20Practice%20~Full-time&f.Level_u|Y=Undergraduate&f.Level_u|Y=Postgraduate'
            else:
                start_rank = per_page * i + 1
                url = 'https://www.ulster.ac.uk/courses?profile=_default-facets-facets-facets&query=&f.Level_u|Y=Undergraduate&f.Level_u|Y=Postgraduate&start_rank=' + str(start_rank)


            yield scrapy.Request(url, callback=self.parse2)


    def parse2(self, response):

        course_links=response.xpath('//*[@class="course"]/h3/a/@href').extract()
        logging.warn("SampleSpider; Scraping Started...; url= %s", response.url)
        main_course_url=[]
        for course_link in course_links:
            course_url = course_link
            parsed_url = urlparse(course_url)
            parsed_qs = parse_qs(parsed_url.query)
            url = parsed_qs['url']
            main_course_url.append(url)
        res = [''.join(ele) for ele in main_course_url]



        international_fee_url=domestic_fee_url=ielts_url=""

        fee=self._get_fee(international_fee_url)
        domestic_fee=self._get_domestic_fee(domestic_fee_url)
        ielts_da=self._get_ielts_pte_tofel(ielts_url)


        for course_url in res:
            yield scrapy.Request(course_url,callback=self.course_info,meta={'international_fee':fee,'domestic_fee':domestic_fee,'ielts_data':ielts_da})






    def course_info(self,response):
        try:
            item=UniversityItem()

            #course_name
            course_name=response.xpath("normalize-space(//*[@class='grid-container']/div/div/div/h1/text()[1])").get().translate({ord(i): None for i in '\r\n'})
            item['course_name'] = course_name

            #degree_level
            degree_level=response.xpath("normalize-space(//*[@class='grid-container']/div/div/div/h1/text()[2])").get().translate({ord(i): None for i in '\r\n'})
            item['degree_level']=degree_level

            #category
            category=response.xpath("//*[@class='grid-container']/div/div/div/div/div[2]/div[2]/p/text()").get()
            item['category'] = category

            #course_website
            course_website=response.url
            item['course_website'] = course_website

            #city
            city=response.xpath("//*[@class='grid-container']/div/div/div/div/div[4]/div[2]/p/text()").get()
            city1=response.xpath("//*[@class='grid-container']/div/div/div/div/div[3]/div[2]/p/text()").get()


            if city.isnumeric()==True:
                city=city1

            if 'This course is taught online' in city:
                city=None



            item["city"] = city

            #duration
            duration_years=response.xpath("//div[@id='modules']/div[@class='callout']/ol/li/a/text()").extract()
            duration=duration_term=''
            if len(duration_years)==1:
                duration='1'
                duration_term='Year'
            if len(duration_years) == 2:
                duration = '2'
                duration_term = 'Year'
            if len(duration_years) == 3:
                duration = '3'
                duration_term = 'Year'
            if len(duration_years) == 4:
                duration = '4'
                duration_term = 'Year'
            if len(duration_years) == 5:
                duration = '5'
                duration_term = 'Year'
            if len(duration_years) == 6:
                duration = '6'
                duration_term = 'Year'


            item['duration'] = duration
            item['duration_term'] = duration_term




            #intake_month
            t=[]
            i=''
            intake_month=response.xpath("//*[@class='grid-container']/div/div/div/div/div[5]/div[2]/p/text()").extract() #some time uasc code aayera
            next_tag=response.xpath("//*[@class='grid-container']/div/div/div/div/div[6]/div[2]/p/text()").extract()
            for i in intake_month:
                if 'The UCAS code' in i:
                    i = next_tag

                #
                #     for k in i:
                #         k.split(' ')
                #         k = ''.join([j for j in k if not j.isdigit()]).strip()
                #         i = k
                #     t.append(i)
                #
                # else:
                #     i = i
                #
                #     i = ''.join([j for j in i if not j.isdigit()]).strip()
                #     t.append(i)


            # i=''.join([j for j in i if not j.isdigit()])
            item['intake_month']=i

            #study_load
            study_l=response.xpath("normalize-space(//*[@class='grid-container']/div/div/div/p/text())").get().translate({ord(i): None for i in '\r\n'}).split(' ')
            study_load=study_l[1]
            item['study_load']=study_load



            #ielts_data
            ielts_score=response.request.meta['ielts_data']
            #item['english_test']=ielts_score
            ielts_data=ielts_score['ielts_data']


            # 22 IELTS Listening
            ielts_listening = ielts_data[-1]

            #  IELTS Speaking
            ielts_speaking = ielts_data[-1]

            #IELTS Writting
            ielts_writing = ielts_data[-1]

            # 25 IELTS Reading
            ielts_reading = ielts_data[-1]

            # 26 IELTS Overall
            ielts_overall = ielts_data[0]

            item["ielts_listening"] = ielts_listening
            item["ielts_writing"] = ielts_writing
            item["ielts_reading"] = ielts_reading
            item["ielts_speaking"] = ielts_speaking
            item["ielts_overall"] = ielts_overall

            #tofel data
            toefl_six=[]
            tofel_data_six = ielts_score['tofel_score']#extract the tofel data from dict inside dict
            item['toefl_reading']=tofel_data_six
            for i in tofel_data_six:
                tofel_data = re.findall("\d+", i)
                toefl_six.append(tofel_data)
            toefl_six = list(map(''.join, toefl_six))

            if ielts_overall=='6.0':
                toefl_overall=toefl_six[0]

            if ielts_writing=='5.5' or ielts_writing=='5.5' or ielts_reading == '5.5'or ielts_reading == '5.5':
                toefl_writing='N/A'
                toefl_reading='N/A'
                toefl_speaking='N/A'
                toefl_listening='N/A'

            item["toefl_listening"] = toefl_listening
            item["toefl_writing"] = toefl_writing
            item["toefl_reading"] = toefl_reading
            item["toefl_speaking"] = toefl_speaking
            item["toefl_overall"] = toefl_overall

            #pte data
            pte_data = ielts_score['pte_score']
            do = []
            for i in pte_data:
                pte_data = re.findall("\d+", i)
                do.append(pte_data)
            pte_data_six=do[2]
            pte_data_five_point_five=do[1]


            #for ielts 6
            if ielts_overall=='6.0':
                pte_overall=pte_data_six[0]
            if ielts_writing == '5.5':
                pte_writing=pte_data_five_point_five[1]
            if ielts_listening == '5.5':
                pte_listening=pte_data_five_point_five[1]
            if ielts_speaking == '5.5':
                pte_speaking=pte_data_five_point_five[1]
            if ielts_reading == '5.5':
                pte_reading=pte_data_five_point_five[1]

            item['pte_overall']=pte_overall
            item['pte_writing']=pte_writing
            item['pte_speaking']=pte_speaking
            item['pte_reading']=pte_reading
            item['pte_listening']=pte_listening


            #course_descreption

            course_descreption_full=response.xpath("//*[@id='overview']/p/text()").extract()

            course_descreption = course_descreption_full[1:len(course_descreption_full) - 1]
            course_descreption=' '.join([str(elem) for elem in course_descreption])#for join list of string to list

            item['course_description']=course_descreption

            # international Fee
            international_fee = response.request.meta['international_fee']

            #modified
            course_nam = international_fee[1]
            cours = course_nam[0].split('/')
            cours = [x.replace('MSc', '').strip() for x in cours]
            cours_fee = course_nam[1]
            if course_name in cours and degree_level == 'MSc':
                fee = cours_fee
            else:
                fee = international_fee[0]


            item['international_fee'] = fee

            # domestic Fee
            domestic_fee = response.request.meta['domestic_fee']
            item['domestic_fee'] = domestic_fee

            # fee year
            fee_year = '2021/22'
            item['fee_year'] = fee_year

            # fee term
            fee_term = 'year'
            item['fee_term'] = fee_term


            #course Structure
            # course_structure=response.xpath('//*[@id="modules"]').get()
            # TAG_RE = re.compile(r'<[^>]+>')
            # course_structure=TAG_RE.sub('', course_structure).translate({ord(i): None for i in '\r\n'})
            # item['course_structure']=course_structure
            #
            # #carrier
            # career=response.xpath('//*[@id="opportunities"]').get()
            # TAG_RE = re.compile(r'<[^>]+>')
            # career=TAG_RE.sub('', career).translate({ord(i): None for i in '\r\n'})
            # item['career']=career

            #currency
            currency="£"
            item['currency']=currency




            yield item

        except Exception as e:
            logging.error("SampleSpider; msg=Crawling Failed > %s;url= %s", str(e), response.url)
            logging.error("SampleSpider; msg=Crawling Failed;url= %s;Error=%s", response.url, traceback.format_exc())




    def _get_fee(self,inernational_fee_url):
        lis=[]
        page=requests.get('https://www.ulster.ac.uk/finance/student/tuition-fees-rates/tuition-fees-202122/tuition-fees-202122-international-students-year-of-admission-from-201718')
        response=html.fromstring(page.content)
        international_fee=response.xpath('//*[@id="table64009"]/tbody/tr[1]/td[2]/text()')
        #return international_fee

        #modified fee
        intternational_exceptFee_course=response.xpath('//*[@id="table64009"]/tbody/tr[11]/td/text()')
        lis.append(international_fee)
        lis.append(intternational_exceptFee_course)
        return lis



    def _get_domestic_fee(self,domestic_fee_url):
        page1=requests.get('https://www.ulster.ac.uk/finance/student/tuition-fees-rates/tuition-fees-202021/tuition-fees-202021-for-students-year-of-admission-2021')
        response=html.fromstring(page1.content)
        domestic_fee=response.xpath('//*[@id="table08898"]/tbody/tr[1]/td[2]/text()')
        return domestic_fee

    def _get_ielts_pte_tofel(self,ipt_url):
        page2=requests.get('https://www.ulster.ac.uk/global/apply/english-language-requirements')
        responce=html.fromstring(page2.content)
        ielts_score=responce.xpath('string(//*[@id="wysiwyg"]/p[3]/text())')

        ielts_data = re.findall("\d+\.\d+", ielts_score)


        #PTE data
        english_req={}
        pte_score=responce.xpath('//*[@id="table59814"]/tbody/tr/td/text()')
        tofel_score=responce.xpath('//*[@id="table09786"]/tbody/tr/td[3]/text()')
        english_req['ielts_data']=ielts_data
        english_req['pte_score']=pte_score
        english_req['tofel_score']=tofel_score

        return english_req














