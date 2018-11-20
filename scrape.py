'''
Reviews
|------------------------------------------------------------------------------------------------|
|  ASIN  |  date  |  author_id  |  author_name  |  rating  |  title |  description  |  verified  |


Questions
|-----------------------------------------|
|  ASIN  |  date  |  question  |  answer  |


Summary
|---------------------------------------------------------------------------------------------------------------------|
|  ASIN  |  reviews_verified  |  reviews_unverified  |  avg_review  |  avg_review_verified  |  avg_review_unverified  |

'''

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import pandas as pd
from progressbar import ProgressBar, Percentage, Bar, ETA, SimpleProgress
import os
from datetime import datetime
from time import sleep
import random

df = pd.read_excel('ASINS_to_scrape.xlsx')
df1 = []
df2 = []

chrome_options = Options()
chrome_options.add_argument('--headless')
chrome_options.add_argument('log-level=3')
driver = webdriver.Chrome('chromedriver.exe', options=chrome_options)

widgets = ['ASIN ', SimpleProgress(),'  ', Percentage(), ' ', Bar(marker='#',left='[',right=']'), ' ', ETA()]
pbar = ProgressBar(widgets=widgets, maxval=len(df)).start()

for i, asin in enumerate(df['ASIN']):
	pbar.update(i + 1)
	# Pull reviews
	reviews_link = 'https://www.amazon.com/product-reviews/' + asin + '/ref=acr_search_see_all?ie=UTF8&showViewpoints=1'
	driver.get(reviews_link)

	last_page = False
	while not last_page:
		sleep(1 + random.random())
		#sleep(random.random())
		reviews = driver.find_elements_by_xpath("//div[@id='cm_cr-review_list']/div")
		if len(reviews) <= 10:
			last_page = True
		for el in reviews:
			try:
				el.find_element_by_xpath('span').get_attribute('class') == 'a-declarative'
				try:
					driver.find_element_by_xpath("//li[@class='a-last']/a").click()
				except:
					last_page = True

				break

			except:

				review_id = el.get_attribute('id')
				temp = el.find_elements_by_xpath('div/div')
				rating = temp[1]
				rating = rating.find_element_by_xpath('a[1]').get_attribute('title')
				rating = float(rating[:rating.find(' ')])
				author_id = temp[0]
				author_id = author_id.find_element_by_xpath('a').get_attribute('href')
				author_id = author_id[author_id.find('account.')+len('account.'):author_id.find('/ref')]


				data = el.text.split('\n')
				author_name = data[0]
				title = data[1]
				date = datetime.strptime(data[2], '%B %d, %Y')
				if data[3] == 'Verified Purchase':
					verified = 1
				else:
					verified = 0
				review = ''
				for i in range(4,len(data)):
					if data[i].find('Helpful') != -1 or data[i].find(' found this helpful') != -1:
						if data[i].find(' found this helpful') == -1:
							num_helped = 0
						else:
							if data[i].find('One person') != -1:
								num_helped = 1
							else:
								num_helped = int(data[i][:data[i].find(' ')])

						break

					review = review + '  ' + data[i]

				df1.append([asin, date, author_id, author_name, rating, title, review, verified])


	# pull questions
	questions_link = 'https://www.amazon.com/ask/questions/asin/'+ asin +'/ref=ask_dp_dpmw_ql_hza?isAnswered=true'
	driver.get(questions_link)

	while True:
		sleep(1 + random.random())
		questions = driver.find_elements_by_xpath("//div[@class='a-section askTeaserQuestions']/div")
		try:
			for q in questions:
				date = q.find_element_by_xpath("div/div[2]/div[2]/div/div[2]/span[2]").text[2:]
				date = datetime.strptime(date, '%B %d, %Y')
				question = q.find_element_by_xpath("div/div[2]/div/div/div[2]/a/span").text
				answer = q.find_element_by_xpath("div/div[2]/div[2]/div/div[2]/span[1]").text

				df2.append([asin, date, question, answer])

			try:
				driver.find_element_by_xpath("//li[@class='a-last']/a").click()

			except:
				break
		except:
			break


pbar.finish()
driver.close()
df1 = pd.DataFrame(df1, columns=['ASIN', 'date', 'author_id', 'author_name', 'rating', 'title', 'description', 'verified'])
df2 = pd.DataFrame(df2, columns=['ASIN', 'date', 'question', 'answer'])

avg_review = df1.groupby('ASIN')['rating'].mean().tolist()

reviews_verified = df1.loc[df1['verified'] == 1].groupby('ASIN')[['verified', 'rating']]
num_verified = reviews_verified.count()['verified'].tolist()
avg_review_verified = reviews_verified.mean()['rating'].tolist()

reviews_unverified = df1.loc[df1['verified'] == 0].groupby('ASIN')[['verified', 'rating']]
num_unverified = reviews_unverified.count()['verified'].tolist()
avg_review_unverified = reviews_unverified.mean()['rating'].tolist()

df3 = pd.DataFrame({
	'ASIN': df['ASIN'].tolist(),
	'reviews_verified': num_verified,
	'reviews_unverified': num_unverified,
	'avg_review': avg_review,
	'avg_review_verified': avg_review_verified,
	'avg_review_unverified': avg_review_unverified
})

df1.set_index('ASIN', drop=True, inplace=True)
df2.set_index('ASIN', drop=True, inplace=True)
df3.set_index('ASIN', drop=True, inplace=True)

df1.to_csv('data/reviews.csv')
df2.to_csv('data/questions.csv')
df3.to_csv('data/summary.csv')

print('Complete!')
sleep(5)
